import json
import re
from contextlib import ExitStack
from pathlib import Path
from time import perf_counter

from django.db import connections
from django.template import Context, Engine

from . import tracker
from .conf import (
    get_devtools_header_max_bytes,
    get_devtools_max_queries,
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
        max_bytes = get_devtools_header_max_bytes()
        if max_bytes <= 0:
            return

        summary_data = {
            "c": stats["count"],
            "db": round(stats["duration"], 2),
            "app": stats["python_time"],
            "full": stats["total_time"],
        }
        if self._json_size(summary_data) > max_bytes:
            return

        raw_queries = stats.get("queries", [])
        total_query_count = len(raw_queries)
        max_queries = get_devtools_max_queries()
        all_queries = (
            raw_queries[:max_queries] if max_queries is not None else raw_queries
        )
        processed_queries = [
            {
                "s": truncate_sql(q["sql"]),
                "dur": q["duration"],
                "dup": 1 if q["is_duplicate"] else 0,
                "sim": 1 if q.get("is_similar") else 0,
            }
            for q in all_queries
        ]
        is_truncated = len(processed_queries) < total_query_count

        full_payload = summary_data.copy()
        if processed_queries:
            full_payload["q"] = processed_queries
        if self._json_size(full_payload) <= max_bytes and not is_truncated:
            response["DevBar-Data"] = self._serialize_payload(full_payload)
            return

        best_count = self._max_queries_that_fit(
            summary_data,
            processed_queries,
            max_bytes,
            total_query_count,
        )
        payload = self._build_truncated_payload(
            summary_data,
            processed_queries,
            best_count,
            total_query_count,
        )

        if self._json_size(payload) <= max_bytes:
            response["DevBar-Data"] = self._serialize_payload(payload)
        else:
            response["DevBar-Data"] = self._serialize_payload(summary_data)

    def _json_size(self, data):
        return len(self._serialize_payload(data).encode("utf-8"))

    def _serialize_payload(self, payload):
        return json.dumps(payload, separators=(",", ":"))

    def _build_truncated_payload(
        self,
        summary_data,
        processed_queries,
        query_count,
        queries_total,
    ):
        payload = summary_data.copy()
        if query_count:
            payload["q"] = processed_queries[:query_count]
        payload["tr"] = 1
        payload["q_total"] = queries_total
        payload["q_sent"] = query_count
        return payload

    def _max_queries_that_fit(
        self,
        summary_data,
        processed_queries,
        max_bytes,
        queries_total,
    ):
        low = 0
        high = len(processed_queries)
        while low < high:
            mid = (low + high + 1) // 2
            payload = self._build_truncated_payload(
                summary_data,
                processed_queries,
                mid,
                queries_total,
            )
            if self._json_size(payload) <= max_bytes:
                low = mid
            else:
                high = mid - 1
        return low

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
        similar_html = self._build_similar_html(stats.get("similar_queries", []))

        template = _template_engine.get_template("django_devbar/devbar.html")
        html = template.render(
            Context(
                {
                    "position": get_position(),
                    "db_time": stats["duration"],
                    "app_time": stats["python_time"],
                    "query_count": stats["count"],
                    "duplicates_html": duplicates_html,
                    "similar_html": similar_html,
                }
            )
        )

        payload = html.encode(response.charset or "utf-8")

        idx = matches[-1].start()
        response.content = content[:idx] + payload + content[idx:]
        response["Content-Length"] = str(len(response.content))

    def _deduplicate_queries(self, queries):
        seen_sqls = set()
        unique = []
        for q in queries:
            if q["sql"] not in seen_sqls:
                seen_sqls.add(q["sql"])
                unique.append({**q, "sql": format_sql(q["sql"])})
        return unique

    def _build_duplicates_html(self, duplicates):
        if not duplicates:
            return ""
        unique = self._deduplicate_queries(duplicates)
        template = _template_engine.get_template("django_devbar/duplicates.html")
        return template.render(
            Context({"duplicates": unique, "total_count": len(duplicates)})
        )

    def _build_similar_html(self, similar):
        if not similar:
            return ""
        unique = self._deduplicate_queries(similar)
        template = _template_engine.get_template("django_devbar/similar.html")
        return template.render(
            Context({"similar": unique, "total_count": len(similar)})
        )
