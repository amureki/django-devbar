import json

from django.http import HttpResponse, StreamingHttpResponse

from django_devbar.middleware import DevBarMiddleware
from django_devbar import tracker


class TestMiddleware:
    def test_devbar_injected_in_html(self, rf):
        def get_response(request):
            return HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        assert b"django-devbar" in response.content
        assert b"</body>" in response.content

    def test_json_response_no_injection(self, rf):
        def get_response(request):
            return HttpResponse('{"ok": true}', content_type="application/json")

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        assert b"django-devbar" not in response.content

    def test_streaming_response_no_injection(self, rf):
        def get_response(request):
            return StreamingHttpResponse(iter(["chunk"]), content_type="text/html")

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        assert (
            not hasattr(response, "content") or b"django-devbar" not in response.content
        )

    def test_gzip_response_no_injection(self, rf):
        def get_response(request):
            response = HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )
            response["Content-Encoding"] = "gzip"
            return response

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        assert b"django-devbar" not in response.content

    def test_position_setting(self, rf, settings):
        settings.DEVBAR = {"POSITION": "top-left", "SHOW_BAR": True}

        def get_response(request):
            return HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        assert b"top:0;left:0" in response.content

    def test_body_tag_case_insensitive(self, rf):
        def get_response(request):
            return HttpResponse(
                "<html><BODY>Test</BODY></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        assert b"django-devbar" in response.content

    def test_multiple_body_tags_uses_last(self, rf):
        def get_response(request):
            return HttpResponse(
                "<html><body>First</body><body>Second</body></html>",
                content_type="text/html",
            )

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        content = response.content.decode()
        first_body_idx = content.find("First</body>")
        devbar_idx = content.find("django-devbar")

        assert devbar_idx > first_body_idx

    def test_devbar_hidden_when_disabled(self, rf, settings):
        settings.DEVBAR = {"SHOW_BAR": False}

        def get_response(request):
            return HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        assert b"django-devbar" not in response.content

    def test_devtools_data_header_added(self, rf, settings):
        settings.DEVBAR = {"ENABLE_DEVTOOLS_DATA": True}

        def get_response(request):
            return HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        assert "DevBar-Data" in response
        data = json.loads(response["DevBar-Data"])
        assert "c" in data
        assert data["c"] >= 0
        assert "db" in data
        assert data["db"] >= 0
        assert "app" in data
        assert data["app"] >= 0
        assert "full" in data
        assert data["full"] >= 0

    def test_devtools_data_header_hidden_when_disabled(self, rf, settings):
        settings.DEVBAR = {"ENABLE_DEVTOOLS_DATA": False}

        def get_response(request):
            return HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        assert "DevBar-Data" not in response

    def test_duplicate_flags_in_query_data(self, rf, monkeypatch, settings):
        settings.DEVBAR = {"ENABLE_DEVTOOLS_DATA": True}

        monkeypatch.setattr(
            tracker,
            "get_stats",
            lambda: {
                "count": 3,
                "duration": 10.0,
                "duplicate_queries": [
                    {"sql": "SELECT * FROM foo", "duration": 5.0},
                    {"sql": "SELECT * FROM bar", "duration": 3.0},
                ],
                "queries": [
                    {
                        "sql": "SELECT * FROM foo",
                        "duration": 5.0,
                        "is_duplicate": 1,
                        "is_similar": 1,
                    },
                    {
                        "sql": "SELECT * FROM bar",
                        "duration": 3.0,
                        "is_duplicate": 1,
                        "is_similar": 1,
                    },
                    {
                        "sql": "SELECT * FROM baz",
                        "duration": 2.0,
                        "is_duplicate": 0,
                        "is_similar": 0,
                    },
                ],
            },
        )

        def get_response(request):
            return HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        data = json.loads(response["DevBar-Data"])
        assert "dup" not in data
        assert len(data["q"]) == 3
        assert sum(q["dup"] for q in data["q"]) == 2

    def test_server_timing_header_always_present(self, rf, monkeypatch):
        monkeypatch.setattr(
            tracker,
            "get_stats",
            lambda: {
                "count": 3,
                "duration": 12.5,
                "duplicate_queries": [],
            },
        )

        def get_response(request):
            return HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        assert "Server-Timing" in response
        header = response["Server-Timing"]
        assert "db;dur=12.50" in header
        assert "app;dur=" in header
        assert "total;dur=" in header

    def test_server_timing_header_preserves_existing_metrics(self, rf, monkeypatch):
        monkeypatch.setattr(
            tracker,
            "get_stats",
            lambda: {
                "count": 3,
                "duration": 12.5,
                "duplicate_queries": [],
            },
        )

        def get_response(request):
            response = HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )
            response["Server-Timing"] = "cache;desc=hit;dur=1.23"
            return response

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        header = response["Server-Timing"]
        assert header.startswith("cache;desc=hit;dur=1.23, ")
        assert "db;dur=12.50" in header
        assert "app;dur=" in header
        assert "total;dur=" in header

    def test_devtools_data_header_truncated_by_max_bytes(
        self, rf, monkeypatch, settings
    ):
        settings.DEVBAR = {
            "ENABLE_DEVTOOLS_DATA": True,
            "DEVTOOLS_HEADER_MAX_BYTES": 350,
        }

        monkeypatch.setattr(
            tracker,
            "get_stats",
            lambda: {
                "count": 20,
                "duration": 12.5,
                "queries": [
                    {
                        "sql": f"SELECT * FROM table WHERE id = {i} AND value = 'long-value-{i}'",
                        "duration": 0.5,
                        "is_duplicate": i % 2 == 0,
                        "is_similar": 1,
                    }
                    for i in range(20)
                ],
            },
        )

        def get_response(request):
            return HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        response = middleware(rf.get("/"))
        data = json.loads(response["DevBar-Data"])

        assert data["tr"] == 1
        assert data["q_sent"] < data["q_total"]
        assert len(response["DevBar-Data"].encode()) <= 350

    def test_devtools_data_header_respects_max_queries(self, rf, monkeypatch, settings):
        settings.DEVBAR = {
            "ENABLE_DEVTOOLS_DATA": True,
            "DEVTOOLS_MAX_QUERIES": 2,
        }

        monkeypatch.setattr(
            tracker,
            "get_stats",
            lambda: {
                "count": 5,
                "duration": 10.0,
                "queries": [
                    {
                        "sql": f"SELECT * FROM foo WHERE id = {i}",
                        "duration": 1.0,
                        "is_duplicate": i > 1,
                        "is_similar": 1,
                    }
                    for i in range(5)
                ],
            },
        )

        def get_response(request):
            return HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        response = middleware(rf.get("/"))
        data = json.loads(response["DevBar-Data"])

        assert data["tr"] == 1
        assert data["q_total"] == 5
        assert data["q_sent"] == 2
        assert len(data["q"]) == 2

    def test_devtools_data_header_hidden_when_budget_too_tiny(
        self, rf, monkeypatch, settings
    ):
        settings.DEVBAR = {
            "ENABLE_DEVTOOLS_DATA": True,
            "DEVTOOLS_HEADER_MAX_BYTES": 12,
        }

        monkeypatch.setattr(
            tracker,
            "get_stats",
            lambda: {
                "count": 1,
                "duration": 10.0,
                "queries": [],
            },
        )

        def get_response(request):
            return HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        response = middleware(rf.get("/"))
        assert "DevBar-Data" not in response
