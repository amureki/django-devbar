# django-devbar

Lightweight performance devbar for Django. Shows DB query count, query duration, application time, and detects duplicate queries with visual severity indicators.

![devbar example](https://github.com/amureki/django-devbar/raw/3c6118d4283c211a5d84510de52e1d5c3e5e46e4/docs/devbar-example.svg)

![devbar warning example](https://github.com/amureki/django-devbar/raw/3c6118d4283c211a5d84510de52e1d5c3e5e46e4/docs/devbar-example-warning.svg)

> **Note:** This package is experimental and may introduce breaking changes in minor versions.

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
    'POSITION': 'bottom-right',  # bottom-right, bottom-left, top-right, top-left
    'SHOW_BAR': None,            # None (default) = follows DEBUG, or True/False to override
    'SHOW_HEADERS': False,       # Add DevBar-* headers to responses
}
```

## Response Headers

Django DevBar adds HTTP response headers with performance metrics:

- **Server-Timing** (always present) - Standard HTTP header with database, application, and total time metrics. Visible in Chrome DevTools Network tab under Timing.

When `DEVBAR = {'SHOW_HEADERS': True}`, additional headers are included:

- **DevBar-Data** - JSON header with comprehensive metrics including duplicate query details

This is useful for:

- **API endpoints** where the HTML overlay can't be displayed
- **Automated testing** to assert performance metrics (e.g., fail CI if query count exceeds a limit)
- **Browser extensions** that need detailed duplicate query information

### Server-Timing format

```
Server-Timing: db;dur=87.50;desc="DB (12 queries)", app;dur=41.30, total;dur=128.80
```

## Chrome Extension

![Chrome DevTools extension](https://github.com/user-attachments/assets/4288f507-0bd5-4b8c-a3dc-0c4d5b93305f)

View Django DevBar metrics directly in Chrome DevTools with the [official extension](https://chromewebstore.google.com/detail/django-devbar/fehcaaopchkbknbdhjadnmehiifdmeid).
Requires `DEVBAR = {'SHOW_HEADERS': True}`.

See [chrome-extension/README.md](chrome-extension/README.md) for more details.
