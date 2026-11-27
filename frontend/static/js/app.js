const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
let sessionId = "web_session_" + Math.random().toString(36).substring(2, 9);
let pendingAttachments = [];
let isSending = false;

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function renderInline(str) {
  if (!str) return '';
  return str
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
}

function fallbackRenderMarkdown(md) {
  if (!md) return '';
  let html = escapeHtml(md);

  // 1. Tables: lines starting and ending with |
  html = html.replace(/(?:^|\n)((?:\|[^\r\n]+\|\r?\n?){2,})/g, function(match, tableBlock) {
    const lines = tableBlock.trim().split(/\r?\n/).map(l => l.trim());
    if (lines.length < 2) return match;
    const headerCols = lines[0].split('|').slice(1, -1).map(c => c.trim());
    const isSep = lines[1].split('|').slice(1, -1).every(c => /^:?-+:?$/.test(c.trim()));
    if (!isSep) return match;

    let tableHtml = '<div class="table-container"><table class="markdown-table"><thead><tr>';
    headerCols.forEach(h => { tableHtml += '<th>' + renderInline(h) + '</th>'; });
    tableHtml += '</tr></thead><tbody>';

    for (let i = 2; i < lines.length; i++) {
      const rowCols = lines[i].split('|').slice(1, -1).map(c => c.trim());
      if (rowCols.length > 0) {
        tableHtml += '<tr>';
        rowCols.forEach(c => { tableHtml += '<td>' + renderInline(c) + '</td>'; });
        tableHtml += '</tr>';
      }
    }
    tableHtml += '</tbody></table></div>';
    return '\n' + tableHtml + '\n';
  });

  // 2. Headings
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

  // 3. Lists
  html = html.replace(/(?:^|\n)((?:- [^\r\n]+\r?\n?)+)/g, function(m, listBlock) {
    const items = listBlock.trim().split(/\r?\n/).map(l => l.replace(/^- /, '').trim());
    return '<ul>' + items.map(it => '<li>' + renderInline(it) + '</li>').join('') + '</ul>';
  });

  // 4. Inlines
  html = renderInline(html);

  // 5. Paragraphs
  const blocks = html.split(/\n{2,}/);
  html = blocks.map(b => {
    b = b.trim();
    if (b.startsWith('<h') || b.startsWith('<ul') || b.startsWith('<ol') || b.startsWith('<div')) {
      return b;
    }
    return '<p>' + b.replace(/\n/g, '<br>') + '</p>';
  }).join('');

  return html;
}

function safeRenderMarkdown(md) {
  if (!md) return '';
  try {
    if (typeof marked !== 'undefined') {
      if (typeof marked.parse === 'function') {
        const out = marked.parse(md);
        if (typeof out === 'string') return out;
      } else if (typeof marked === 'function') {
        const out = marked(md);
        if (typeof out === 'string') return out;
      }
    }
  } catch (e) {
    console.warn("marked.parse warning, using fallback:", e);
  }

  try {
    return fallbackRenderMarkdown(md);
  } catch (e) {
    console.error("fallbackRenderMarkdown error:", e);
    let s = md.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    s = s.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    return s.replace(/\n/g, '<br>');
  }
}

let currentLoadingBubble = null;

function showLoadingIndicator() {
  removeLoadingIndicator();
  const div = document.createElement('div');
  div.className = 'msg bot';
  div.id = 'loadingBubble';
  div.innerHTML = `
    <div class="typing-indicator">
      <span>FleetHarbor AI is querying real-time database & knowledge base</span>
      <div class="typing-dots">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    </div>
  `;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  currentLoadingBubble = div;
}

function removeLoadingIndicator() {
  if (currentLoadingBubble && currentLoadingBubble.parentNode) {
    currentLoadingBubble.parentNode.removeChild(currentLoadingBubble);
  }
  currentLoadingBubble = null;
}

function addMessage(text, isUser, sources = [], resType = null, attachments = []) {
  const msgDiv = document.createElement('div');
  msgDiv.className = 'msg ' + (isUser ? 'user' : 'bot');

  if (isUser) {
    if (attachments && attachments.length > 0) {
      const attachRow = document.createElement('div');
      attachRow.className = 'msg-attachments';
      attachments.forEach(function (file) {
        const pill = document.createElement('span');
        pill.className = 'msg-attach-pill';
        pill.textContent = '📎 ' + file.name;
        pill.title = file.name + ' (' + formatFileSize(file.size) + ')';
        attachRow.appendChild(pill);
      });
      msgDiv.appendChild(attachRow);
    }
    const p = document.createElement('p');
    p.innerText = text;
    msgDiv.appendChild(p);
  } else {
    msgDiv.innerHTML = safeRenderMarkdown(text);

    const isApologyOrError = text && (
      text.includes('information is not available') ||
      text.includes('not available in the FleetHarbor') ||
      text.includes('temporarily unavailable') ||
      text.includes('I apologize') ||
      text.includes('Sorry, something unexpected')
    );

    if (sources && sources.length > 0 && !isApologyOrError && resType !== 'unavailable' && resType !== 'error') {
      const srcDiv = document.createElement('div');
      srcDiv.className = 'sources-box';
      let tagsHtml = sources.map(s => '<span class="source-tag">🛡️ ' + escapeHtml(s) + '</span>').join('');
      srcDiv.innerHTML = '<div class="sources-title"><span>🔒</span> Verified Data Sources</div><div class="sources-list">' + tagsHtml + '</div>';
      msgDiv.appendChild(srcDiv);
    }
  }

  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

const SUGGESTIONS_POOL = [
  { label: "Track SHP-10001", query: "What is the status of SHP-10001?" },
  { label: "Location of SHP-10005", query: "What is the location of SHP-10005?" },
  { label: "Track SHP-10002", query: "Where is shipment SHP-10002?" },
  { label: "Check SHP-10003 Arrival", query: "Has SHP-10003 arrived at destination?" },
  { label: "ETA for SHP-10004", query: "What is the estimated delivery for SHP-10004?" },
  { label: "Track 10K SHP-15000", query: "What is the status of SHP-15000?" },
  { label: "Track 10K SHP-19999", query: "What is the status of SHP-19999?" },
  { label: "Employee EMP-20001", query: "Look up employee EMP-20001" },
  { label: "Employee EMP-20050", query: "Look up employee EMP-20050" },
  { label: "Customs Clearance Docs", query: "What documents are required for international customs clearance?" },
  { label: "Commercial Invoice Guide", query: "What information must be included on a commercial invoice?" },
  { label: "Bill of Lading Purpose", query: "What is a Bill of Lading and why is it required?" },
  { label: "Certificate of Origin", query: "When is a Certificate of Origin needed for customs?" },
  { label: "Customs Hold Procedures", query: "What should be done if a shipment is placed on customs hold?" },
  { label: "Pharma Cold-Chain Rules", query: "What are the pharma cold-chain rules and temperature ranges?" },
  { label: "Dangerous Goods Hazmat", query: "What documents are required for shipping hazardous materials?" },
  { label: "Perishable Cargo Policy", query: "What are the standard handling procedures for perishable cargo?" },
  { label: "Dry Ice Packaging", query: "What are the rules for shipping with dry ice?" },
  { label: "Define In Transit", query: "What is In Transit?" },
  { label: "FOB vs CIF Shipping Terms", query: "What is the difference between FOB and CIF shipping terms?" },
  { label: "Define Demurrage", query: "What does demurrage mean in freight shipping?" },
  { label: "Shipment Lifecycle", query: "Explain the complete shipment lifecycle from pickup to delivery" },
  { label: "Out for Delivery Meaning", query: "What does Out for Delivery mean?" },
  { label: "Handling Shipment Delays", query: "What happens when a shipment is delayed?" },
  { label: "Proof of Delivery (POD)", query: "How is proof of delivery obtained and verified?" },
  { label: "Air vs Ocean Transit", query: "What are the delivery transit times for air vs ocean freight?" },
  { label: "Cargo Weight Limits", query: "What are standard cargo weight and dimension limits?" }
];

const suggestionsContainer = document.getElementById('suggestionsContainer');

function renderRandomSuggestions(count = 5) {
  if (!suggestionsContainer) return;
  const shuffled = [...SUGGESTIONS_POOL];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  const selected = shuffled.slice(0, count);

  suggestionsContainer.innerHTML = '<span class="suggestions-label">Suggestions:</span>';
  selected.forEach(item => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'suggestion-chip';
    btn.innerText = item.label;
    btn.onclick = () => askQuestion(item.query);
    suggestionsContainer.appendChild(btn);
  });

  const shuffleBtn = document.createElement('button');
  shuffleBtn.type = 'button';
  shuffleBtn.className = 'suggestion-chip suggestion-shuffle';
  shuffleBtn.innerHTML = '🔄 Shuffle';
  shuffleBtn.title = 'Rotate suggestions';
  shuffleBtn.onclick = () => renderRandomSuggestions(count);
  suggestionsContainer.appendChild(shuffleBtn);
}

function askQuestion(q) {
  if (!userInput || isSending) return;
  userInput.value = q;
  handleSend();
}

async function handleSend(e) {
  if (e) {
    if (e.preventDefault) e.preventDefault();
    if (e.stopPropagation) e.stopPropagation();
  }
  if (isSending) return false;
  let query = userInput ? userInput.value.trim() : '';
  if (!query && pendingAttachments.length === 0) return false;

  if (query.length > 2000) {
    addMessage("⚠️ Your question is too long (" + query.length + " chars). Please keep queries under 2000 characters.", false, [], 'error');
    return false;
  }

  isSending = true;

  const sentFiles = pendingAttachments.slice();
  pendingAttachments = [];
  renderAttachTray();

  if (!query && sentFiles.length > 0) {
    query = 'Uploaded ' + sentFiles.map(f => f.name).join(', ');
  }

  // The intro card is only for the start of a dialogue. Remove it on the first question so
  // the question and its answer share the same screen.
  chatMessages.querySelectorAll(':scope > .msg.bot > .welcome-container').forEach(el => el.parentElement.remove());
  addMessage(query, true, [], null, sentFiles);
  addQuestionToHistory(query);
  if (userInput) userInput.value = '';
  if (sendBtn) {
    sendBtn.disabled = true;
    sendBtn.innerText = 'Analyzing...';
  }
  showLoadingIndicator();
  renderRandomSuggestions(5);

  // 1. Process and upload attachments if present
  if (sentFiles.length > 0) {
    for (const file of sentFiles) {
      const formData = new FormData();
      formData.append('file', file);
      try {
        const upResp = await fetch('/upload-doc', {
          method: 'POST',
          body: formData
        });
        const upData = await upResp.json();
        removeLoadingIndicator();
        if (upData.summary) {
          addMessage(upData.summary, false, [file.name + ' (Import Verified)'], 'upload_summary');
        } else if (upData.message) {
          addMessage(`✅ **${file.name}**: ${upData.message}`, false, [file.name], 'upload_summary');
        }
      } catch (uploadErr) {
        console.error('File upload error:', uploadErr);
        removeLoadingIndicator();
        addMessage(`⚠️ **Upload Notice**: Could not process ${file.name}.`, false, [], 'error');
      }
    }

    const isMereAttachmentNote = /^(here\s+is\s+(?:a\s+)?new\s+data|here\s+is\s+data|new\s+data|attached|uploaded\s+.*|here\s+is\s+the\s+file|Uploaded\s+.*)$/i.test(query);
    if (isMereAttachmentNote) {
      isSending = false;
      if (sendBtn) {
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<span>Send</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>';
      }
      if (userInput) userInput.focus();
      return false;
    }

    showLoadingIndicator();
  }

  try {
    const streamResp = await fetch('/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: query, session_id: sessionId })
    });

    if (streamResp.ok && streamResp.body) {
      removeLoadingIndicator();
      const msgDiv = document.createElement('div');
      msgDiv.className = 'msg bot';
      const contentDiv = document.createElement('div');
      contentDiv.className = 'msg-content';
      msgDiv.appendChild(contentDiv);
      chatMessages.appendChild(msgDiv);

      const reader = streamResp.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let accumulatedText = '';
      let finalSources = [];
      let finalResType = null;
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split(/\r?\n/);
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;
          const jsonStr = trimmed.slice(5).trim();
          if (!jsonStr) continue;
          try {
            const event = JSON.parse(jsonStr);
            if (event.token) {
              accumulatedText += event.token;
              contentDiv.innerHTML = safeRenderMarkdown(accumulatedText);
              chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            if (event.done) {
              if (event.response) accumulatedText = event.response;
              finalSources = event.sources || [];
              finalResType = event.response_type || null;
            }
          } catch (e) {
            console.warn('SSE parse error:', e);
          }
        }
      }

      if (!accumulatedText.trim()) {
        accumulatedText = "⚠️ No response received from assistant. Please try again.";
      }
      contentDiv.innerHTML = safeRenderMarkdown(accumulatedText);

      const isApologyOrError = accumulatedText && (
        accumulatedText.includes('information is not available') ||
        accumulatedText.includes('not available in the FleetHarbor') ||
        accumulatedText.includes('temporarily unavailable') ||
        accumulatedText.includes('I apologize') ||
        accumulatedText.includes('Sorry, something unexpected')
      );

      if (finalSources && finalSources.length > 0 && !isApologyOrError && finalResType !== 'unavailable' && finalResType !== 'error') {
        const srcDiv = document.createElement('div');
        srcDiv.className = 'sources-box';
        let tagsHtml = finalSources.map(s => '<span class="source-tag">🛡️ ' + escapeHtml(s) + '</span>').join('');
        srcDiv.innerHTML = '<div class="sources-title"><span>🔒</span> Verified Data Sources</div><div class="sources-list">' + tagsHtml + '</div>';
        msgDiv.appendChild(srcDiv);
      }
      chatMessages.scrollTop = chatMessages.scrollHeight;
    } else if (streamResp.status === 404 || streamResp.status === 405 || streamResp.status === 501 || !streamResp.body) {
      // Synchronous fallback only if streaming route unsupported
      const resp = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query, session_id: sessionId })
      });
      const data = await resp.json();
      removeLoadingIndicator();
      if (resp.ok && data.success) {
        const botResponse = (data.data && data.data.response) || data.response || "No response text received.";
        const botSources = (data.data && data.data.sources) || data.sources || [];
        const resType = (data.data && data.data.response_type) || null;
        addMessage(botResponse, false, botSources, resType);
      } else {
        const detailErrs = data.data && Array.isArray(data.data.errors) ? data.data.errors.join('; ') : '';
        const errMsg = detailErrs || data.message || (data.data && data.data.message) || data.detail || "Server error encountered.";
        addMessage("⚠️ " + escapeHtml(errMsg), false, [], 'error');
      }
    } else {
      // Handle 400 / 413 / 422 / 500 from /chat/stream once without duplicating POST /chat
      removeLoadingIndicator();
      let errData = {};
      try { errData = await streamResp.json(); } catch (_) {}
      const detailErrs = errData.data && Array.isArray(errData.data.errors) ? errData.data.errors.join('; ') : '';
      const errMsg = detailErrs || errData.message || (errData.data && errData.data.message) || errData.detail || `Server error (${streamResp.status}).`;
      addMessage("⚠️ " + escapeHtml(errMsg), false, [], 'error');
    }
  } catch (err) {
    console.error("Fetch error:", err);
    removeLoadingIndicator();
    addMessage("⚠️ Error contacting assistant: " + escapeHtml(err.message), false, [], 'error');
  } finally {
    isSending = false;
    if (sendBtn) {
      sendBtn.disabled = false;
      sendBtn.innerHTML = '<span>Send</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>';
    }
    if (userInput) userInput.focus();
  }
  return false;
}

// ── File attachments ("+" button) ───────────────────────────
const attachBtn = document.getElementById('attachBtn');
const fileInput = document.getElementById('fileInput');
const attachTray = document.getElementById('attachTray');
const REMOVE_ICON = '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function renderAttachTray() {
  if (!attachTray) return;
  attachTray.innerHTML = '';
  attachTray.classList.toggle('has-files', pendingAttachments.length > 0);

  pendingAttachments.forEach(function (file, index) {
    const chip = document.createElement('span');
    chip.className = 'attach-chip';

    const name = document.createElement('span');
    name.className = 'attach-chip-name';
    name.textContent = file.name;
    name.title = file.name;

    const size = document.createElement('span');
    size.className = 'attach-chip-size';
    size.textContent = formatFileSize(file.size);

    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'attach-chip-remove';
    remove.setAttribute('aria-label', 'Remove ' + file.name);
    remove.title = 'Remove file';
    remove.innerHTML = REMOVE_ICON;
    remove.onclick = function () {
      pendingAttachments.splice(index, 1);
      renderAttachTray();
    };

    chip.appendChild(name);
    chip.appendChild(size);
    chip.appendChild(remove);
    attachTray.appendChild(chip);
  });
}

function addAttachments(fileList) {
  Array.from(fileList || []).forEach(function (file) {
    const duplicate = pendingAttachments.some(function (f) {
      return f.name === file.name && f.size === file.size && f.lastModified === file.lastModified;
    });
    if (!duplicate) pendingAttachments.push(file);
  });
  renderAttachTray();
}

if (attachBtn && fileInput) {
  attachBtn.addEventListener('click', function () {
    fileInput.click();
  });
  fileInput.addEventListener('change', function (e) {
    addAttachments(e.target.files);
    e.target.value = '';
    if (userInput) userInput.focus();
  });
}

// ── Question History Management ──────────────────────────────
const HISTORY_KEY = 'fleetharbor_question_history_v2';
const historySidebar = document.getElementById('historySidebar');
const historyBackdrop = document.getElementById('historyBackdrop');
const historyList = document.getElementById('historyList');
const historyCountBadge = document.getElementById('historyCountBadge');
const navHistoryCount = document.getElementById('navHistoryCount');
const toggleHistoryBtn = document.getElementById('toggleHistoryBtn');

function getHistory() {
  try {
    const stored = localStorage.getItem(HISTORY_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (e) {
    console.warn('Failed to read history from localStorage:', e);
    return [];
  }
}

function saveHistory(list) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(list));
  } catch (e) {
    console.warn('Failed to save history to localStorage:', e);
  }
}

function updateHistoryBadges(count) {
  if (historyCountBadge) historyCountBadge.textContent = count;
  if (navHistoryCount) navHistoryCount.textContent = count;
}

function formatTimeAgo(timestamp) {
  if (!timestamp) return 'Earlier';
  const diffSec = Math.floor((Date.now() - timestamp) / 1000);
  if (diffSec < 60) return 'Just now';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return diffMin + 'm ago';
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return diffHour + 'h ago';
  const date = new Date(timestamp);
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

function renderHistoryList(filterQuery = '') {
  if (!historyList) return;
  const history = getHistory();
  updateHistoryBadges(history.length);

  const q = (filterQuery || '').trim().toLowerCase();
  const filtered = q ? history.filter(item => item.query.toLowerCase().includes(q)) : history;

  if (filtered.length === 0) {
    historyList.innerHTML = `
      <div class="history-empty">
        <div class="history-empty-icon">${q ? '🔍' : '💬'}</div>
        <h4>${q ? 'No matching questions' : 'No questions yet'}</h4>
        <p>${q ? 'Try searching for something else.' : 'Questions you ask will appear here so you can re-ask or inspect them anytime.'}</p>
      </div>
    `;
    return;
  }

  historyList.innerHTML = '';
  filtered.forEach((item) => {
    const div = document.createElement('div');
    div.className = 'history-item';
    div.title = 'Click to re-ask: ' + item.query;

    // Content top row
    const topRow = document.createElement('div');
    topRow.className = 'history-item-top';

    const timeSpan = document.createElement('span');
    timeSpan.className = 'history-time';
    timeSpan.textContent = formatTimeAgo(item.timestamp);
    topRow.appendChild(timeSpan);

    // Tool buttons
    const toolsDiv = document.createElement('div');
    toolsDiv.className = 'history-tools';

    // Edit/Insert into input button
    const editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.className = 'tool-btn';
    editBtn.title = 'Edit in input';
    editBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>';
    editBtn.onclick = function(e) {
      e.stopPropagation();
      if (userInput) {
        userInput.value = item.query;
        userInput.focus();
      }
    };
    toolsDiv.appendChild(editBtn);

    // Copy button
    const copyBtn = document.createElement('button');
    copyBtn.type = 'button';
    copyBtn.className = 'tool-btn';
    copyBtn.title = 'Copy question';
    copyBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
    copyBtn.onclick = function(e) {
      e.stopPropagation();
      navigator.clipboard.writeText(item.query).then(() => {
        copyBtn.title = 'Copied!';
        copyBtn.style.color = '#10B981';
        setTimeout(() => {
          copyBtn.title = 'Copy question';
          copyBtn.style.color = '';
        }, 1500);
      });
    };
    toolsDiv.appendChild(copyBtn);

    // Delete button
    const delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.className = 'tool-btn tool-del';
    delBtn.title = 'Remove from history';
    delBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="12" x2="18" y2="18"/></svg>';
    delBtn.onclick = function(e) {
      e.stopPropagation();
      deleteHistoryItem(item.id);
    };
    toolsDiv.appendChild(delBtn);

    topRow.appendChild(toolsDiv);
    div.appendChild(topRow);

    const textDiv = document.createElement('div');
    textDiv.className = 'history-text';
    textDiv.textContent = item.query;
    div.appendChild(textDiv);

    // Tag if shipment or employee ID detected
    const shpMatch = item.query.match(/SHP-\d+/i);
    const empMatch = item.query.match(/EMP-\d+/i);
    if (shpMatch || empMatch) {
      const footDiv = document.createElement('div');
      footDiv.className = 'history-item-footer';
      const tag = document.createElement('span');
      tag.className = 'history-tag';
      tag.textContent = shpMatch ? shpMatch[0].toUpperCase() : empMatch[0].toUpperCase();
      footDiv.appendChild(tag);
      div.appendChild(footDiv);
    }

    // Clicking the item re-asks the question
    div.onclick = function() {
      askQuestion(item.query);
      closeMobileHistory();
    };

    historyList.appendChild(div);
  });
}

function addQuestionToHistory(query) {
  if (!query || !query.trim()) return;
  const clean = query.trim();
  let list = getHistory();

  // Deduplicate: remove if already exists, then prepend to top
  list = list.filter(item => item.query.toLowerCase() !== clean.toLowerCase());

  list.unshift({
    id: 'hist_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
    query: clean,
    timestamp: Date.now()
  });

  // Keep up to 100 recent questions
  if (list.length > 100) list = list.slice(0, 100);

  saveHistory(list);
  renderHistoryList(document.getElementById('historySearchInput') ? document.getElementById('historySearchInput').value : '');
}

function deleteHistoryItem(id) {
  let list = getHistory();
  list = list.filter(item => item.id !== id);
  saveHistory(list);
  renderHistoryList(document.getElementById('historySearchInput') ? document.getElementById('historySearchInput').value : '');
}

function clearAllHistory() {
  const history = getHistory();
  if (history.length === 0) return;
  if (confirm("Clear all previously asked questions from history?")) {
    localStorage.removeItem(HISTORY_KEY);
    renderHistoryList();
  }
}

function filterHistory(val) {
  renderHistoryList(val);
}

function toggleHistorySidebar() {
  if (!historySidebar) return;
  if (window.innerWidth <= 1024) {
    historySidebar.classList.toggle('mobile-open');
    if (historyBackdrop) {
      historyBackdrop.classList.toggle('active', historySidebar.classList.contains('mobile-open'));
    }
  } else {
    historySidebar.classList.toggle('collapsed');
  }
}

function closeMobileHistory() {
  if (historySidebar) historySidebar.classList.remove('mobile-open');
  if (historyBackdrop) historyBackdrop.classList.remove('active');
}

if (toggleHistoryBtn) {
  toggleHistoryBtn.addEventListener('click', toggleHistorySidebar);
}

function startNewChat() {
  sessionId = "web_session_" + Math.random().toString(36).substring(2, 9);
  pendingAttachments = [];
  renderAttachTray();
  removeLoadingIndicator();
  if (userInput) userInput.value = '';
  if (chatMessages) {
    chatMessages.innerHTML = `
      <div class="msg bot">
        <div class="welcome-container">
          <div class="welcome-header">
            <span style="font-size: 1.5rem;">🚢</span>
            <h3>New Dialogue Started</h3>
          </div>
          <p>Conversation memory reset for a clean session. Your saved question history remains available in the left sidebar.</p>
          <p style="margin-top: 0.6rem; margin-bottom: 0;"><strong>How can I assist your logistics workflow today?</strong></p>
        </div>
      </div>
    `;
  }
  renderRandomSuggestions(5);
  if (userInput) userInput.focus();
  closeMobileHistory();
}

// Initial load of history
renderHistoryList();

// Initial random suggestions on load
renderRandomSuggestions(5);
