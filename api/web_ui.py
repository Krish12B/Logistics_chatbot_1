"""Embedded Web Chat UI & Landing Page for FleetHarbor Logistics Chatbot.
Provides an interactive in-browser chat interface, real-time Markdown rendering, and quick API navigation.
"""

LANDING_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FleetHarbor AI</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <!-- Marked.js for GitHub Flavored Markdown with offline fallback -->
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    :root {
      --primary: #0F172A;
      --primary-light: #1E293B;
      --accent-blue: #2563EB;
      --accent-blue-hover: #1D4ED8;
      --accent-cyan: #06B6D4;
      --accent-emerald: #10B981;
      --bg-page: #F8FAFC;
      --card-bg: #FFFFFF;
      --text-main: #0F172A;
      --text-secondary: #475569;
      --text-muted: #64748B;
      --border: #E2E8F0;
      --border-light: #F1F5F9;
      --card-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.05), 0 8px 10px -6px rgba(15, 23, 42, 0.03);
      --card-shadow-hover: 0 20px 35px -10px rgba(15, 23, 42, 0.08), 0 10px 15px -5px rgba(15, 23, 42, 0.04);
      --glass-border: rgba(255, 255, 255, 0.12);
      --gradient-brand: linear-gradient(135deg, #1E40AF 0%, #2563EB 55%, #0284C7 100%);
      --gradient-accent: linear-gradient(135deg, #0EA5E9 0%, #06B6D4 100%);
      --gradient-header: linear-gradient(135deg, #0B132B 0%, #1C2541 60%, #0F172A 100%);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: radial-gradient(circle at 10% 10%, rgba(37, 99, 235, 0.05) 0%, transparent 40%),
                  radial-gradient(circle at 90% 90%, rgba(6, 182, 212, 0.04) 0%, transparent 40%),
                  var(--bg-page);
      color: var(--text-main);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
    }

    /* Custom Scrollbars */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.35); border-radius: 9999px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(100, 116, 139, 0.6); }

    /* Header Navigation */
    header {
      background: var(--gradient-header);
      color: white;
      padding: 0.9rem 1.75rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 4px 20px rgba(11, 19, 43, 0.15);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      position: sticky;
      top: 0;
      z-index: 50;
      backdrop-filter: blur(12px);
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 0.9rem;
    }

    .brand-icon {
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.45rem;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .brand-text h1 {
      font-size: 1.25rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      background: linear-gradient(to right, #FFFFFF, #E2E8F0);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .header-links {
      display: flex;
      gap: 0.85rem;
      align-items: center;
    }

    .badge-online {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.28);
      color: #34D399;
      font-size: 0.75rem;
      padding: 0.35rem 0.75rem;
      border-radius: 9999px;
      font-weight: 600;
      letter-spacing: 0.01em;
    }

    .badge-dot {
      width: 7px;
      height: 7px;
      background: #10B981;
      border-radius: 50%;
      box-shadow: 0 0 8px #10B981;
      animation: pulse 2.2s infinite ease-in-out;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.85); }
    }

    .btn-nav {
      background: rgba(255, 255, 255, 0.08);
      color: #F8FAFC;
      border: 1px solid rgba(255, 255, 255, 0.16);
      text-decoration: none;
      padding: 0.4rem 0.95rem;
      border-radius: 10px;
      font-size: 0.8rem;
      font-weight: 600;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
    }

    .btn-nav:hover {
      background: rgba(255, 255, 255, 0.15);
      border-color: rgba(255, 255, 255, 0.3);
      color: #FFFFFF;
      transform: translateY(-1px);
    }

    /* Main Layout with History Sidebar */
    main {
      flex: 1;
      max-width: 1380px;
      width: 100%;
      margin: 1.25rem auto;
      padding: 0 1.25rem;
      display: flex;
      gap: 1.25rem;
      align-items: stretch;
      position: relative;
    }

    /* Question History Sidebar */
    .history-sidebar {
      width: 320px;
      flex: 0 0 320px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 24px;
      box-shadow: var(--card-shadow);
      display: flex;
      flex-direction: column;
      height: calc(100vh - 120px);
      min-height: 480px;
      overflow: hidden;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
    }

    .history-sidebar.collapsed {
      width: 0;
      flex: 0 0 0;
      opacity: 0;
      margin-right: -1.25rem;
      pointer-events: none;
      border: none;
    }

    .history-header {
      padding: 0.9rem 1.2rem;
      background: #FFFFFF;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.5rem;
    }

    .history-title {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: 700;
      font-size: 0.925rem;
      color: var(--text-main);
    }

    .history-title svg {
      color: var(--accent-blue);
    }

    .history-badge {
      background: #EEF2F6;
      color: var(--accent-blue);
      font-size: 0.725rem;
      font-weight: 700;
      padding: 0.15rem 0.55rem;
      border-radius: 9999px;
      border: 1px solid #DBEAFE;
    }

    .history-actions {
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }

    .btn-icon {
      background: #F8FAFC;
      border: 1px solid #E2E8F0;
      color: var(--text-secondary);
      width: 30px;
      height: 30px;
      border-radius: 8px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s;
    }

    .btn-icon:hover {
      background: #FFFFFF;
      color: var(--accent-blue);
      border-color: #93C5FD;
      box-shadow: 0 2px 6px rgba(37, 99, 235, 0.1);
    }

    .btn-icon.btn-danger:hover {
      background: #FEF2F2;
      color: #DC2626;
      border-color: #FCA5A5;
      box-shadow: 0 2px 6px rgba(220, 38, 38, 0.1);
    }

    .history-search {
      padding: 0.65rem 0.9rem;
      background: #F8FAFC;
      border-bottom: 1px solid var(--border);
      position: relative;
    }

    .history-search-input {
      width: 100%;
      padding: 0.45rem 0.75rem 0.45rem 2rem;
      background: #FFFFFF;
      border: 1px solid #CBD5E1;
      border-radius: 8px;
      font-size: 0.8rem;
      outline: none;
      font-family: inherit;
      color: var(--text-main);
      transition: all 0.2s;
    }

    .history-search-input:focus {
      border-color: var(--accent-blue);
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }

    .history-search-icon {
      position: absolute;
      left: 1.5rem;
      top: 50%;
      transform: translateY(-50%);
      color: #94A3B8;
      pointer-events: none;
    }

    .history-list {
      flex: 1;
      overflow-y: auto;
      padding: 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      background: #FAFCFF;
    }

    .history-item {
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 12px;
      padding: 0.7rem 0.85rem;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      position: relative;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }

    .history-item:hover {
      background: #F0F7FF;
      border-color: #93C5FD;
      box-shadow: 0 4px 10px rgba(37, 99, 235, 0.08);
      transform: translateY(-1px);
    }

    .history-item-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .history-time {
      font-size: 0.7rem;
      color: var(--text-muted);
      font-weight: 500;
    }

    .history-tools {
      display: flex;
      gap: 0.25rem;
      opacity: 0.35;
      transition: opacity 0.2s;
    }

    .history-item:hover .history-tools {
      opacity: 1;
    }

    .tool-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      width: 22px;
      height: 22px;
      border-radius: 4px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.15s;
    }

    .tool-btn:hover {
      background: #E2E8F0;
      color: var(--text-main);
    }

    .tool-btn.tool-del:hover {
      background: #FEE2E2;
      color: #DC2626;
    }

    .history-text {
      font-size: 0.825rem;
      color: var(--text-main);
      font-weight: 600;
      line-height: 1.4;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      word-break: break-word;
    }

    .history-item-footer {
      display: flex;
      align-items: center;
      gap: 0.35rem;
      margin-top: 0.1rem;
    }

    .history-tag {
      font-size: 0.675rem;
      color: #2563EB;
      background: #EFF6FF;
      padding: 0.1rem 0.45rem;
      border-radius: 9999px;
      font-weight: 600;
    }

    .history-empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 3.5rem 1.25rem;
      color: var(--text-muted);
      gap: 0.65rem;
      height: 100%;
    }

    .history-empty-icon {
      font-size: 2.2rem;
      opacity: 0.7;
    }

    .history-empty h4 {
      font-size: 0.9rem;
      font-weight: 700;
      color: var(--text-secondary);
    }

    .history-empty p {
      font-size: 0.775rem;
      line-height: 1.45;
      max-width: 210px;
    }

    .history-footer {
      padding: 0.65rem 1rem;
      background: #FFFFFF;
      border-top: 1px solid var(--border);
      font-size: 0.72rem;
      color: var(--text-muted);
      text-align: center;
      font-weight: 500;
    }

    /* Central Chat Card */
    .chat-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 24px;
      box-shadow: var(--card-shadow);
      display: flex;
      flex-direction: column;
      flex: 1;
      min-width: 0;
      height: calc(100vh - 120px);
      min-height: 480px;
      overflow: hidden;
      transition: box-shadow 0.3s;
    }

    /* Mobile drawer overlay */
    .history-backdrop {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.45);
      backdrop-filter: blur(2px);
      z-index: 90;
    }

    @media (max-width: 1024px) {
      .history-sidebar {
        position: fixed;
        left: -330px;
        top: 0;
        bottom: 0;
        height: 100vh;
        z-index: 100;
        border-radius: 0 20px 20px 0;
        box-shadow: 10px 0 25px rgba(0, 0, 0, 0.15);
      }
      .history-sidebar.mobile-open {
        left: 0;
      }
      .history-backdrop.active {
        display: block;
      }
    }

    /* Narrow screens: the header wraps to two rows, so leave room for it */
    @media (max-width: 720px) {
      .chat-card {
        height: calc(100vh - 140px);
      }
    }

    .chat-card:hover {
      box-shadow: var(--card-shadow-hover);
    }

    /* Chat Card Header */
    .chat-header {
      padding: 0.6rem 1.6rem;
      background: #FFFFFF;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .chat-header-title {
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }

    .chat-header-title h2 {
      font-size: 0.95rem;
      color: var(--text-main);
      font-weight: 700;
      letter-spacing: -0.01em;
    }

    /* Message Stream */
    .chat-messages {
      flex: 1;
      padding: 0.6rem 1rem;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
      background: linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 100%);
    }

    /* Message Bubbles */
    .msg {
      max-width: 86%;
      padding: 0.75rem 1.1rem;
      border-radius: 18px;
      line-height: 1.5;
      font-size: 0.8rem;
      word-break: break-word;
      animation: msgSlideUp 0.28s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
    }

    @keyframes msgSlideUp {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .msg.bot {
      align-self: flex-start;
      background: #FFFFFF;
      color: var(--text-main);
      border: 1px solid #E2E8F0;
      border-bottom-left-radius: 4px;
      box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
    }

    .msg.user {
      align-self: flex-end;
      background: var(--gradient-brand);
      color: white;
      border-bottom-right-radius: 4px;
      box-shadow: 0 6px 18px rgba(37, 99, 235, 0.22);
    }

    .msg.user p {
      margin: 0;
      color: white;
      font-weight: 500;
      letter-spacing: -0.01em;
    }

    /* Welcome Card Styling */
    .welcome-container {
      background: linear-gradient(135deg, rgba(239, 246, 255, 0.8) 0%, rgba(240, 253, 250, 0.7) 100%);
      border: 1px solid #DBEAFE;
      border-radius: 18px;
      padding: 1.35rem 1.6rem;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.05);
    }

    .welcome-header {
      display: flex;
      align-items: center;
      gap: 0.65rem;
      margin-bottom: 0.75rem;
    }

    .welcome-header h3 {
      font-size: 1.15rem;
      font-weight: 800;
      color: #1E3A8A;
      letter-spacing: -0.02em;
    }

    .welcome-pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      margin: 0.85rem 0;
    }

    .welcome-pill {
      font-size: 0.725rem;
      font-weight: 600;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      background: #FFFFFF;
      color: #1D4ED8;
      border: 1px solid #BFDBFE;
    }

    .welcome-list {
      list-style: none;
      margin: 0.6rem 0 0.8rem 0;
      display: flex;
      flex-direction: column;
      gap: 0.45rem;
    }

    .welcome-list li {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.875rem;
      color: #334155;
    }

    .welcome-list li::before {
      content: "✦";
      color: #2563EB;
      font-size: 0.75rem;
    }

    /* Markdown Elements in Bot Messages */
    .msg.bot h1 {
      font-size: 1rem;
      color: #0F172A;
      margin: 0 0 0.4rem 0;
      font-weight: 800;
      border-bottom: 2px solid #F1F5F9;
      padding-bottom: 0.35rem;
      letter-spacing: -0.01em;
    }

    .msg.bot h2 {
      font-size: 0.92rem;
      color: #1E40AF;
      margin: 0.5rem 0 0.3rem 0;
      font-weight: 700;
    }

    .msg.bot h3 {
      font-size: 0.86rem;
      color: #0F172A;
      margin: 0.5rem 0 0.25rem 0;
      font-weight: 700;
      letter-spacing: -0.01em;
    }

    .msg.bot p {
      margin-bottom: 0.45rem;
      line-height: 1.5;
      color: #334155;
    }

    .msg.bot ul, .msg.bot ol {
      margin: 0.25rem 0 0.4rem 1.1rem;
      font-size: 0.8rem;
      line-height: 1.5;
      color: #334155;
    }

    .msg.bot li {
      margin-bottom: 0.1rem;
    }

    .msg.bot strong {
      color: #0F172A;
      font-weight: 700;
    }

    .msg.bot code {
      background: #F1F5F9;
      color: #0F172A;
      padding: 0.1rem 0.35rem;
      border-radius: 6px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      border: 1px solid #E2E8F0;
    }

    /* Table Container & Aesthetics */
    .table-container {
      width: 100%;
      overflow-x: auto;
      margin: 0.6rem 0;
      border-radius: 14px;
      border: 1px solid #E2E8F0;
      box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
    }

    .msg.bot table, .markdown-table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      font-size: 0.76rem;
      line-height: 1.35;
      text-align: left;
      margin: 0.6rem 0;
      border-radius: 12px;
      border: 1px solid #E2E8F0;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
    }

    .msg.bot th, .markdown-table th {
      background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
      color: #F8FAFC;
      font-weight: 700;
      padding: 0.42rem 0.7rem;
      font-size: 0.7rem;
      letter-spacing: 0.03em;
      text-transform: uppercase;
      border-bottom: 1px solid #0F172A;
    }

    .msg.bot td, .markdown-table td {
      padding: 0.32rem 0.7rem;
      border-bottom: 1px solid #F1F5F9;
      color: #334155;
    }

    .msg.bot tr:last-child td, .markdown-table tr:last-child td {
      border-bottom: none;
    }

    .msg.bot tr:nth-child(even), .markdown-table tr:nth-child(even) {
      background: #F8FAFC;
    }

    .msg.bot tr:hover, .markdown-table tr:hover {
      background: #F1F5F9;
    }

    /* Sources Audit Box */
    .sources-box {
      margin-top: 0.5rem;
      padding-top: 0.45rem;
      border-top: 1px solid #F1F5F9;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }

    .sources-title {
      font-size: 0.66rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    .sources-list {
      display: flex;
      flex-wrap: wrap;
      gap: 0.45rem;
    }

    .source-tag {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      background: #F0F9FF;
      color: #0284C7;
      border: 1px solid #BAE6FD;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
      font-size: 0.68rem;
      font-weight: 600;
      transition: all 0.2s;
    }

    .source-tag:hover {
      background: #E0F2FE;
      border-color: #7DD3FC;
    }

    /* Typing Animation */
    .typing-indicator {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      color: var(--text-muted);
      font-size: 0.85rem;
      font-weight: 500;
    }

    .typing-dots {
      display: inline-flex;
      gap: 0.25rem;
    }

    .typing-dot {
      width: 7px;
      height: 7px;
      background: var(--accent-blue);
      border-radius: 50%;
      animation: bounce 1.4s infinite ease-in-out both;
    }

    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }

    @keyframes bounce {
      0%, 80%, 100% { transform: scale(0); opacity: 0.3; }
      40% { transform: scale(1); opacity: 1; }
    }

    /* Dynamic Suggestions Bar */
    .suggestions {
      padding: 0.5rem 1.4rem;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.4rem;
      background: #FFFFFF;
      border-top: 1px solid var(--border);
    }

    .suggestions-label {
      font-size: 0.66rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-right: 0.25rem;
    }

    .suggestion-chip {
      background: #F8FAFC;
      border: 1px solid #CBD5E1;
      color: #1E293B;
      padding: 0.3rem 0.65rem;
      border-radius: 9999px;
      font-size: 0.7rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
    }

    .suggestion-chip:hover {
      background: #FFFFFF;
      color: var(--accent-blue);
      border-color: #93C5FD;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12);
    }

    .suggestion-chip.suggestion-shuffle {
      background: #F1F5F9;
      color: var(--text-muted);
      border-style: dashed;
      border-color: #CBD5E1;
    }

    .suggestion-chip.suggestion-shuffle:hover {
      background: #E2E8F0;
      color: #0F172A;
      border-color: #94A3B8;
      border-style: solid;
      transform: translateY(-2px);
    }

    /* Chat Input Area (Dock Style) */
    .chat-input-area {
      padding: 0.55rem 1.4rem 0.7rem 1.4rem;
      background: #FFFFFF;
      border-top: 1px solid #F1F5F9;
      display: flex;
      gap: 0.75rem;
      align-items: center;
    }

    .chat-input-wrapper {
      flex: 1;
      position: relative;
      display: flex;
      align-items: center;
    }

    .chat-input {
      width: 100%;
      padding: 0.65rem 1.2rem;
      border: 1px solid #CBD5E1;
      border-radius: 9999px;
      font-size: 0.925rem;
      outline: none;
      font-family: inherit;
      color: var(--text-main);
      background: #F8FAFC;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .chat-input:focus {
      background: #FFFFFF;
      border-color: var(--accent-blue);
      box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
    }

    .chat-input::placeholder {
      color: #94A3B8;
      font-weight: 500;
    }

    .btn-send {
      background: var(--gradient-brand);
      color: white;
      border: none;
      padding: 0.85rem 1.85rem;
      border-radius: 9999px;
      font-weight: 700;
      font-size: 0.885rem;
      letter-spacing: -0.01em;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28);
      transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .btn-send:hover {
      box-shadow: 0 6px 20px rgba(37, 99, 235, 0.38);
      transform: translateY(-1px);
    }

    .btn-send:active {
      transform: scale(0.97);
    }

    .btn-send:disabled {
      background: #CBD5E1;
      box-shadow: none;
      cursor: not-allowed;
      transform: none;
    }

    /* Attach (+) button, attachment tray and attachment pills */
    .btn-attach {
      flex: 0 0 auto;
      width: 46px;
      height: 46px;
      border-radius: 9999px;
      border: 1px solid #CBD5E1;
      background: #F8FAFC;
      color: #1E293B;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .btn-attach:hover {
      background: #FFFFFF;
      color: var(--accent-blue);
      border-color: #93C5FD;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12);
    }

    .btn-attach:focus-visible {
      outline: none;
      border-color: var(--accent-blue);
      box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
    }

    .attach-tray {
      display: none;
      flex-wrap: wrap;
      gap: 0.5rem;
      max-height: 116px;
      overflow-y: auto;
      padding: 0.75rem 1.4rem 0 1.4rem;
      background: #FFFFFF;
    }

    .attach-tray.has-files {
      display: flex;
    }

    .attach-chip {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      max-width: 100%;
      padding: 0.3rem 0.3rem 0.3rem 0.85rem;
      background: #F8FAFC;
      border: 1px solid #CBD5E1;
      border-radius: 9999px;
      color: #1E293B;
      font-size: 0.775rem;
      font-weight: 600;
    }

    .attach-chip-name {
      max-width: 240px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .attach-chip-size {
      color: var(--text-muted);
      font-weight: 500;
      white-space: nowrap;
    }

    .attach-chip-remove {
      flex: 0 0 auto;
      width: 22px;
      height: 22px;
      border: none;
      border-radius: 9999px;
      background: #E2E8F0;
      color: #334155;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }

    .attach-chip-remove:hover {
      background: #CBD5E1;
      color: #0F172A;
    }

    .msg-attachments {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      margin-bottom: 0.55rem;
    }

    .msg-attach-pill {
      display: inline-block;
      max-width: 100%;
      padding: 0.25rem 0.7rem;
      border-radius: 9999px;
      background: rgba(255, 255, 255, 0.18);
      border: 1px solid rgba(255, 255, 255, 0.35);
      color: #FFFFFF;
      font-size: 0.75rem;
      font-weight: 600;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      vertical-align: middle;
    }

  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="brand-icon">🚢</div>
      <div class="brand-text">
        <h1>FleetHarbor AI</h1>
      </div>
    </div>
    <div class="header-links">
      <button type="button" id="toggleHistoryBtn" class="btn-nav" title="Toggle Question History Sidebar">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        <span>History</span>
        <span class="history-badge" id="navHistoryCount" style="padding: 0.1rem 0.45rem; font-size: 0.7rem; background: rgba(255, 255, 255, 0.2); color: #FFFFFF; border-color: rgba(255, 255, 255, 0.3);">0</span>
      </button>
      <span class="badge-online"><span class="badge-dot"></span> System Live</span>
      <a href="/docs" class="btn-nav" target="_blank">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/><path d="M6 6h10"/><path d="M6 10h10"/></svg>
        Swagger Docs (/docs)
      </a>
    </div>
  </header>

  <main>
    <div class="history-backdrop" id="historyBackdrop" onclick="closeMobileHistory()"></div>

    <!-- History Section Sidebar -->
    <aside class="history-sidebar" id="historySidebar" aria-label="Question History">
      <div class="history-header">
        <div class="history-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <span>Question History</span>
          <span class="history-badge" id="historyCountBadge">0</span>
        </div>
        <div class="history-actions">
          <button type="button" class="btn-icon" id="newChatBtn" title="Start New Chat Session" onclick="startNewChat()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          </button>
          <button type="button" class="btn-icon btn-danger" id="clearHistoryBtn" title="Clear All History" onclick="clearAllHistory()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      </div>

      <div class="history-search">
        <svg class="history-search-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input type="text" id="historySearchInput" class="history-search-input" placeholder="Search asked questions..." oninput="filterHistory(this.value)" />
      </div>

      <div class="history-list" id="historyList">
        <!-- Dynamically rendered by JavaScript -->
      </div>

      <div class="history-footer">
        <span>💡 Click any question to re-ask instantly</span>
      </div>
    </aside>

    <div class="chat-card">
      <div class="chat-header">
        <div class="chat-header-title">
          <h2>Live Assistant Dialogue</h2>
        </div>
      </div>
      
      <div class="chat-messages" id="chatMessages">
        <div class="msg bot">
          <div class="welcome-container">
            <div class="welcome-header">
              <span style="font-size: 1.5rem;">🚢</span>
              <h3>Welcome to FleetHarbor AI!</h3>
            </div>
            <p>Hello! I am your enterprise logistics operations assistant connected directly to real-time freight records, employee profiles, and our certified knowledge base.</p>
            
            <div class="welcome-pill-row">
              <span class="welcome-pill">GDP Cold-Chain Rules</span>
              <span class="welcome-pill">Customs Compliance</span>
            </div>

            <ul class="welcome-list">
              <li>Track shipments by ID (e.g. <code>SHP-10001</code> to <code>SHP-20000</code>) for routes, delays & ETAs.</li>
              <li>Look up logistics personnel (e.g. <code>EMP-20001</code>) for roles, certifications & dispatch contacts.</li>
              <li>Query cross-border customs regulations, commercial invoice standards, and GDP cold-chain manuals.</li>
            </ul>
            <p style="margin-top: 0.6rem; margin-bottom: 0;"><strong>How can I assist your logistics workflow today?</strong></p>
          </div>
        </div>
      </div>

      <div class="suggestions" id="suggestionsContainer"></div>

      <div class="attach-tray" id="attachTray" aria-live="polite"></div>

      <form class="chat-input-area" id="chatForm" onsubmit="handleSend(event); return false;">
        <button type="button" id="attachBtn" class="btn-attach" aria-label="Attach a file" title="Attach a file (.txt, .pdf, .docx, .csv)">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
        <div class="chat-input-wrapper">
          <input type="text" id="userInput" class="chat-input" placeholder="Ask a question or track shipment (e.g. 'Status of SHP-15000' or 'Look up EMP-20001')..." autocomplete="off" />
        </div>
        <button type="submit" id="sendBtn" class="btn-send">
          <span>Send</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
      </form>

      <input type="file" id="fileInput" accept=".txt,.pdf,.docx,.csv" multiple hidden />
    </div>
  </main>

  <script>
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
        .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
        .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>');
    }

    function fallbackRenderMarkdown(md) {
      if (!md) return '';
      let html = escapeHtml(md);

      // 1. Tables: lines starting and ending with |
      html = html.replace(/(?:^|\\n)((?:\\|[^\\r\\n]+\\|\\r?\\n?){2,})/g, function(match, tableBlock) {
        const lines = tableBlock.trim().split(/\\r?\\n/).map(l => l.trim());
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
        return '\\n' + tableHtml + '\\n';
      });

      // 2. Headings
      html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
      html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
      html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

      // 3. Lists
      html = html.replace(/(?:^|\\n)((?:- [^\\r\\n]+\\r?\\n?)+)/g, function(m, listBlock) {
        const items = listBlock.trim().split(/\\r?\\n/).map(l => l.replace(/^- /, '').trim());
        return '<ul>' + items.map(it => '<li>' + renderInline(it) + '</li>').join('') + '</ul>';
      });

      // 4. Inlines
      html = renderInline(html);

      // 5. Paragraphs
      const blocks = html.split(/\\n{2,}/);
      html = blocks.map(b => {
        b = b.trim();
        if (b.startsWith('<h') || b.startsWith('<ul') || b.startsWith('<ol') || b.startsWith('<div')) {
          return b;
        }
        return '<p>' + b.replace(/\\n/g, '<br>') + '</p>';
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
        s = s.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
        return s.replace(/\\n/g, '<br>');
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

        const isMereAttachmentNote = /^(here\\s+is\\s+(?:a\\s+)?new\\s+data|here\\s+is\\s+data|new\\s+data|attached|uploaded\\s+.*|here\\s+is\\s+the\\s+file|Uploaded\\s+.*)$/i.test(query);
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
            const lines = buffer.split(/\\r?\\n/);
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
        const shpMatch = item.query.match(/SHP-\\d+/i);
        const empMatch = item.query.match(/EMP-\\d+/i);
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
  </script>
</body>
</html>
"""
