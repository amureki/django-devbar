# Django DevBar - Chrome Extension

A Chrome DevTools extension for viewing Django DevBar performance metrics directly in your browser's developer tools.

## Features

- **Real-time Metrics**: View DB time, app time, total time, and query count for each request
- **Duplicate Query Detection**: See duplicate queries highlighted with details
- **Request History**: Track the last 50 requests in your session
- **Native DevTools UI**: Seamlessly integrated into Chrome DevTools

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

Requires `DEVBAR = {'SHOW_HEADERS': True}` in Django settings. 
See the [main README](../README.md) for Django DevBar installation and configuration.

## Development

### Build Commands

```bash
npm install              # Install dependencies
npm run build           # Build extension to dist/
npm run zip             # Create zip for Chrome Web Store
npm run generate-icons  # Generate icon sizes from icon.svg
```

### Making Changes

1. Edit the source files
2. Run `npm run build` to update dist/
3. Go to `chrome://extensions/`
4. Click the refresh icon on the Django DevBar extension
5. Reload DevTools
