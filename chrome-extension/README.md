# Django DevBar - Chrome Extension

A Chrome DevTools extension for viewing Django DevBar performance metrics directly in your browser's developer tools.

## Features

- **Real-time Metrics**: View DB time, app time, total time, and query count for each request
- **Similar & Duplicate Query Detection**: See similar and duplicate queries highlighted with details
- **Copy-Friendly Debugging**: Copy request query reports as SQL or Markdown for issues, PRs, and chats
- **Request History**: Track the last 50 requests in your session
- **Native DevTools UI**: Seamlessly integrated into Chrome DevTools

## Installation

1. **Install the Extension**

   **Option A - Chrome Web Store** (recommended):
   Install directly from the [Chrome Web Store](https://chromewebstore.google.com/detail/django-devbar/fehcaaopchkbknbdhjadnmehiifdmeid).

   **About Permissions**: Chrome shows a broad permissions warning during install, but this extension only runs on `localhost` and `127.0.0.1` for local Django development. It cannot access other websites.

   **Option B - Development Mode**:

   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in the top-right corner)
   - Click "Load unpacked"
   - Select the `chrome-extension` directory from this repository

1. **Use the Extension**

   - Open Chrome DevTools (F12 or right-click → Inspect)
   - Navigate to the "Django DevBar" tab
   - Visit any page running Django with DevBar middleware enabled
   - Metrics will appear automatically in the DevTools panel

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
1. Run `npm run build` to update dist/
1. Go to `chrome://extensions/`
1. Click the refresh icon on the Django DevBar extension
1. Reload DevTools
