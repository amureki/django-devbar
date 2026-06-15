# Django DevBar Browser Extension

A DevTools extension for viewing Django DevBar performance metrics directly in your browser's developer tools.

## Features

- **Real-time Metrics**: View DB time, app time, total time, and query count for each request
- **Similar & Duplicate Query Detection**: See similar and duplicate queries highlighted with details
- **Copy-Friendly Debugging**: Copy request query reports as SQL or Markdown for issues, PRs, and chats
- **Request History**: Track the last 50 requests in your session
- **Native DevTools UI**: Seamlessly integrated into browser DevTools

## Installation

1. **Install the Extension**

   **Option A - Browser stores** (recommended):

   - [Chrome Web Store](https://chromewebstore.google.com/detail/django-devbar/fehcaaopchkbknbdhjadnmehiifdmeid)
   - [Firefox Add-ons](https://addons.mozilla.org/en-US/firefox/addon/django-devbar/)

   Packaged builds and checksums are available from [GitHub Releases](https://github.com/amureki/django-devbar/releases).

   **About Permissions**: Chrome shows a broad permissions warning because the optional page toggle is available on any development host. The content script only reads the extension setting and hides/shows the `#django-devbar` element when present.

   **Option B - Development Mode**:

   - Run `npm install && npm run build:chrome`
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in the top-right corner)
   - Click "Load unpacked"
   - Select `browser-extension/dist/chrome`

   **Option C - Firefox Desktop Temporary Add-on**:

   - Run `npm install && npm run build:firefox`
   - Open Firefox Desktop and navigate to `about:debugging#/runtime/this-firefox`
   - Click "Load Temporary Add-on..."
   - Select `browser-extension/dist/firefox/manifest.json`

1. **Use the Extension**

   - Open browser DevTools (F12 or right-click → Inspect)
   - Navigate to the "Django DevBar" tab
   - Visit any page running Django with DevBar middleware enabled
   - Metrics will appear automatically in the DevTools panel

## Development

### Folder Structure

```text
src/                   # shared extension files copied into every build
manifests/common.json  # shared manifest fields
manifests/chrome.json  # Chrome-only manifest fields
manifests/firefox.json # Firefox-only manifest fields
dist/chrome/           # generated Chrome extension
dist/firefox/          # generated Firefox extension
```

Keep browser-specific differences in `manifests/` or tiny API wrappers in `src/*.js`; avoid build-time magic unless needed.

### Build Commands

```bash
npm install              # Install dependencies
npm run build           # Build Chrome and Firefox extensions
npm run build:chrome    # Build only Chrome to dist/chrome/
npm run build:firefox   # Build only Firefox to dist/firefox/
npm run zip:chrome      # Create zip for Chrome Web Store
npm run zip:firefox     # Create zip for Firefox AMO
npm run generate-icons  # Generate icon sizes from icon.svg
```

### Making Changes

1. Edit files in `src/` or `manifests/`
1. Run `npm run build` to update `dist/`
1. Chrome: go to `chrome://extensions/` and refresh the extension
1. Firefox: go to `about:debugging#/runtime/this-firefox` and reload the temporary add-on
1. Reload DevTools
