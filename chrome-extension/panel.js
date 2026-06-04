const MAX_HISTORY = 50;
const STORAGE_KEY = 'django-devbar-show-bar';

const checkbox = document.getElementById('show-bar-toggle');
if (checkbox && chrome && chrome.storage) {
  chrome.storage.local.get([STORAGE_KEY], (result) => {
    checkbox.checked = result[STORAGE_KEY] !== false;
  });

  checkbox.addEventListener('change', () => {
    chrome.storage.local.set({ [STORAGE_KEY]: checkbox.checked });
  });
}

let requestHistory = [];
let currentRequest = null;
let pageUrl = null;
let pageUrlReady = false;
let pendingHarLog = null;
const copyResetTimers = new WeakMap();

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

const formatMs = (value) => value?.toFixed(0) ?? '0';
const formatCopyMs = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(1) : '0.0';
};
const countSimilar = (queries) => queries?.filter(q => q.sim).length ?? 0;
const countDuplicates = (queries) => queries?.filter(q => q.dup).length ?? 0;
const getQueries = (data) => Array.isArray(data?.q) ? data.q : [];
const getQueryId = (idx) => `Q${String(idx + 1).padStart(3, '0')}`;
const getTruncationInfo = (data) => {
  if (!data?.tr) return '';
  const sent = data.q_sent ?? 0;
  const total = data.q_total ?? '?';
  return `Showing ${sent} of ${total} queries. Increase DEVBAR['DEVTOOLS_HEADER_MAX_BYTES'] to see more.`;
};
const formatTime = (date) => {
  const h = date.getHours(), m = date.getMinutes(), s = date.getSeconds(), ms = date.getMilliseconds();
  return `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}.${String(ms).padStart(3,'0')}`;
};

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = String(text ?? '');
  return div.innerHTML;
}

function getQueryLabels(query) {
  const labels = [];
  if (query.dup) labels.push('duplicate');
  if (query.sim) labels.push('similar');
  return labels;
}

function formatQueryTitle(query, idx) {
  const labels = getQueryLabels(query);
  const labelText = labels.length ? ` — ${labels.join(', ')}` : '';
  return `${getQueryId(idx)} — ${formatCopyMs(query.dur)}ms${labelText}`;
}

function formatRequestMarkdown(request) {
  if (!request) return '';

  const { data, method, url } = request;
  const queries = getQueries(data);
  const lines = [
    '# Django DevBar Query Report',
    '',
    '## Request',
    `- method: ${method}`,
    `- path: ${getPathFromUrl(url)}`,
    `- url: ${url}`,
    `- captured_at: ${formatTime(request.timestamp)}`,
    '',
    '## Summary',
    `- total_queries: ${data.c ?? queries.length}`,
    `- copied_queries: ${queries.length}`,
    `- db_time_ms: ${formatCopyMs(data.db)}`,
    `- app_time_ms: ${formatCopyMs(data.app)}`,
    `- duplicate_queries: ${countDuplicates(queries)}`,
    `- similar_queries: ${countSimilar(queries)}`,
    `- truncated: ${Boolean(data.tr)}`,
  ];

  const truncationInfo = getTruncationInfo(data);
  if (truncationInfo) {
    lines.push(`- truncation_note: ${truncationInfo}`);
  }

  if (!queries.length) return `${lines.join('\n')}\n`;

  lines.push('', '## Queries');
  queries.forEach((query, idx) => {
    const fence = getMarkdownFence(query.s);
    lines.push('', `### ${formatQueryTitle(query, idx)}`, '', `${fence}sql`, query.s ?? '', fence);
  });

  return `${lines.join('\n')}\n`;
}

function getMarkdownFence(text) {
  const backtickRuns = String(text ?? '').match(/`+/g) ?? [];
  const longestRun = backtickRuns.reduce((longest, run) => Math.max(longest, run.length), 0);
  return '`'.repeat(Math.max(3, longestRun + 1));
}

function formatRequestSql(request) {
  return getQueries(request?.data).map((query, idx) => {
    return `-- ${formatQueryTitle(query, idx)}\n${query.s ?? ''}`;
  }).join('\n\n');
}

async function writeClipboard(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.left = '-9999px';
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  try {
    document.execCommand('copy');
  } finally {
    textarea.remove();
  }
}

function flashCopied(button, label = 'Copied') {
  const original = button.dataset.originalLabel || button.textContent;
  button.dataset.originalLabel = original;
  clearTimeout(copyResetTimers.get(button));

  button.textContent = label;
  button.classList.add('is-copied');

  const timer = setTimeout(() => {
    button.textContent = original;
    button.classList.remove('is-copied');
    copyResetTimers.delete(button);
  }, 1200);
  copyResetTimers.set(button, timer);
}

function formatSql(sql) {
  const escaped = escapeHtml(sql);
  const keywordRegex = /\b(SELECT|FROM|WHERE|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN|ON|AND|OR|ORDER BY|GROUP BY|HAVING|LIMIT|OFFSET|INSERT INTO|VALUES|UPDATE|SET|DELETE|CREATE TABLE|ALTER TABLE|DROP TABLE|DISTINCT|COUNT|SUM|AVG|MAX|MIN|UNION|EXISTS|IN|IS NULL|IS NOT NULL|LIKE|BETWEEN|CASE|WHEN|THEN|ELSE|END|ASC|DESC|AS|WITH|RECURSIVE)\b/gi;
  return escaped.replace(keywordRegex, (match) => `<span class="sql-keyword">${match}</span>`);
}

function getPathFromUrl(url) {
  try {
    const parsed = new URL(url);
    return parsed.pathname + parsed.search;
  } catch (e) {
    return url;
  }
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
      duplicates: []
    };
  }

  return null;
}

function isDocumentRequest(request) {
  if (request._resourceType === 'document') return true;
  const contentType = request.response.headers.find(h => h.name.toLowerCase() === 'content-type');
  return contentType?.value.includes('text/html') ?? false;
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

function getDurationClass(duration) {
  if (duration > 50) return 'slow';
  if (duration > 10) return 'medium';
  return 'fast';
}

function getQueryClass(query) {
  if (query.dup) return ' duplicate';
  if (query.sim) return ' similar';
  return '';
}

function renderWaterfallChart(queries) {
  if (!Array.isArray(queries) || queries.length === 0) return '';

  let cumulativeTime = 0;
  const queriesWithStartTime = queries.map(q => {
    const startTime = cumulativeTime;
    cumulativeTime += q.dur ?? 0;
    return { ...q, start_time: startTime };
  });

  const maxEndTime = cumulativeTime;

  const gridInterval = maxEndTime > 100 ? 20 : maxEndTime > 50 ? 10 : 5;
  const gridLines = [];
  if (maxEndTime > 0) {
    for (let t = 0; t <= maxEndTime; t += gridInterval) {
      const position = (t / maxEndTime) * 100;
      gridLines.push(`
        <div class="waterfall-grid-line" style="left: ${position}%"></div>
        <div class="waterfall-grid-label" style="left: ${position}%">${t}ms</div>
      `);
    }
  }

  return `<div class="waterfall-grid-lines">${gridLines.join('')}</div>
    ${queriesWithStartTime.map((query, idx) => {
      const duration = query.dur ?? 0;
      const startTime = query.start_time ?? 0;
      const barWidth = maxEndTime > 0 ? (duration / maxEndTime) * 100 : 0;
      const barLeft = maxEndTime > 0 ? (startTime / maxEndTime) * 100 : 0;
      const formattedSql = formatSql(query.s);

      return `
      <div class="query${getQueryClass(query)}" data-idx="${idx}">
        <div class="query-header">
          <span class="query-index">#${idx + 1}</span>
          <span class="query-summary" title="${escapeHtml(query.s)}"><code>${formattedSql}</code></span>
          <span class="query-time">${duration.toFixed(1)}ms</span>
        </div>
        <div class="waterfall-row">
          <span class="waterfall-start">${startTime.toFixed(1)}ms</span>
          <div class="waterfall-chart">
            <div class="timing-bar ${getDurationClass(duration)}" style="width: ${barWidth}%; margin-left: ${barLeft}%"></div>
          </div>
          <span class="waterfall-end">${(startTime + duration).toFixed(1)}ms</span>
        </div>
      </div>`;
    }).join('')}`;
}

function renderEmptyState() {
  const app = document.getElementById('app');
  const html = `
    <div class="empty-state">
      <h2>Django DevBar</h2>
      <p style="margin-top: 12px;">No requests captured yet.</p>
      <p style="margin-top: 6px;">Navigate to a page with Django DevBar enabled.</p>
      <div style="margin-top: 16px; font-size: 11px; color: #888; line-height: 1.6;">
        <strong>Troubleshooting:</strong><br>
        • Make sure Django DevBar middleware is installed<br>
        • Set <span class="code">DEVBAR = {'ENABLE_DEVTOOLS_DATA': True}</span> in settings<br>
        • Reload the page after enabling headers
      </div>
      <p style="margin-top: 12px; font-size: 10px;">
        <a href="https://github.com/amureki/django-devbar" target="_blank" style="color: #1a73e8;">django-devbar</a>
      </p>
    </div>`;
  app.innerHTML = html;
}

function renderUI() {
  const app = document.getElementById('app');
  if (!currentRequest) {
    renderEmptyState();
    return;
  }

  const { data, method, url } = currentRequest;
  const type = getRequestType(currentRequest);
  const queries = getQueries(data);
  const currentDuplicateCount = countDuplicates(queries);
  const currentSimilarCount = countSimilar(queries);
  const truncationInfo = getTruncationInfo(data);

  let html = `
    <div class="current">
      <div class="req-left">
        <span class="request-type ${type.class}">${type.label}</span>
        <span class="request-method">${escapeHtml(method)}</span>
        <span class="request-url" title="${escapeHtml(url)}">${escapeHtml(getPathFromUrl(url))}</span>
        <a href="${escapeHtml(url)}" target="_blank" class="url-link" title="Open in new tab" aria-label="Open request URL in new tab">↗</a>
      </div>
      <div class="current-right">
        <div class="metrics">
          ${renderMetric('queries', data.c ?? 0)}
          ${renderMetric('db', formatMs(data.db), 'ms')}
          ${renderMetric('app', formatMs(data.app), 'ms')}
          ${currentDuplicateCount ? `<span class="dup-warn">⚠ ${currentDuplicateCount} dup</span>` : ''}
          ${currentSimilarCount ? `<span class="sim-warn">≈ ${currentSimilarCount} sim</span>` : ''}
          <span class="metric-label">${formatTime(currentRequest.timestamp)}</span>
        </div>
        <div class="panel-actions">
          <button type="button" class="copy-button" data-action="copy-request-sql" ${queries.length ? '' : 'disabled'}>Copy SQL</button>
          <button type="button" class="copy-button primary" data-action="copy-request-markdown">Copy Markdown</button>
        </div>
      </div>
    </div>`;

  if (queries.length > 0) {
    html += `<div class="queries"><div class="waterfall-container">
      ${renderWaterfallChart(queries)}
    </div>
    ${truncationInfo ? `<div class="trunc-note">${escapeHtml(truncationInfo)}</div>` : ''}
    </div>`;
  } else if (truncationInfo) {
    html += `<div class="queries"><div class="trunc-note">${escapeHtml(truncationInfo)}</div></div>`;
  }

  const hasPageOrDoc = requestHistory.some(r => r.isMainPage || r.isDocument);

  const otherRequests = requestHistory
    .filter(r => r !== currentRequest)
    .sort((a, b) => {
      if (hasPageOrDoc) {
        if (a.isMainPage !== b.isMainPage) return a.isMainPage ? -1 : 1;
      }
      return b.timestamp - a.timestamp;
    });

  if (otherRequests.length > 0) {
    const sectionTitle = hasPageOrDoc ? 'Other' : 'Recent Requests';
    html += `<div class="history"><div class="history-title">${sectionTitle} (${otherRequests.length})</div>
      ${otherRequests.map(req => {
        const t = getRequestType(req);
        const duplicateCount = countDuplicates(req.data.q);
        const similarCount = countSimilar(req.data.q);
        return `<div class="hist-row">
          <div class="hist-left">
            <span class="request-type ${t.class}">${t.label}</span>
            <span class="request-method">${escapeHtml(req.method)}</span>
            <span class="hist-url" title="${escapeHtml(req.url)}">${escapeHtml(getPathFromUrl(req.url))}</span>
            <a href="${escapeHtml(req.url)}" target="_blank" class="url-link" title="Open in new tab" aria-label="Open request URL in new tab">↗</a>
          </div>
          <div class="hist-stats">
            ${renderMetric('queries', req.data.c ?? 0)}
            ${renderMetric('db', formatMs(req.data.db), 'ms')}
            ${renderMetric('app', formatMs(req.data.app), 'ms')}
            ${duplicateCount ? `<span class="dup-warn">⚠</span>` : ''}
            ${similarCount ? `<span class="sim-warn">≈</span>` : ''}
            <span class="metric-label">${formatTime(req.timestamp)}</span>
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

  currentRequest = requestHistory.find(r => r.isMainPage)
    || requestHistory.filter(r => r.isDocument).pop();

  renderUI();
}

document.addEventListener('click', async (event) => {
  const button = event.target.closest('button[data-action]');
  if (!button) return;

  const action = button.dataset.action;

  try {
    switch (action) {
      case 'copy-request-markdown':
        await writeClipboard(formatRequestMarkdown(currentRequest));
        flashCopied(button);
        break;
      case 'copy-request-sql':
        await writeClipboard(formatRequestSql(currentRequest));
        flashCopied(button);
        break;
      default:
        return;
    }
  } catch (error) {
    console.error('Failed to copy DevBar content:', error);
    flashCopied(button, 'Copy failed');
  }
});

chrome.devtools.network.getHAR((harLog) => {
  if (pageUrlReady) {
    processHarLog(harLog);
  } else {
    pendingHarLog = harLog;
  }
});

chrome.devtools.network.onRequestFinished.addListener(processRequest);

renderEmptyState();
