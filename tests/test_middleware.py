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

    def test_headers_added(self, rf):
        def get_response(request):
            return HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        assert "DevBar-Query-Count" in response
        assert "DevBar-DB-Time" in response
        assert "DevBar-App-Time" in response
        assert "DevBar-Duplicates" not in response

    def test_headers_hidden_when_disabled(self, rf, settings):
        settings.DEVBAR = {"SHOW_HEADERS": False}

        def get_response(request):
            return HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        assert "DevBar-Query-Count" not in response
        assert "DevBar-DB-Time" not in response
        assert "DevBar-App-Time" not in response
        assert "DevBar-Duplicates" not in response

    def test_has_duplicates_header_present_when_duplicates(self, rf, monkeypatch):
        monkeypatch.setattr(
            tracker,
            "get_stats",
            lambda: {
                "count": 3,
                "duration": 10.0,
                "has_duplicates": True,
                "duplicate_queries": [
                    {"sql": "SELECT * FROM foo", "params": "(1,)", "duration": 5.0},
                    {"sql": "SELECT * FROM bar", "params": "(2,)", "duration": 3.0},
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

        assert response["DevBar-Duplicates"] == "2"

    def test_extension_mode_adds_json_header(self, rf, settings, monkeypatch):
        settings.DEVBAR_EXTENSION_MODE = True
        settings.DEVBAR_SHOW_HEADERS = True

        monkeypatch.setattr(
            tracker,
            "get_stats",
            lambda: {
                "count": 5,
                "duration": 20.5,
                "has_duplicates": True,
                "duplicate_queries": [
                    {"sql": "SELECT * FROM foo", "params": "(1,)", "duration": 5.0}
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

        assert "DevBar-Data" in response
        import json

        data = json.loads(response["DevBar-Data"])
        assert data["count"] == 5
        assert data["db_time"] == 20.5
        assert data["has_duplicates"] is True
        assert len(data["duplicates"]) == 1

    def test_extension_mode_disabled_no_json_header(self, rf, settings):
        settings.DEVBAR_EXTENSION_MODE = False
        settings.DEVBAR_SHOW_HEADERS = True

        def get_response(request):
            return HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        assert "DevBar-Data" not in response
