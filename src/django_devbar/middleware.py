import re
from contextlib import ExitStack
from pathlib import Path
from time import perf_counter

from django.db import connections
from django.template import Context, Engine

from . import tracker
from .conf import (
    get_position,
    get_show_bar,
    get_show_headers,
)

BODY_CLOSE_RE = re.compile(rb"</body\s*>", re.IGNORECASE)

_template_engine = Engine(
    dirs=[Path(__file__).parent / "templates"],
    autoescape=True,
)


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

        level = "warn" if stats["has_duplicates"] else "ok"

        if get_show_headers():
            self._add_headers(response, stats)

        if get_show_bar() and self._can_inject(response):
            self._inject_devbar(response, stats, level)

        return response

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

        duplicates_html = self._build_duplicates_html(
            stats.get("duplicate_queries", [])
        )

        template = _template_engine.get_template("django_devbar/devbar.html")
        html = template.render(
            Context(
                {
                    "position": get_position(),
                    "level": level,
                    "db_time": stats["duration"],
                    "app_time": stats["python_time"],
                    "query_count": stats["count"],
                    "duplicates_html": duplicates_html,
                }
            )
        )

        payload = html.encode(response.charset or "utf-8")

        idx = matches[-1].start()
        response.content = content[:idx] + payload + content[idx:]
        response["Content-Length"] = str(len(response.content))

    def _build_duplicates_html(self, duplicates):
        if not duplicates:
            return ""
        template = _template_engine.get_template("django_devbar/duplicates.html")
        return template.render(Context({"duplicates": duplicates}))
