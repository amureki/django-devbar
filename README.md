# django-devbar

A performance bar for Django development. Shows database query counts, query duration,
and application time. Flags similar and duplicate queries.

Settings and the response header format remain compatible within 1.x.
Breaking changes require a new major version.

[![Badge PyPI]][pypi]
[![Badge Chrome]][chrome]
[![Badge Firefox]][firefox]

## Install

| Component                  | Install from               | Notes                             |
| :------------------------- | :------------------------- | :-------------------------------- |
| Django package             | [PyPI]                     | `uv add --dev django-devbar`      |
| Chrome DevTools extension  | [Chrome Web Store][chrome] | Optional                          |
| Firefox DevTools extension | [Firefox Add-ons][firefox] | Optional                          |
| Browser extension packages | [GitHub Releases]          | Manual/dev installs and checksums |

## Screenshots

Query count, query duration, and application time:

![devbar example](https://github.com/amureki/django-devbar/raw/3c6118d4283c211a5d84510de52e1d5c3e5e46e4/docs/devbar-example.svg)

Similar and duplicate queries with details:

![devbar warning example](https://github.com/amureki/django-devbar/raw/3c6118d4283c211a5d84510de52e1d5c3e5e46e4/docs/devbar-example-warning.svg)

The optional Chrome and Firefox extension shows query details in DevTools:

[![Browser DevTools extension](https://github.com/user-attachments/assets/f53a4bb8-fba1-446c-8224-82eac47bd027)](#browser-extension)

## Motivation

django-devbar sends metrics in response headers and can display an HTML bar.
Compared with [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/):

- Setup requires one middleware entry.
- The browser extension reads metrics from any response type, including JSON.
- Django is the only dependency.
- Metrics require no extra requests to debug endpoints.
- The HTML bar is optional. You can use headers and the extension alone.

## Django setup

```bash
# Using uv
uv add --dev django-devbar

# Or using pip
pip install django-devbar
```

Place DevBar near the start of your middleware list:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # ...
]

if DEBUG:
    idx = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
    MIDDLEWARE.insert(idx + 1, "django_devbar.DevBarMiddleware")
```

The `if DEBUG` condition keeps the middleware active only in development. It also
avoids import errors when the package is not installed in production.

If the middleware remains installed, `DEBUG=False` disables the HTML bar and detailed
`DevBar-Data` header by default, but query collection and `Server-Timing` remain active.
Use the conditional setup above to disable collection in production.

## Configuration

All settings are optional. Set them in a `DEVBAR` dictionary in your Django settings:

```python
DEVBAR = {
    "POSITION": "bottom-right",  # bottom-right (default), bottom-left, top-right, top-left
    "SHOW_BAR": None,  # follows DEBUG; set True/False to override
    "ENABLE_DEVTOOLS_DATA": None,  # follows DEBUG; set True/False to override
    "DEVTOOLS_HEADER_MAX_BYTES": 6144,  # max bytes for DevBar-Data header payload
    "DEVTOOLS_MAX_QUERIES": None,  # optional cap for query entries sent to DevTools
}
```

Header limits reduce data sent to DevTools, not query collection or its memory use.

## Response headers

DevBar always adds `Server-Timing` with database, application, and total time.
You can view it in the browser's Network tab under Timing:

```
Server-Timing: db;dur=87.50, app;dur=41.30, total;dur=128.80
```

Timings and query counts exclude streaming body generation and queries executed
while a streaming response is consumed.

With `DEBUG=True`, DevBar also adds a `DevBar-Data` JSON header by default:

- The `q` entries contain query details, with `dup` and `sim` flags for duplicate and similar queries.
- The payload is truncated to fit `DEVTOOLS_HEADER_MAX_BYTES`.
- Truncated payloads include `tr`, `q_total`, and `q_sent` metadata.

Use these headers to inspect API responses, read metrics in the browser extension,
or check query counts in automated tests.

## Browser extension

Install the extension from [Chrome Web Store][chrome] or [Firefox Add-ons][firefox]
to view metrics in DevTools.

See [browser-extension/README.md](browser-extension/README.md) for more details.

[badge chrome]: https://img.shields.io/chrome-web-store/v/fehcaaopchkbknbdhjadnmehiifdmeid?label=Chrome
[badge firefox]: https://img.shields.io/amo/v/django-devbar?label=Firefox
[badge pypi]: https://img.shields.io/pypi/v/django-devbar.svg
[chrome]: https://chromewebstore.google.com/detail/django-devbar/fehcaaopchkbknbdhjadnmehiifdmeid
[firefox]: https://addons.mozilla.org/en-US/firefox/addon/django-devbar/
[github releases]: https://github.com/amureki/django-devbar/releases
[pypi]: https://pypi.org/project/django-devbar/
