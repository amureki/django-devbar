// Store request history
let requestHistory = [];
let currentRequest = null;

// Listen for network requests
chrome.devtools.network.onRequestFinished.addListener(function(request) {
  // Check if this request has DevBar headers
  const headers = {};
  request.response.headers.forEach(header => {
    if (header.name.startsWith('DevBar-')) {
      headers[header.name] = header.value;
    }
  });

  // Only process if DevBar headers are present
  if (Object.keys(headers).length === 0) {
    return;
  }

  // Parse the data
  let data = null;

  // Try to parse the DevBar-Data header (extension mode)
  if (headers['DevBar-Data']) {
    try {
      data = JSON.parse(headers['DevBar-Data']);
    } catch (e) {
      console.error('Failed to parse DevBar-Data header:', e);
    }
  }

  // Fallback to individual headers if DevBar-Data is not available
  if (!data && headers['DevBar-Query-Count']) {
    data = {
      count: parseInt(headers['DevBar-Query-Count'], 10),
      db_time: parseFloat(headers['DevBar-DB-Time']) || 0,
      app_time: parseFloat(headers['DevBar-App-Time']) || 0,
      total_time: (parseFloat(headers['DevBar-DB-Time']) || 0) + (parseFloat(headers['DevBar-App-Time']) || 0),
      has_duplicates: !!headers['DevBar-Duplicates'],
      duplicates: []
    };
  }

  if (!data) {
    return;
  }

  // Create request object
  const requestData = {
    url: request.request.url,
    method: request.request.method,
    timestamp: new Date(),
    data: data
  };

  // Update current request
  currentRequest = requestData;

  // Add to history (keep last 50)
  requestHistory.unshift(requestData);
  if (requestHistory.length > 50) {
    requestHistory.pop();
  }

  // Render the UI
  renderUI();
});

function renderUI() {
  const app = document.getElementById('app');

  if (!currentRequest) {
    return;
  }

  const data = currentRequest.data;

  let html = `
    <div class="request-card">
      <div class="request-header">
        <div>
          <span class="request-method">${currentRequest.method}</span>
          <span class="request-url" title="${currentRequest.url}">${currentRequest.url}</span>
        </div>
      </div>

      <div class="metrics-grid">
        <div class="metric">
          <div class="metric-label">DB Time</div>
          <div class="metric-value">${data.db_time.toFixed(0)}<span class="metric-unit">ms</span></div>
        </div>
        <div class="metric">
          <div class="metric-label">App Time</div>
          <div class="metric-value">${data.app_time.toFixed(0)}<span class="metric-unit">ms</span></div>
        </div>
        <div class="metric">
          <div class="metric-label">Total Time</div>
          <div class="metric-value">${data.total_time.toFixed(0)}<span class="metric-unit">ms</span></div>
        </div>
        <div class="metric">
          <div class="metric-label">Queries</div>
          <div class="metric-value">${data.count}</div>
        </div>
      </div>
  `;

  if (data.has_duplicates && data.duplicates && data.duplicates.length > 0) {
    html += `
      <div class="warning">
        ⚠️ Duplicate queries detected (${data.duplicates.length})
      </div>
      <div class="duplicates-section">
        <div class="duplicates-header">Duplicate Queries:</div>
    `;

    data.duplicates.forEach(dup => {
      html += `
        <div class="duplicate-query">
          <div class="duplicate-sql">${escapeHtml(dup.sql)}</div>
          <div class="duplicate-params">Params: ${escapeHtml(dup.params || 'None')}</div>
          <div class="duplicate-duration">Duration: ${dup.duration.toFixed(2)}ms</div>
        </div>
      `;
    });

    html += `</div>`;
  }

  html += `</div>`;

  // Add history section if there's more than one request
  if (requestHistory.length > 1) {
    html += `
      <div class="history-section">
        <div class="history-header">Recent Requests (${requestHistory.length})</div>
    `;

    requestHistory.slice(0, 10).forEach((req, index) => {
      const time = req.timestamp.toLocaleTimeString();
      html += `
        <div class="history-item" onclick="showRequest(${index})">
          <div>
            <span class="request-method">${req.method}</span>
            <span class="history-url" title="${req.url}">${req.url}</span>
          </div>
          <div class="history-stats">
            <span>DB: ${req.data.db_time.toFixed(0)}ms</span>
            <span>Queries: ${req.data.count}</span>
            <span>${time}</span>
          </div>
        </div>
      `;
    });

    html += `</div>`;
  }

  app.innerHTML = html;
}

function showRequest(index) {
  currentRequest = requestHistory[index];
  renderUI();
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Make showRequest available globally
window.showRequest = showRequest;
