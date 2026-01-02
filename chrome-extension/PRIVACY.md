# Privacy Policy for Django DevBar Extension

**Last updated:** January 2026

## Overview

Django DevBar is a developer tool Chrome extension designed to display performance metrics for Django web applications during local development. 
This privacy policy explains what data is collected and how it's used.

## Data Collection

### What We Collect

Django DevBar collects and stores the following data **locally on your device**:

1. **UI Preference** — Your checkbox preference for showing/hiding the on-page DevBar overlay

### What We Don't Collect

- No browsing history
- No personal information
- No analytics or telemetry
- No usage statistics
- No database queries or performance metrics
- No data sent to external servers

## Data Storage

All data is stored using Chrome's `chrome.storage.local` API:

- **Local storage** — Data is stored on your device only
- **No sync** — Settings do not sync across devices
- **No external servers** — We do not operate any servers that receive your data

## Data Processed (Not Stored)

The extension processes the following data in memory only:

- **HTTP Response Headers** — Reads `DevBar-Data` headers from localhost and local development domains to display performance metrics
- **Request History** — Maintains up to 50 recent requests in memory while DevTools is open; cleared when DevTools closes

This data is never stored persistently or transmitted externally.

## Permissions Explained

| Permission | Why We Need It |
|------------|----------------|
| `storage` | Store your UI preference for showing/hiding the on-page DevBar |
| Content scripts on development domains | Control DevBar visibility on localhost, 127.0.0.1, *.local, *.test domains only |

## Third-Party Services

Django DevBar does not use any third-party services, analytics, or tracking.

## Data Deletion

To delete all Django DevBar data:

1. Open Chrome extension settings (`chrome://extensions/`)
2. Find Django DevBar → Click "Remove"
3. All locally stored data will be deleted

Alternatively, you can clear the extension's storage:
- Open DevTools on any page
- Go to Application → Storage → Extension Storage → Django DevBar
- Clear the stored preferences

## Data Security

Since the extension only works with local development environments and stores minimal data (a single UI preference), security risks are minimal. We follow Chrome extension best practices:

- Manifest V3 compliance for enhanced security
- Minimal permission requests
- No remote code execution
- HTML escaping to prevent XSS attacks
- Content Security Policy enforcement

## Children's Privacy

Django DevBar is a developer tool not directed at children under 13 and does not knowingly collect data from children.

## Changes to This Policy

We may update this privacy policy from time to time. Changes will be posted to this page with an updated revision date.

## Contact

For questions about this privacy policy, please open an issue at:
https://github.com/amureki/django-devbar/issues

## Open Source

Django DevBar is open-source software. You can review the complete source code at:
https://github.com/amureki/django-devbar
