# Django DevBar - Chrome Extension

A Chrome DevTools extension for viewing Django DevBar performance metrics directly in your browser's developer tools.

## Features

- 📊 **Real-time Metrics**: View DB time, app time, total time, and query count for each request
- 🔍 **Duplicate Query Detection**: See duplicate queries highlighted with details
- 📜 **Request History**: Track the last 50 requests in your session
- 🎨 **Native DevTools UI**: Seamlessly integrated into Chrome DevTools

## Installation (Development Mode)

1. **Enable Extension Mode in Django**

   Add to your Django `settings.py`:
   ```python
   DEVBAR_EXTENSION_MODE = True
   DEVBAR_SHOW_HEADERS = True  # Required for the extension to work
   ```

2. **Load the Extension in Chrome**

   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in the top-right corner)
   - Click "Load unpacked"
   - Select the `chrome-extension` directory from this repository
   - The Django DevBar extension should now appear in your extensions list

3. **Use the Extension**

   - Open Chrome DevTools (F12 or right-click → Inspect)
   - Navigate to the "Django DevBar" tab
   - Visit any page running Django with DevBar middleware enabled
   - Metrics will appear automatically in the DevTools panel

## Configuration

The extension works alongside your existing Django DevBar setup. Make sure you have:

```python
# settings.py

MIDDLEWARE = [
    # ... other middleware
    'django_devbar.middleware.DevBarMiddleware',
]

# Enable extension mode to get detailed JSON data
DEVBAR_EXTENSION_MODE = True

# Enable headers (required for the extension)
DEVBAR_SHOW_HEADERS = True

# Optional: Keep the HTML overlay as well
DEVBAR_SHOW_BAR = True  # Default: same as DEBUG
```

## Troubleshooting

**No data appearing in the panel?**
- Ensure `DEVBAR_EXTENSION_MODE = True` and `DEVBAR_SHOW_HEADERS = True` are set
- Check that the Django DevBar middleware is installed and enabled
- Verify the request returns HTML or includes DevBar headers (check Network tab)
- Make sure you're viewing a Django page with DevBar enabled

**Extension not showing in DevTools?**
- Refresh the extensions page (`chrome://extensions/`)
- Reload the extension
- Close and reopen DevTools
- Check the Chrome console for any extension errors

## Development

The extension consists of:
- `manifest.json` - Extension configuration
- `devtools.html/js` - DevTools entry point
- `panel.html/js` - Main panel UI and logic
- `icons/` - Extension icons

To make changes:
1. Edit the files
2. Go to `chrome://extensions/`
3. Click the refresh icon on the Django DevBar extension
4. Reload DevTools

## Publishing (Future)

Once stable, this extension will be published to the Chrome Web Store for easy installation.
