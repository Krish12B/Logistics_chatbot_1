
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const sessionId = "web_session_" + Math.random().toString(36).substring(2, 9);

    function renderInline(str) {
      if (!str) return '';
      return str
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>');
    }

    function fallbackRenderMarkdown(md) {
      if (!md) return '';
      let html = md;

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

    function addMessage(text, isUser, sources = [], resType = null) {
      const msgDiv = document.createElement('div');
      msgDiv.className = 'msg ' + (isUser ? 'user' : 'bot');

      if (isUser) {
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

        if (sources && sources.length > 0 && !isApologyOrError && resType !== 'unavailable') {
          const srcDiv = document.createElement('div');
          srcDiv.className = 'sources-box';
          let tagsHtml = sources.map(s => '<span class="source-tag">🛡️ ' + s + '</span>').join('');
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
      if (!userInput) return;
      userInput.value = q;
      handleSend();
    }

    async function handleSend(e) {
      if (e) {
        if (e.preventDefault) e.preventDefault();
        if (e.stopPropagation) e.stopPropagation();
      }
      const query = userInput ? userInput.value.trim() : '';
      if (!query) return false;

      addMessage(query, true);
      if (userInput) userInput.value = '';
      if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.innerText = 'Analyzing...';
      }
      showLoadingIndicator();
      renderRandomSuggestions(5);

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
            const lines = buffer.split('
');
            buffer = lines.pop();

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

          contentDiv.innerHTML = safeRenderMarkdown(accumulatedText);

          const isApologyOrError = accumulatedText && (
            accumulatedText.includes('information is not available') ||
            accumulatedText.includes('not available in the FleetHarbor') ||
            accumulatedText.includes('temporarily unavailable') ||
            accumulatedText.includes('I apologize') ||
            accumulatedText.includes('Sorry, something unexpected')
          );

          if (finalSources && finalSources.length > 0 && !isApologyOrError && finalResType !== 'unavailable') {
            const srcDiv = document.createElement('div');
            srcDiv.className = 'sources-box';
            let tagsHtml = finalSources.map(s => '<span class="source-tag">🛡️ ' + s + '</span>').join('');
            srcDiv.innerHTML = '<div class="sources-title"><span>🔒</span> Verified Data Sources</div><div class="sources-list">' + tagsHtml + '</div>';
            msgDiv.appendChild(srcDiv);
          }
          chatMessages.scrollTop = chatMessages.scrollHeight;
        } else {
          // Synchronous fallback
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
            const errMsg = data.message || (data.data && data.data.message) || data.detail || "Server error encountered.";
            addMessage("⚠️ " + errMsg, false);
          }
        }
      } catch (err) {
        console.error("Fetch error:", err);
        removeLoadingIndicator();
        addMessage("⚠️ Error contacting assistant: " + err.message, false);
      } finally {
        if (sendBtn) {
          sendBtn.disabled = false;
          sendBtn.innerHTML = '<span>Send</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>';
        }
        if (userInput) userInput.focus();
      }
      return false;
    }

    // Initial random suggestions on load
    renderRandomSuggestions(5);
  