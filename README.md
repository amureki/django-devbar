# django-devbar

Lightweight performance devbar for Django. Shows DB query count, query duration, and response time.

![devbar example](docs/devbar-example.svg)

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

# Add X-DevBar-* response headers (default: False)
DEVBAR_SHOW_HEADERS = True
```

## Response Headers

When `DEVBAR_SHOW_HEADERS = True`, performance metrics are added as HTTP response headers. This is useful for:

- **API endpoints** where the HTML overlay can't be displayed
- **Automated testing** to assert performance thresholds (e.g., fail CI if query count exceeds a limit)
- **Monitoring tools** that can capture and aggregate header values

Headers included:

| Header | Description |
|--------|-------------|
| `X-DevBar-Query-Count` | Number of database queries executed |
| `X-DevBar-Query-Duration` | Total time spent in database queries (ms) |
| `X-DevBar-Response-Time` | Total request-response cycle time (ms) |
| `X-DevBar-Has-Duplicates` | Present (value `1`) if duplicate queries detected |
