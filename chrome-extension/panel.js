(function() {
  'use strict';

  const MAX_HISTORY = 50;

  let requestHistory = [];
  let currentRequest = null;
  let pageUrl = null;
  let pageUrlReady = false;
  let pendingHarLog = null;

  chrome.devtools.inspectedWindow.eval('location.href', (result, error) => {
    if (error || !result) return;
    pageUrl = result;
    pageUrlReady = true;

    if (pendingHarLog) {
      processHarLog(pendingHarLog);
      pendingHarLog = null;
    }
  });

  chrome.devtools.network.onNavigated.addListener((url) => {
    pageUrl = url;
    requestHistory = [];
    currentRequest = null;
    renderUI();
  });

  const formatMs = (value) => (value != null ? value.toFixed(0) : '0');
  const formatTime = (date) => {
    const h = date.getHours(), m = date.getMinutes(), s = date.getSeconds(), ms = date.getMilliseconds();
    return `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}.${String(ms).padStart(3,'0')}`;
  };

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function parseDevBarHeaders(headers) {
    const devbarHeaders = {};
    for (const { name, value } of headers) {
      const lowerName = name.toLowerCase();
      if (lowerName.startsWith('devbar-')) {
        devbarHeaders[lowerName] = value;
      }
    }

    if (Object.keys(devbarHeaders).length === 0) return null;

    if (devbarHeaders['devbar-data']) {
      try {
        return JSON.parse(devbarHeaders['devbar-data']);
      } catch (e) {
        console.error('Failed to parse DevBar-Data header:', e);
      }
    }

    if (devbarHeaders['devbar-query-count']) {
      const dbTime = parseFloat(devbarHeaders['devbar-db-time']) || 0;
      const appTime = parseFloat(devbarHeaders['devbar-app-time']) || 0;
      return {
        count: parseInt(devbarHeaders['devbar-query-count'], 10),
        db_time: dbTime,
        app_time: appTime,
        total_time: dbTime + appTime,
        has_duplicates: !!devbarHeaders['devbar-duplicates'],
        duplicates: []
      };
    }

    return null;
  }

  function isDocumentRequest(request) {
    if (request._resourceType === 'document') return true;
    const contentType = request.response.headers.find(
      h => h.name.toLowerCase() === 'content-type'
    );
    return contentType?.value.includes('text/html');
  }

  function isMainPageRequest(url) {
    if (!pageUrl) return false;
    const normalize = (u) => u.split('?')[0].replace(/\/$/, '');
    return normalize(url) === normalize(pageUrl);
  }

  function processRequest(request, options = {}) {
    const data = parseDevBarHeaders(request.response.headers);
    if (!data) return;

    const isDocument = isDocumentRequest(request);
    const isMainPage = isMainPageRequest(request.request.url);

    const requestData = {
      url: request.request.url,
      method: request.request.method,
      timestamp: new Date(request.startedDateTime || Date.now()),
      data,
      isDocument,
      isMainPage
    };

    if (isMainPage) {
      currentRequest = requestData;
    } else if (isDocument && !currentRequest?.isMainPage) {
      currentRequest = requestData;
    } else if (!currentRequest) {
      currentRequest = requestData;
    }

    const isDuplicate = requestHistory.some(
      r => r.url === requestData.url && r.timestamp.getTime() === requestData.timestamp.getTime()
    );
    if (!isDuplicate) {
      requestHistory.unshift(requestData);
      if (requestHistory.length > MAX_HISTORY) {
        requestHistory.pop();
      }
    }

    if (!options.skipRender) {
      renderUI();
    }
  }

  function renderMetric(label, value, unit = '') {
    return `<span class="metric"><span class="metric-label">${label}</span> ${value}${unit ? `<span class="metric-unit">${unit}</span>` : ''}</span>`;
  }

  function getRequestType(req) {
    if (req.isMainPage) return { class: 'type-page', label: 'PAGE' };
    if (req.isDocument) return { class: 'type-doc', label: 'DOC' };
    return { class: 'type-xhr', label: 'XHR' };
  }

  function renderUI() {
    const app = document.getElementById('app');
    if (!currentRequest) return;

    const { data, method, url } = currentRequest;
    const type = getRequestType(currentRequest);

    let html = `
      <div class="current">
        <div class="req-left">
          <span class="request-type ${type.class}">${type.label}</span>
          <span class="request-method">${escapeHtml(method)}</span>
          <span class="request-url" title="${escapeHtml(url)}">${escapeHtml(url)}</span>
        </div>
        <div class="metrics">
          ${renderMetric('DB', formatMs(data.db_time), 'ms')}
          ${renderMetric('App', formatMs(data.app_time), 'ms')}
          ${renderMetric('Queries', data.count ?? 0)}
          ${data.has_duplicates ? `<span class="dup-warn">⚠ ${data.duplicates?.length || ''} dup</span>` : ''}
        </div>
      </div>`;

    if (data.has_duplicates && data.duplicates?.length > 0) {
      html += `<div class="dups">${data.duplicates.map(dup =>
        `<div class="dup"><code>${escapeHtml(dup.sql)}</code> <span class="dup-time">${(dup.duration ?? 0).toFixed(1)}ms</span></div>`
      ).join('')}</div>`;
    }

    const otherRequests = requestHistory
      .filter(r => r !== currentRequest)
      .sort((a, b) => a.isMainPage !== b.isMainPage ? (a.isMainPage ? -1 : 1) : b.timestamp - a.timestamp);

    if (otherRequests.length > 0) {
      html += `<div class="history"><div class="history-title">Other (${otherRequests.length})</div>
        ${otherRequests.map(req => {
          const t = getRequestType(req);
          return `<div class="hist-row">
            <div class="hist-left">
              <span class="request-type ${t.class}">${t.label}</span>
              <span class="request-method">${escapeHtml(req.method)}</span>
              <span class="hist-url" title="${escapeHtml(req.url)}">${escapeHtml(req.url)}</span>
            </div>
            <div class="hist-stats">
              ${renderMetric('DB', formatMs(req.data.db_time), 'ms')}
              ${renderMetric('App', formatMs(req.data.app_time), 'ms')}
              ${renderMetric('Queries', req.data.count ?? 0)}
              ${req.data.has_duplicates ? `<span class="dup-warn">⚠</span>` : ''}
            </div>
          </div>`;
        }).join('')}
      </div>`;
    }

    app.innerHTML = html;
  }


  function processHarLog(harLog) {
    if (!harLog?.entries) return;

    harLog.entries.forEach(entry => processRequest(entry, { skipRender: true }));

    const mainPageReq = requestHistory.find(r => r.isMainPage);

    if (mainPageReq) {
      currentRequest = mainPageReq;
    } else {
      const docRequests = requestHistory.filter(r => r.isDocument);
      const oldestDoc = docRequests[docRequests.length - 1];
      if (oldestDoc) {
        currentRequest = oldestDoc;
      }
    }

    renderUI();
  }

  chrome.devtools.network.getHAR((harLog) => {
    if (pageUrlReady) {
      processHarLog(harLog);
    } else {
      pendingHarLog = harLog;
    }
  });

  chrome.devtools.network.onRequestFinished.addListener(processRequest);
})();
