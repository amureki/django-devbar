# django-devbar

Lightweight performance devbar for Django. Shows DB query count, query duration, application time, and detects duplicate queries with visual severity indicators.

![devbar example](https://raw.githubusercontent.com/amureki/django-devbar/main/docs/devbar-example.svg)

## Installation

```bash
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

# Enable console logging for duplicate queries (default: True)
DEVBAR_ENABLE_CONSOLE = True

# Performance thresholds for warning/critical levels (defaults shown)
DEVBAR_THRESHOLDS = {
    "time_warning": 500,    # ms
    "time_critical": 1500,  # ms
    "count_warning": 20,    # queries
    "count_critical": 50,   # queries
}
```

## Response Headers

When `DEVBAR_SHOW_HEADERS = True`, performance metrics are added as HTTP response headers. This is useful for:

- **API endpoints** where the HTML overlay can't be displayed
- **Automated testing** to assert performance thresholds (e.g., fail CI if query count exceeds a limit)
- **Monitoring tools** that can capture and aggregate header values

Headers included:

| Header | Example | Description |
|--------|---------|-------------|
| `DevBar-Query-Count` | `12` | Number of database queries executed |
| `DevBar-DB-Time` | `87ms` | Total time spent in database queries |
| `DevBar-App-Time` | `41ms` | Application time (total time minus DB time) |
| `DevBar-Duplicates` | `3` | Number of duplicate queries detected (only present if duplicates found) |
