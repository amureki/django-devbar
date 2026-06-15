import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  isSameNavigationUrl,
  shouldResetForMainDocumentRequest,
} from '../src/navigation.js';

function request(url, { resourceType, headers = [] } = {}) {
  return {
    _resourceType: resourceType,
    request: { url, headers },
  };
}

function shouldReset(overrides = {}) {
  return shouldResetForMainDocumentRequest({
    request: request('https://example.com/page', { resourceType: 'document' }),
    pageUrl: 'https://example.com/page',
    pendingNavigationUrl: null,
    hasCapturedRequests: true,
    skipRender: false,
    ...overrides,
  });
}

describe('isSameNavigationUrl', () => {
  it('ignores hash changes', () => {
    assert.equal(
      isSameNavigationUrl('https://example.com/page#one', 'https://example.com/page#two'),
      true,
    );
  });

  it('keeps query string changes distinct', () => {
    assert.equal(
      isSameNavigationUrl('https://example.com/page?one=1', 'https://example.com/page?one=2'),
      false,
    );
  });
});

describe('shouldResetForMainDocumentRequest', () => {
  it('resets for a real same-URL document reload', () => {
    assert.equal(shouldReset(), true);
  });

  it('does not reset on History API navigation alone or following XHRs', () => {
    assert.equal(
      shouldReset({
        request: request('https://example.com/page', { headers: [{ name: 'sec-fetch-mode', value: 'cors' }] }),
        pendingNavigationUrl: 'https://example.com/page',
      }),
      false,
    );
  });

  it('does not lose a pending same-URL reload when an XHR finishes first', () => {
    const pendingNavigationUrl = 'https://example.com/page';

    assert.equal(
      shouldReset({
        request: request('https://example.com/page', { headers: [{ name: 'sec-fetch-mode', value: 'cors' }] }),
        pendingNavigationUrl,
      }),
      false,
    );
    assert.equal(
      shouldReset({
        request: request('https://example.com/page', { resourceType: 'document' }),
        pendingNavigationUrl,
      }),
      true,
    );
  });

  it('does not reset for same-page HTML XHRs without document markers', () => {
    assert.equal(
      shouldReset({
        request: request('https://example.com/page'),
        pendingNavigationUrl: 'https://example.com/page',
      }),
      false,
    );
  });

  it('accepts Sec-Fetch-Dest document as a document marker', () => {
    assert.equal(
      shouldReset({
        request: request('https://example.com/page', {
          headers: [{ name: 'Sec-Fetch-Dest', value: 'document' }],
        }),
      }),
      true,
    );
  });

  it('does not reset for pending navigation URL mismatches', () => {
    assert.equal(
      shouldReset({
        request: request('https://example.com/page', { resourceType: 'document' }),
        pageUrl: 'https://example.com/page',
        pendingNavigationUrl: 'https://example.com/other',
      }),
      false,
    );
  });

  it('matches reload requests when only the hash differs', () => {
    assert.equal(
      shouldReset({
        request: request('https://example.com/page', { resourceType: 'document' }),
        pageUrl: 'https://example.com/page#section',
        pendingNavigationUrl: 'https://example.com/page#section',
      }),
      true,
    );
  });
});
