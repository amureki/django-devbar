# django-devbar

> [!WARNING]
> This package is experimental and may introduce breaking changes in minor versions.

Lightweight performance devbar for Django. Shows DB query count, query duration, application time, and detects duplicate queries with visual severity indicators.

## Showcase

Normal operation – showing query count, duration, and application time:

![devbar example](https://github.com/amureki/django-devbar/raw/3c6118d4283c211a5d84510de52e1d5c3e5e46e4/docs/devbar-example.svg)

Duplicate queries detected – severity indicator and details shown:

![devbar warning example](https://github.com/amureki/django-devbar/raw/3c6118d4283c211a5d84510de52e1d5c3e5e46e4/docs/devbar-example-warning.svg)

[optional] Chrome extension - showing detailed metrics in DevTools panel:

[![Chrome DevTools extension](https://github.com/user-attachments/assets/9bbc41b7-3d93-46e7-aef4-9330a862b8f0)](#chrome-extension)

## Motivation

While [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/) is a proven tool trusted by countless projects, django-devbar explores a different approach to development debugging:

- **Minimal setup** — just add middleware, nothing else required
- **Browser DevTools integration** — Chrome extension panel works with any response type, including JSON
- **Zero extra dependencies** — only requires Django
- **Lower overhead** — no extra requests to debug endpoints
- **Non-intrusive** — HTML bar is optional; works via headers and DevTools panel alone

## Installation

```bash
# Using uv (recommended)
uv add --dev django-devbar

# Or using pip
pip install django-devbar
```

Add to your middleware as early as possible, but after any middleware that encodes the response (e.g., `GZipMiddleware`):

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django_devbar.DevBarMiddleware",
    # ...
]
```

## Configuration

All settings are optional. Configure via a `DEVBAR` dict in your Django settings:

```python
DEVBAR = {
    "POSITION": "bottom-right",  # bottom-right (default), bottom-left, top-right, top-left
    "SHOW_BAR": None,  # follows DEBUG; set True/False to override
    "ENABLE_DEVTOOLS_DATA": None,  # follows DEBUG; set True/False to override
}
```

## Response Headers

Django DevBar adds HTTP response headers with performance metrics:

- **Server-Timing** (always present) – Standard HTTP header with database, application, and total time metrics. Visible in Chrome DevTools Network tab under Timing.

An additional header is included by default in DEBUG mode:

- **DevBar-Data** - JSON header with comprehensive metrics including duplicate query details

This is useful for:

- **API endpoints** where the HTML overlay can't be displayed
- **Automated testing** to assert performance metrics (e.g., fail CI if query count exceeds a limit)
- **Browser extensions** that need detailed duplicate query information

### Server-Timing format

```
Server-Timing: db;dur=87.50, app;dur=41.30, total;dur=128.80
```

## Chrome Extension

View Django DevBar metrics directly in Chrome DevTools with the [official extension](https://chromewebstore.google.com/detail/django-devbar/fehcaaopchkbknbdhjadnmehiifdmeid).

See [chrome-extension/README.md](chrome-extension/README.md) for more details.
