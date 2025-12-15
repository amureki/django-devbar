# Testing the Django DevBar Chrome Extension MVP

This guide will help you test the Chrome DevTools extension locally.

## Prerequisites

- Chrome browser (or Chromium-based browser like Edge)
- A Django project with django-devbar installed
- The chrome-extension directory from this repository

## Step 1: Configure Django

Add the following to your Django project's `settings.py`:

```python
MIDDLEWARE = [
    # ... other middleware
    'django_devbar.middleware.DevBarMiddleware',
]

# Enable extension mode
DEVBAR_EXTENSION_MODE = True
DEVBAR_SHOW_HEADERS = True

# Optional: Keep the HTML overlay as well
DEVBAR_SHOW_BAR = True  # Shows both overlay and extension panel
```

## Step 2: Load the Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Toggle "Developer mode" ON (top-right corner)
3. Click "Load unpacked"
4. Navigate to and select the `chrome-extension` directory from this repository
5. The "Django DevBar" extension should now appear in your extensions list

## Step 3: Test the Extension

1. Start your Django development server
2. Open Chrome and navigate to any page in your Django application
3. Open Chrome DevTools (F12 or right-click → Inspect)
4. Look for the "Django DevBar" tab in the DevTools panel
5. Navigate to different pages in your Django app

## What You Should See

### In the DevTools Panel

The Django DevBar panel should display:
- **Metrics Grid**: DB Time, App Time, Total Time, Query Count
- **Duplicate Query Warning**: If duplicate queries are detected (yellow warning box)
- **Duplicate Query Details**: SQL, parameters, and duration for each duplicate
- **Request History**: Last 10 requests with summary stats

### Example Data

For a typical request, you might see:
```
DB Time: 87ms
App Time: 41ms
Total Time: 128ms
Queries: 12
```

If duplicates are detected:
```
⚠️ Duplicate queries detected (3)

Duplicate Queries:
SELECT * FROM auth_user WHERE id = %s
Params: (1,)
Duration: 5.2ms
```

## Troubleshooting

### No "Django DevBar" tab in DevTools?

1. Refresh the extensions page (`chrome://extensions/`)
2. Click the refresh icon on the Django DevBar extension
3. Close and reopen DevTools
4. Check the Chrome console (F12 → Console) for errors

### No data appearing?

1. **Check Django settings:**
   ```python
   DEVBAR_EXTENSION_MODE = True
   DEVBAR_SHOW_HEADERS = True
   ```

2. **Verify headers in Network tab:**
   - Open Chrome DevTools → Network tab
   - Navigate to a page
   - Click on the request
   - Check the Response Headers section
   - You should see `DevBar-Data`, `DevBar-Query-Count`, etc.

3. **Check the middleware:**
   - Ensure `DevBarMiddleware` is in your `MIDDLEWARE` list
   - Ensure it's placed correctly (after GZipMiddleware if you have it)

### Extension not updating?

1. Go to `chrome://extensions/`
2. Find "Django DevBar"
3. Click the refresh icon (circular arrow)
4. Close and reopen DevTools

### Still having issues?

- Check the DevTools Console for JavaScript errors
- Check your Django server logs for errors
- Verify the request is returning HTML (not JSON)
- Try with a simple Django view first

## Advanced Testing

### Test with Duplicate Queries

Create a Django view with intentional duplicates:

```python
from django.http import HttpResponse
from django.contrib.auth.models import User

def test_view(request):
    # This will trigger duplicate query detection
    user1 = User.objects.get(id=1)
    user2 = User.objects.get(id=1)  # Same query!
    user3 = User.objects.get(id=1)  # Duplicate again!

    return HttpResponse(f"<html><body>Users: {user1}, {user2}, {user3}</body></html>")
```

Visit this view and check the DevBar panel for duplicate warnings.

### Test Request History

1. Navigate to multiple pages in your Django app
2. Check the "Recent Requests" section in the DevBar panel
3. Click on different requests to view their metrics

## Next Steps

Once you've verified the extension works:

1. **Provide feedback**: What features would you like to see?
2. **Report issues**: Found a bug? Let us know!
3. **Suggest improvements**: UI enhancements, new metrics, etc.

## Known Limitations (MVP)

- Extension only works when DevTools is open
- Only shows data from requests with DevBar headers
- Request history is cleared when DevTools is closed
- No export functionality yet
- No filtering or search in history yet

These limitations will be addressed in future versions based on feedback!
