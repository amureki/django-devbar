# Django DevBar - Chrome Extension

A Chrome DevTools extension for viewing Django DevBar performance metrics directly in your browser's developer tools.

## Features

- 📊 **Real-time Metrics**: View DB time, app time, total time, and query count for each request
- 🔍 **Duplicate Query Detection**: See duplicate queries highlighted with details
- 📜 **Request History**: Track the last 50 requests in your session
- 🎨 **Native DevTools UI**: Seamlessly integrated into Chrome DevTools

## Installation (Development Mode)

1. **Enable Headers in Django**

   Add to your Django `settings.py`:
   ```python
   DEVBAR = {
       'SHOW_HEADERS': True,  # Required for the extension to work
   }
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

DEVBAR = {
    'SHOW_HEADERS': True,  # Required for the extension (includes DevBar-Data JSON)
    'SHOW_BAR': True,      # Optional: Keep the HTML overlay as well (default: DEBUG)
}
```

## Troubleshooting

**No data appearing in the panel?**
- Ensure `DEVBAR = {'SHOW_HEADERS': True}` is set
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

## Chrome Web Store Publishing

### Prerequisites

- [x] Privacy policy created and hosted (privacy.html via GitHub Pages)
- [x] Manifest V3 compliant
- [x] Version 1.0.0
- [ ] Screenshots captured (3-5 required)
- [ ] Promotional tile created (440x280 PNG)

### Manual Steps Required

1. **Capture Screenshots** (1280x800 or 640x400):
   - DevTools panel with metrics for a page with queries
   - Duplicate queries section expanded
   - Request history view
   - Dark mode variant (optional)

2. **Create Promotional Tile** (440x280 PNG):
   - Show extension name: "Django DevBar"
   - Include visual of DevTools panel or metrics
   - Professional, clean design

3. **Host Privacy Policy**:
   - Enable GitHub Pages for this repository
   - Set privacy policy URL in Chrome Web Store listing to: `https://[your-username].github.io/django-devbar/chrome-extension/privacy.html`

4. **Submit to Chrome Web Store**:
   - Create a [Chrome Web Store Developer account](https://chrome.google.com/webstore/devconsole) ($5 one-time fee)
   - Zip the chrome-extension folder (excluding README.md)
   - Upload to Chrome Web Store Developer Dashboard
   - Fill in listing details:
     - **Category**: Developer Tools
     - **Description**: Expanded description from manifest.json
     - **Screenshots**: Upload 3-5 screenshots
     - **Promotional Images**: Upload 440x280 tile
     - **Privacy Policy URL**: GitHub Pages URL
     - **Support URL**: https://github.com/amureki/django-devbar/issues
   - Submit for review (typically 1-3 days)

### Store Listing Text

**Short description** (132 chars max):
```
View Django DevBar metrics in Chrome DevTools: database queries, response times, and duplicate query detection.
```

**Detailed description**:
```
Django DevBar - Chrome DevTools Panel

View Django DevBar performance metrics directly in Chrome DevTools. Track database queries, response times, and duplicate query detection for your Django applications during development.

Features:
• Real-time performance metrics in DevTools panel
• Database query count and execution time tracking
• Duplicate query detection with SQL details
• Request history (up to 50 requests)
• Dark mode support
• Toggle on-page bar visibility

Works with Django DevBar middleware on localhost and local development domains.

SETUP:
1. Install Django DevBar middleware in your Django project
2. Set DEVBAR_SHOW_HEADERS = True in Django settings
3. Open Chrome DevTools and navigate to the "Django DevBar" tab
4. Visit your Django application on localhost

This extension only works with local development environments (localhost, 127.0.0.1, *.local, *.test domains) for security and privacy.

Source code: https://github.com/amureki/django-devbar
```
