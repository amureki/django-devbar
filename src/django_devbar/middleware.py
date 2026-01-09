import json
import re
from contextlib import ExitStack
from pathlib import Path
from time import perf_counter

from django.db import connections
from django.template import Context, Engine

from . import tracker
from .conf import (
    get_enable_devtools_data,
    get_position,
    get_show_bar,
)
from .tracker import format_sql, truncate_sql

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
        python_time = round(max(0, total_time - db_time), 2)

        stats["python_time"] = python_time
        stats["total_time"] = round(total_time, 2)

        if get_enable_devtools_data():
            self._add_devtools_data_header(response, stats)

        self._add_server_timing_header(response, stats)

        if get_show_bar() and self._can_inject(response):
            self._inject_devbar(response, stats)

        return response

    def _add_devtools_data_header(self, response, stats):
        # Abbreviated keys used to minimize DevBar-Data header size
        extension_data = {
            "c": stats["count"],
            "db": round(stats["duration"], 2),
            "app": stats["python_time"],
            "full": stats["total_time"],
        }

        all_queries = stats.get("queries", [])
        duplicates = stats.get("duplicate_queries", [])

        if all_queries:
            processed_queries = [
                {
                    "s": truncate_sql(q["sql"]),
                    "dur": q["duration"],
                    "dup": 1 if q["is_duplicate"] else 0,
                }
                for q in all_queries
            ]
            extension_data["q"] = processed_queries

        if duplicates:
            marked_duplicates = [{**d, "dup": 1} for d in duplicates]
            extension_data["dup"] = marked_duplicates

        response["DevBar-Data"] = json.dumps(extension_data)

    def _add_server_timing_header(self, response, stats):
        parts = [
            f"db;dur={stats['duration']:.2f}",
            f"app;dur={stats['python_time']:.2f}",
            f"total;dur={stats['total_time']:.2f}",
        ]
        response["Server-Timing"] = ", ".join(parts)

    def _can_inject(self, response):
        if getattr(response, "streaming", False):
            return False
        content_type = response.get("Content-Type", "").lower()
        if "html" not in content_type:
            return False
        if response.get("Content-Encoding"):
            return False
        return hasattr(response, "content")

    def _inject_devbar(self, response, stats):
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
        formatted_duplicates = [
            {**dup, "sql": format_sql(dup["sql"])} for dup in duplicates
        ]
        template = _template_engine.get_template("django_devbar/duplicates.html")
        return template.render(Context({"duplicates": formatted_duplicates}))
