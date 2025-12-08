from django.http import HttpResponse, StreamingHttpResponse

from django_devbar.middleware import DevBarMiddleware


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
        settings.DEVBAR_POSITION = "top-left"

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
        settings.DEVBAR_SHOW_BAR = False

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

        assert "X-DevBar-Query-Count" in response
        assert "X-DevBar-Query-Duration" in response
        assert "X-DevBar-Response-Time" in response

    def test_headers_hidden_when_disabled(self, rf, settings):
        settings.DEVBAR_SHOW_HEADERS = False

        def get_response(request):
            return HttpResponse(
                "<html><body>Test</body></html>", content_type="text/html"
            )

        middleware = DevBarMiddleware(get_response)
        request = rf.get("/")
        response = middleware(request)

        assert "X-DevBar-Query-Count" not in response
        assert "X-DevBar-Query-Duration" not in response
        assert "X-DevBar-Response-Time" not in response
