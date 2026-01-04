# Chrome Web Store Listing

## Detailed Description

Django DevBar Chrome Extension brings Django performance metrics directly into Chrome DevTools. 
This extension is a companion tool for Django DevBar, a lightweight Django middleware that tracks database queries and response times.

**REQUIREMENTS**

This extension requires Django DevBar middleware installed in your Django application:
https://github.com/amureki/django-devbar

Django DevBar is a minimal performance monitoring tool for Django that displays query counts, query duration, and response times. This Chrome extension enhances that experience by bringing those metrics into your browser's DevTools instead of just showing them in an overlay on your page.

**WHAT IT DOES**

The extension creates a dedicated "Django DevBar" panel in Chrome DevTools that displays:
• Database query count and total execution time
• Application processing time
• Total response time
• Number of duplicate queries detected

All metrics appear automatically as you navigate your Django application during development.

**WHY USE IT**

If you're developing a Django application locally, this extension provides a native DevTools experience for monitoring performance. Instead of looking at an overlay on your page or checking response headers manually, you get a clean, persistent view of metrics right in your developer tools where you already spend your time debugging.

It's particularly useful for:
• Identifying N+1 query problems
• Spotting slow database queries during development
• Tracking duplicate queries that could be optimized
• Monitoring overall response time as you build features

**SETUP**

For setup instructions, see the README:
https://github.com/amureki/django-devbar

**PRIVACY & PERMISSIONS**

This extension only runs on localhost (127.0.0.1 and localhost) and common local development domains (.local, .test). It cannot access any other websites or your browsing data.

When you install the extension, Chrome shows a broad permissions warning, but the extension is strictly limited to local development environments. You can verify this by checking the manifest.json in the source code.

**OPEN SOURCE**

Both the middleware and this extension are open source:
https://github.com/amureki/django-devbar

Report issues, request features, or contribute on GitHub.
