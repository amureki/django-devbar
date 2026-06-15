# django-devbar

> [!WARNING]
> This package is experimental and may introduce breaking changes in minor versions.

Lightweight performance devbar for Django.
Shows DB query count, query duration, application time, and detects similar and duplicate queries with visual severity indicators.

[![PyPI](https://img.shields.io/pypi/v/django-devbar.svg)](https://pypi.org/project/django-devbar/)
[![Chrome Web Store](https://img.shields.io/chrome-web-store/v/fehcaaopchkbknbdhjadnmehiifdmeid?label=Chrome)](https://chromewebstore.google.com/detail/django-devbar/fehcaaopchkbknbdhjadnmehiifdmeid)
[![Firefox Add-ons](https://img.shields.io/amo/v/django-devbar?label=Firefox)](https://addons.mozilla.org/en-US/firefox/addon/django-devbar/)

## Install

| Component                  | Install from                                                                                                                                                                                           |
| :------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Django package             | [PyPI](https://pypi.org/project/django-devbar/) — `uv add --dev django-devbar`                                                                                                                         |
| Chrome DevTools extension  | <a href="https://chromewebstore.google.com/detail/django-devbar/fehcaaopchkbknbdhjadnmehiifdmeid"><img src="docs/badges/chrome-web-store.png" alt="Available in the Chrome Web Store" height="45"></a> |
| Firefox DevTools extension | <a href="https://addons.mozilla.org/en-US/firefox/addon/django-devbar/"><img src="docs/badges/firefox-addons.svg" alt="Get the add-on for Firefox" height="45"></a>                                    |

## Showcase

Normal operation – showing query count, duration, and application time:

![devbar example](https://github.com/amureki/django-devbar/raw/3c6118d4283c211a5d84510de52e1d5c3e5e46e4/docs/devbar-example.svg)

Similar and duplicate queries detected – severity indicators and details shown:

![devbar warning example](https://github.com/amureki/django-devbar/raw/3c6118d4283c211a5d84510de52e1d5c3e5e46e4/docs/devbar-example-warning.svg)

[optional] Browser extension (Chrome and Firefox) — showing detailed metrics in DevTools panel:

[![Browser DevTools extension](https://github.com/user-attachments/assets/f53a4bb8-fba1-446c-8224-82eac47bd027)](#browser-extension)

## Motivation

While [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/) is a proven tool trusted by countless projects, django-devbar explores a different approach to development debugging:

- **Minimal setup** — just add middleware, nothing else required
- **Browser DevTools integration** — extension panel works with any response type, including JSON
- **Zero extra dependencies** — only requires Django
- **Lower overhead** — no extra requests to debug endpoints
- **Non-intrusive** — HTML bar is optional; works via headers and DevTools panel alone

## Django Setup

```bash
# Using uv (recommended)
uv add --dev django-devbar

# Or using pip
pip install django-devbar
```

Add to your middleware early. For example:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # ...
]

if DEBUG:
    idx = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
    MIDDLEWARE.insert(idx + 1, "django_devbar.DevBarMiddleware")
```

This keeps the middleware active only in development and avoids import errors if the package isn't installed in production.

## Configuration

All settings are optional. Configure via a `DEVBAR` dict in your Django settings:

```python
DEVBAR = {
    "POSITION": "bottom-right",  # bottom-right (default), bottom-left, top-right, top-left
    "SHOW_BAR": None,  # follows DEBUG; set True/False to override
    "ENABLE_DEVTOOLS_DATA": None,  # follows DEBUG; set True/False to override
    "DEVTOOLS_HEADER_MAX_BYTES": 6144,  # max bytes for DevBar-Data header payload
    "DEVTOOLS_MAX_QUERIES": None,  # optional hard cap for q/dup entries sent to DevTools
}
```

## Response Headers

Django DevBar adds HTTP response headers with performance metrics:

- **Server-Timing** (always present) – Standard HTTP header with database, application, and total time metrics. Visible in browser DevTools Network tab under Timing.

An additional header is included by default in DEBUG mode:

- **DevBar-Data** - JSON header with comprehensive metrics including similar and duplicate query details
  - Query-level flags are embedded in `q` entries (`dup` and `sim`)
  - Payload is automatically truncated to fit `DEVTOOLS_HEADER_MAX_BYTES`
  - When truncated, response includes metadata keys: `tr`, `q_total`, `q_sent`

This is useful for:

- **API endpoints** where the HTML overlay can't be displayed
- **Automated testing** to assert performance metrics (e.g., fail CI if query count exceeds a limit)
- **Browser extensions** that need detailed duplicate query information

### Server-Timing format

```
Server-Timing: db;dur=87.50, app;dur=41.30, total;dur=128.80
```

## Browser Extension

View Django DevBar metrics directly in browser DevTools. Install from the Chrome Web Store or Firefox Add-ons.

See [browser-extension/README.md](browser-extension/README.md) for more details.
