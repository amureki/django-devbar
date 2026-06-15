export function isSameNavigationUrl(previousUrl, nextUrl) {
  if (!previousUrl || !nextUrl) return false;

  try {
    const previous = new URL(previousUrl);
    const next = new URL(nextUrl, previous);
    previous.hash = '';
    next.hash = '';
    return previous.href === next.href;
  } catch (e) {
    return previousUrl.split('#')[0] === nextUrl.split('#')[0];
  }
}

export function getRequestHeader(request, name) {
  return request.request.headers
    ?.find(h => h.name.toLowerCase() === name)
    ?.value.toLowerCase();
}

export function isNavigationDocumentRequest(request) {
  return request._resourceType === 'document'
    || getRequestHeader(request, 'sec-fetch-dest') === 'document';
}

export function shouldResetForMainDocumentRequest({
  request,
  pageUrl,
  pendingNavigationUrl,
  hasCapturedRequests,
  skipRender = false,
}) {
  if (skipRender || !hasCapturedRequests) return false;
  if (!pageUrl || !request?.request?.url) return false;
  if (!isSameNavigationUrl(request.request.url, pageUrl)) return false;
  if (!isNavigationDocumentRequest(request)) return false;
  return !pendingNavigationUrl || isSameNavigationUrl(request.request.url, pendingNavigationUrl);
}
