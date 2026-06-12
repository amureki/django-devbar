/**
 * Tests for changes introduced in the PR:
 *   1. `isSameNavigationUrl` function
 *   2. `onNavigated` listener skipping state reset for same-url navigation
 */

import { describe, it, expect, beforeAll, beforeEach, vi } from 'vitest';

// ---------------------------------------------------------------------------
// isSameNavigationUrl — pure function
//
// The function is not exported from panel.js (side-effecting browser script),
// so we define it here identically to the implementation under test. This is
// intentional: isSameNavigationUrl is a self-contained pure function and its
// full logic can be verified this way.  The onNavigated integration tests
// below confirm the function is actually wired up in the real module.
// ---------------------------------------------------------------------------

function isSameNavigationUrl(previousUrl, nextUrl) {
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

// ---------------------------------------------------------------------------
// Pure-function unit tests
// ---------------------------------------------------------------------------

describe('isSameNavigationUrl', () => {
  describe('falsy arguments', () => {
    it('returns false when previousUrl is null', () => {
      expect(isSameNavigationUrl(null, 'https://example.com/')).toBe(false);
    });

    it('returns false when nextUrl is null', () => {
      expect(isSameNavigationUrl('https://example.com/', null)).toBe(false);
    });

    it('returns false when previousUrl is undefined', () => {
      expect(isSameNavigationUrl(undefined, 'https://example.com/')).toBe(false);
    });

    it('returns false when nextUrl is undefined', () => {
      expect(isSameNavigationUrl('https://example.com/', undefined)).toBe(false);
    });

    it('returns false when previousUrl is empty string', () => {
      expect(isSameNavigationUrl('', 'https://example.com/')).toBe(false);
    });

    it('returns false when nextUrl is empty string', () => {
      expect(isSameNavigationUrl('https://example.com/', '')).toBe(false);
    });

    it('returns false when both args are null', () => {
      expect(isSameNavigationUrl(null, null)).toBe(false);
    });
  });

  describe('identical URLs', () => {
    it('returns true for identical absolute URLs', () => {
      expect(isSameNavigationUrl('https://example.com/', 'https://example.com/')).toBe(true);
    });

    it('returns true for identical URLs with path', () => {
      expect(isSameNavigationUrl(
        'https://example.com/path/to/page',
        'https://example.com/path/to/page',
      )).toBe(true);
    });

    it('returns true for identical URLs with query string', () => {
      expect(isSameNavigationUrl(
        'https://example.com/search?q=hello',
        'https://example.com/search?q=hello',
      )).toBe(true);
    });
  });

  describe('hash-only differences', () => {
    it('returns true when only the hash changes', () => {
      expect(isSameNavigationUrl(
        'https://example.com/page#section1',
        'https://example.com/page#section2',
      )).toBe(true);
    });

    it('returns true when hash is removed', () => {
      expect(isSameNavigationUrl(
        'https://example.com/page#anchor',
        'https://example.com/page',
      )).toBe(true);
    });

    it('returns true when hash is added', () => {
      expect(isSameNavigationUrl(
        'https://example.com/page',
        'https://example.com/page#new-section',
      )).toBe(true);
    });

    it('returns true when both URLs have same path but different hashes', () => {
      expect(isSameNavigationUrl(
        'https://example.com/docs#intro',
        'https://example.com/docs#conclusion',
      )).toBe(true);
    });

    it('returns true when hash changes alongside query string stays the same', () => {
      expect(isSameNavigationUrl(
        'https://example.com/page?tab=one#top',
        'https://example.com/page?tab=one#bottom',
      )).toBe(true);
    });
  });

  describe('genuinely different URLs', () => {
    it('returns false when the path differs', () => {
      expect(isSameNavigationUrl(
        'https://example.com/page-a',
        'https://example.com/page-b',
      )).toBe(false);
    });

    it('returns false when the host differs', () => {
      expect(isSameNavigationUrl(
        'https://example.com/page',
        'https://other.com/page',
      )).toBe(false);
    });

    it('returns false when the scheme differs', () => {
      expect(isSameNavigationUrl(
        'http://example.com/page',
        'https://example.com/page',
      )).toBe(false);
    });

    it('returns false when the query string differs', () => {
      expect(isSameNavigationUrl(
        'https://example.com/search?q=hello',
        'https://example.com/search?q=world',
      )).toBe(false);
    });

    it('returns false when the port differs', () => {
      expect(isSameNavigationUrl(
        'https://example.com:8080/page',
        'https://example.com:9090/page',
      )).toBe(false);
    });

    it('returns false when path differs even with matching hash', () => {
      expect(isSameNavigationUrl(
        'https://example.com/page-a#section',
        'https://example.com/page-b#section',
      )).toBe(false);
    });
  });

  describe('relative URL resolution', () => {
    it('treats a relative nextUrl as relative to the previous URL', () => {
      // new URL('/other', 'https://example.com/page') → 'https://example.com/other'
      // These are different pages, so should return false.
      expect(isSameNavigationUrl(
        'https://example.com/page',
        '/other',
      )).toBe(false);
    });

    it('returns true for a hash-only relative nextUrl', () => {
      // new URL('#new-hash', 'https://example.com/page#old') resolves to
      // 'https://example.com/page#new-hash'. After stripping hashes, both
      // sides become 'https://example.com/page'.
      expect(isSameNavigationUrl(
        'https://example.com/page#old',
        '#new-hash',
      )).toBe(true);
    });
  });

  describe('invalid / non-parseable URLs (fallback path)', () => {
    it('returns true for non-URL strings with the same base (no hash)', () => {
      // Both throw in new URL(); fallback compares split('#')[0]
      expect(isSameNavigationUrl('not-a-url', 'not-a-url')).toBe(true);
    });

    it('returns true for non-URL strings differing only by hash', () => {
      expect(isSameNavigationUrl('not-a-url#foo', 'not-a-url#bar')).toBe(true);
    });

    it('returns false for distinct non-URL strings', () => {
      expect(isSameNavigationUrl('page-one', 'page-two')).toBe(false);
    });

    it('returns false for non-URL strings that differ before the hash', () => {
      expect(isSameNavigationUrl('page-one#hash', 'page-two#hash')).toBe(false);
    });
  });

  describe('edge cases', () => {
    it('returns true for the same URL with an empty hash fragment', () => {
      expect(isSameNavigationUrl(
        'https://example.com/page#',
        'https://example.com/page',
      )).toBe(true);
    });

    it('returns true for two URLs that both have an empty hash fragment', () => {
      expect(isSameNavigationUrl(
        'https://example.com/page#',
        'https://example.com/page#',
      )).toBe(true);
    });

    it('handles URLs with username/password in the authority', () => {
      expect(isSameNavigationUrl(
        'https://user:pass@example.com/page#a',
        'https://user:pass@example.com/page#b',
      )).toBe(true);
    });

    it('returns false when username differs', () => {
      expect(isSameNavigationUrl(
        'https://alice@example.com/page',
        'https://bob@example.com/page',
      )).toBe(false);
    });
  });
});

// ---------------------------------------------------------------------------
// Integration tests: onNavigated listener behaviour
//
// panel.js runs side effects at module level (addListener calls, DOM reads).
// We mock the required globals before importing the module, then drive the
// captured onNavigated callback to verify that same-URL navigation does NOT
// reset state while a different-URL navigation DOES reset it.
// ---------------------------------------------------------------------------

describe('onNavigated listener', () => {
  let onNavigatedCallback;
  let evalCallback;

  beforeAll(async () => {
    // Set up a minimal DOM expected by panel.js at load time.
    document.body.innerHTML = '<div id="app"></div>';

    // Mock the extension API consumed by panel.js at module scope.
    globalThis.chrome = {
      storage: {
        local: {
          get: vi.fn((_keys, cb) => cb && cb({})),
          set: vi.fn(),
        },
      },
      devtools: {
        inspectedWindow: {
          eval: vi.fn((_expr, cb) => {
            // Capture the callback so we can fire it to initialise pageUrl.
            evalCallback = cb;
          }),
        },
        network: {
          onNavigated: {
            addListener: vi.fn((cb) => {
              onNavigatedCallback = cb;
            }),
          },
          onRequestFinished: {
            addListener: vi.fn(),
          },
          getHAR: vi.fn(),
        },
      },
    };

    // Import panel.js once; it registers all its listeners during this call.
    await import('../panel.js');

    // Simulate evalInspectedWindow resolving the initial page URL.
    if (evalCallback) {
      evalCallback('https://example.com/page', null);
    }
  });

  it('captures the onNavigated listener during module load', () => {
    expect(typeof onNavigatedCallback).toBe('function');
  });

  it('resets DOM state when navigating to a different page', () => {
    // Navigate to a completely different URL — state must be reset.
    onNavigatedCallback('https://example.com/other-page');

    // renderUI() is invoked after the reset; with an empty requestHistory and
    // null currentRequest it renders the empty-state placeholder.
    const app = document.getElementById('app');
    expect(app.innerHTML).toContain('No requests captured yet');
  });

  it('does NOT call renderUI when navigating via hash change only', () => {
    const app = document.getElementById('app');

    // Ensure pageUrl is /page by navigating there from a different URL first.
    // This triggers a real reset (different URLs), so sentinel is set after.
    onNavigatedCallback('https://example.com/base-page');
    onNavigatedCallback('https://example.com/page');
    // Now pageUrl === 'https://example.com/page'. Set sentinel.
    app.innerHTML = '<div class="sentinel">existing content</div>';

    // Navigate to the same page with only a hash change — renderUI must be skipped.
    onNavigatedCallback('https://example.com/page#new-section');

    expect(app.innerHTML).toContain('sentinel');
  });

  it('does not reset DOM state for an identical URL (no hash)', () => {
    const app = document.getElementById('app');

    // Establish pageUrl = /page by first navigating away then back.
    onNavigatedCallback('https://example.com/setup-page');
    onNavigatedCallback('https://example.com/page');
    app.innerHTML = '<div class="sentinel">existing content</div>';

    // Navigate to exactly the same URL — renderUI must be skipped.
    onNavigatedCallback('https://example.com/page');

    expect(app.innerHTML).toContain('sentinel');
  });

  it('still updates pageUrl for hash-only navigation so subsequent real navigation resets state', () => {
    // Establish pageUrl = /page.
    onNavigatedCallback('https://example.com/setup-different');
    onNavigatedCallback('https://example.com/page');

    // Trigger a hash-only navigation (no reset, pageUrl becomes /page#step2).
    onNavigatedCallback('https://example.com/page#step2');

    // Now navigate to a genuinely different URL — the reset must happen even
    // though pageUrl was last set during a hash-only navigation.
    onNavigatedCallback('https://example.com/completely-different');

    const app = document.getElementById('app');
    expect(app.innerHTML).toContain('No requests captured yet');
  });

  it('does not reset DOM state when hash changes multiple times in a row', () => {
    const app = document.getElementById('app');

    // Establish pageUrl = /page.
    onNavigatedCallback('https://example.com/setup-base');
    onNavigatedCallback('https://example.com/page');
    app.innerHTML = '<div class="sentinel">stable content</div>';

    // Each subsequent navigation only changes the hash → renderUI must be skipped.
    onNavigatedCallback('https://example.com/page#alpha');
    onNavigatedCallback('https://example.com/page#beta');

    expect(app.innerHTML).toContain('sentinel');
  });
});