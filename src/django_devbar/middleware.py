import json
import re
from contextlib import ExitStack
from time import perf_counter

from django.db import connections

from . import tracker
from .conf import (
    get_position,
    get_show_bar,
    get_show_headers,
    get_thresholds,
    get_enable_console,
)

STYLE_BLOCK = """<style>
#django-devbar {
    position: fixed; %s; z-index: 99999;
    font-family: -apple-system, system-ui, sans-serif;
    font-size: 11px; font-weight: 500;
    padding: 4px 8px; border-radius: 4px;
    backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    transition: all 0.2s ease;
    cursor: default;
    line-height: 1.3;
    background: rgba(20, 20, 20, 0.85);
    color: #e5e5e5;
}
#django-devbar.level-warn { border-left: 3px solid #f59e0b; }
#django-devbar.level-crit { border-left: 3px solid #dc2626; }
#django-devbar span { opacity: 0.7; margin-right: 2px; }
#django-devbar strong { opacity: 1; font-weight: 600; margin-right: 6px; }
</style>"""

BAR_TEMPLATE = """<div id="django-devbar" class="level-%s">
<span>db</span> <strong>%.0fms</strong>
<span>py</span> <strong>%.0fms</strong>
<span>count</span> <strong>%d</strong>%s
</div>"""

SCRIPT_TEMPLATE = """<script>
(function() {
    const stats = %s;
    if (stats.duplicates && stats.duplicates.length > 0) {
        console.groupCollapsed(`⚠️ Django DevBar: Duplicate Queries Detected (${stats.duplicates.length})`);
        console.table(stats.duplicates.map(d => ({SQL: d.sql, Parameters: d.params, Duration_ms: d.duration})));
        console.groupEnd();
    }
})();
</script>"""

BODY_CLOSE_RE = re.compile(rb"</body\s*>", re.IGNORECASE)


class DevBarMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tracker.reset()
        request_start = perf_counter()

        with ExitStack() as stack:
            for alias in connections:
                stack.enter_context(
                    connections[alias].execute_wrapper(tracker.tracking_wrapper)
                )
            response = self.get_response(request)

        total_time = (perf_counter() - request_start) * 1000
        stats = tracker.get_stats()

        db_time = stats["duration"]
        python_time = max(0, total_time - db_time)

        stats["python_time"] = python_time
        stats["total_time"] = total_time

        thresholds = get_thresholds()
        level = self._determine_level(stats, total_time, thresholds)

        if get_show_headers():
            self._add_headers(response, stats)

        if get_show_bar() and self._can_inject(response):
            self._inject_devbar(response, stats, level)

        return response

    def _determine_level(self, stats, total_time, thresholds):
        if (
            total_time > thresholds["time_critical"]
            or stats["count"] > thresholds["count_critical"]
        ):
            return "crit"
        if (
            stats["has_duplicates"]
            or total_time > thresholds["time_warning"]
            or stats["count"] > thresholds["count_warning"]
        ):
            return "warn"
        return "ok"

    def _add_headers(self, response, stats):
        response["DevBar-Query-Count"] = str(stats["count"])
        response["DevBar-DB-Time"] = f"{stats['duration']:.0f}ms"
        response["DevBar-App-Time"] = f"{stats['python_time']:.0f}ms"
        if stats["has_duplicates"]:
            response["DevBar-Duplicates"] = str(len(stats["duplicate_queries"]))

    def _can_inject(self, response):
        if getattr(response, "streaming", False):
            return False
        content_type = response.get("Content-Type", "").lower()
        if "html" not in content_type:
            return False
        if response.get("Content-Encoding"):
            return False
        return hasattr(response, "content")

    def _inject_devbar(self, response, stats, level):
        content = response.content
        matches = list(BODY_CLOSE_RE.finditer(content))
        if not matches:
            return

        dup_marker = (
            ' <strong style="color:#f59e0b">(D)</strong>'
            if stats["has_duplicates"]
            else ""
        )

        css = STYLE_BLOCK % get_position()
        html = BAR_TEMPLATE % (
            level,
            stats["duration"],
            stats["python_time"],
            stats["count"],
            dup_marker,
        )

        script = ""
        if get_enable_console() and stats.get("duplicate_queries"):
            console_data = {"duplicates": stats["duplicate_queries"]}
            script = SCRIPT_TEMPLATE % json.dumps(console_data)

        payload = (css + html + script).encode(response.charset or "utf-8")

        idx = matches[-1].start()
        response.content = content[:idx] + payload + content[idx:]
        response["Content-Length"] = str(len(response.content))
