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

```python
# Position: bottom-right, bottom-left, top-right, top-left (default: bottom-right)
DEVBAR_POSITION = "top-left"

# Show HTML overlay (default: DEBUG)
DEVBAR_SHOW_BAR = True

# Add DevBar-* response headers (default: False)
DEVBAR_SHOW_HEADERS = True
```

## Response Headers

When `DEVBAR_SHOW_HEADERS = True`, performance metrics are added as HTTP response headers. This is useful for:

- **API endpoints** where the HTML overlay can't be displayed
- **Automated testing** to assert performance metrics (e.g., fail CI if query count exceeds a limit)
- **Monitoring tools** that can capture and aggregate header values

Headers included:

| Header | Example | Description |
|--------|---------|-------------|
| `DevBar-Query-Count` | `12` | Number of database queries executed |
| `DevBar-DB-Time` | `87ms` | Total time spent in database queries |
| `DevBar-App-Time` | `41ms` | Application time (total time minus DB time) |
| `DevBar-Duplicates` | `3` | Number of duplicate queries detected (only present if duplicates found) |
