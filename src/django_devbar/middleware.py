import re
from contextlib import ExitStack
from time import perf_counter

from django.db import connections

from . import tracker
from .conf import get_position, get_show_bar, get_show_headers

DEVBAR_HTML = (
    '<div id="django-devbar" style="position:fixed;{position};'
    "background:rgba(0,0,0,0.7);color:rgba(255,255,255,0.85);"
    "padding:4px 8px;margin:8px;"
    "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
    "font-size:10px;line-height:1.3;font-weight:500;letter-spacing:0.02em;"
    "z-index:99999;border-radius:3px;"
    'backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)">'
    '<span style="opacity:0.5">queries</span> {count}{duplicates} <span style="opacity:0.5">·</span> '
    '<span style="opacity:0.5">db</span> {duration:.0f}ms <span style="opacity:0.5">·</span> '
    '<span style="opacity:0.5">total</span> {response_time:.0f}ms</div>'
)

DUPLICATE_MARKER = (
    ' <span style="color:#f59e0b" title="Duplicate queries detected">(d)</span>'
)

BODY_CLOSE_RE = re.compile(rb"</body\s*>", re.IGNORECASE)


class DevBarMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_start = perf_counter()
        tracker.reset()

        with ExitStack() as stack:
            for alias in connections:
                stack.enter_context(
                    connections[alias].execute_wrapper(tracker.tracking_wrapper)
                )
            response = self.get_response(request)

        response_time = (perf_counter() - request_start) * 1000
        stats = tracker.get_stats()

        if get_show_headers():
            self._add_headers(response, stats, response_time)

        if get_show_bar() and self._can_inject(response):
            self._inject_devbar(response, stats, response_time)

        return response

    def _add_headers(self, response, stats, response_time):
        response["X-DevBar-Query-Count"] = str(stats["count"])
        response["X-DevBar-Query-Duration"] = f"{stats['duration']:.1f}"
        response["X-DevBar-Response-Time"] = f"{response_time:.1f}"
        if stats["has_duplicates"]:
            response["X-DevBar-Duplicates"] = "1"

    def _can_inject(self, response):
        if getattr(response, "streaming", False):
            return False
        content_type = response.get("Content-Type", "").lower()
        if "text/html" not in content_type:
            return False
        if response.get("Content-Encoding"):
            return False
        return hasattr(response, "content")

    def _inject_devbar(self, response, stats, response_time):
        content = response.content
        matches = list(BODY_CLOSE_RE.finditer(content))
        if not matches:
            return

        devbar_html = DEVBAR_HTML.format(
            position=get_position(),
            count=stats["count"],
            duplicates=DUPLICATE_MARKER if stats["has_duplicates"] else "",
            duration=stats["duration"],
            response_time=response_time,
        ).encode(response.charset or "utf-8")

        idx = matches[-1].start()
        response.content = content[:idx] + devbar_html + content[idx:]
        response["Content-Length"] = str(len(response.content))
