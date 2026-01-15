// ============================================
// Market Optimizer - Enhanced JavaScript
// Features: i18n, Dark Mode, Better UX, Tutorial
// ============================================

// === Global State ===
let currentLang = localStorage.getItem('preferred_language') || 'bn'; // Default to Bengali
let currentTheme = localStorage.getItem('preferred_theme') || 'light';
let translations = {};
let currentProduct = '';

// === API Helper ===
const api = (path, params = {}) => {
  const url = new URL(path, window.location.origin);
  Object.keys(params).forEach(k => {
    if (params[k] !== undefined) url.searchParams.append(k, params[k]);
  });
  return fetch(url).then(r => r.json());
};

// === Tutorial System ===
function showTutorial() {
  const overlay = document.getElementById('tutorialOverlay');
  if (overlay) {
    overlay.style.display = 'flex';
    localStorage.setItem('tutorial_shown', 'true');
  }
}

function closeTutorial() {
  const overlay = document.getElementById('tutorialOverlay');
  if (overlay) {
    overlay.style.display = 'none';
  }
}

// Auto-show tutorial for first-time users
function checkFirstVisit() {
  const hasSeenTutorial = localStorage.getItem('tutorial_shown');
  if (!hasSeenTutorial) {
    setTimeout(showTutorial, 1000); // Show after 1 second
  }
}

// === Product Selector ===
function getSelectedProduct() {
  const select = document.getElementById('productSelect');
  if (!select || !select.value) {
    showToast(
      currentLang === 'bn'
        ? 'প্রথমে একটি পণ্য নির্বাচন করুন'
        : 'Please select a product first',
      'error'
    );
    return null;
  }
  return select.value;
}

function setupProductSelector() {
  const select = document.getElementById('productSelect');
  if (select) {
    select.addEventListener('change', (e) => {
      currentProduct = e.target.value;
      if (currentProduct) {
        showToast(
          currentLang === 'bn'
            ? `"${e.target.selectedOptions[0].text}" নির্বাচন করা হয়েছে। এখন একটি বাটনে ক্লিক করুন।`
            : `"${e.target.selectedOptions[0].text}" selected. Click a button to continue.`,
          'info'
        );
      }
    });
  }
}

// === Example Questions ===
function askExample(question) {
  const input = document.getElementById('chatInput');
  if (input) {
    input.value = question;
    handleChat();
  }
}

// Make it available globally
window.askExample = askExample;
window.showTutorial = showTutorial;
window.closeTutorial = closeTutorial;

// === Internationalization (i18n) ===
async function loadTranslations() {
  try {
    const response = await fetch('/static/translations.json');
    translations = await response.json();
    applyTranslations();
  } catch (e) {
    console.error('Failed to load translations:', e);
  }
}

function t(key) {
  return translations[currentLang]?.[key] || translations['en']?.[key] || key;
}

function applyTranslations() {
  // Update all elements with data-i18n attribute
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    el.textContent = t(key);
  });

  // Update placeholders
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    el.placeholder = t(key);
  });

  // Update HTML lang attribute
  document.documentElement.lang = currentLang === 'bn' ? 'bn' : 'en';
}

function switchLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('preferred_language', lang);
  applyTranslations();

  // Update active button
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
  });

  showToast(lang === 'bn' ? 'ভাষা পরিবর্তন হয়েছে' : 'Language changed', 'info');
}

// === Theme Management ===
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('preferred_theme', theme);
  currentTheme = theme;

  const toggle = document.getElementById('themeToggle');
  if (toggle) {
    toggle.classList.toggle('active', theme === 'dark');
  }
}

function toggleTheme() {
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  applyTheme(newTheme);
  showToast(
    currentLang === 'bn'
      ? (newTheme === 'dark' ? 'ডার্ক মোড চালু' : 'লাইট মোড চালু')
      : (newTheme === 'dark' ? 'Dark mode enabled' : 'Light mode enabled'),
    'info'
  );
}

// === Toast Notifications ===
function showToast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast-msg ${type === 'error' ? 'toast-error' : 'toast-info'}`;
  el.innerText = msg;
  document.body.appendChild(el);

  requestAnimationFrame(() => el.classList.add('visible'));
  setTimeout(() => el.classList.remove('visible'), 4200);
  setTimeout(() => el.remove(), 5000);
}

// === Helper Functions ===
function showElement(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'block';
}

function hideElement(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'none';
}

function setLoading(id, isLoading) {
  const el = document.getElementById(id);
  if (!el) return;

  if (isLoading) {
    el.innerHTML = '<div class="loading-spinner"></div>';
  }
}


// === API Functions ===
document.getElementById('btnForecast')?.addEventListener('click', async () => {
  const product = getSelectedProduct();
  if (!product) return;
  showToast(t('toast_fetching_forecast'));

  try {
    const res = await api('/api/forecast', { product });
    if (res.error) throw new Error(res.error);

    // Format labels to show day name and date
    const labels = res.map(r => formatDateLabel(r.ds));
    const data = res.map(r => r.yhat);

    // Hide empty state, show chart
    hideElement('forecastEmpty');
    showElement('forecastChart');
    showElement('forecastSummary');

    renderForecast(labels, data);

    // Show summary
    const avgForecast = (data.reduce((a, b) => a + b, 0) / data.length).toFixed(2);
    document.getElementById('forecastText').innerText =
      currentLang === 'bn'
        ? `পরবর্তী ৩০ দিনের গড় পূর্বাভাস: ${avgForecast} ইউনিট`
        : `Average forecast for next 30 days: ${avgForecast} units`;

    showToast(currentLang === 'bn' ? 'পূর্বাভাস লোড হয়েছে!' : 'Forecast loaded!', 'info');
  } catch (e) {
    showToast(`${t('toast_forecast_failed')}: ${e.message}`, 'error');
  }
});

document.getElementById('btnPrice')?.addEventListener('click', async () => {
  const product = getSelectedProduct();
  if (!product) return;
  showToast(t('toast_optimizing_price'));

  try {
    const res = await api('/api/price', { product });
    if (res.error) throw new Error(res.error);

    // Hide empty state, show result
    hideElement('priceEmpty');
    showElement('priceResult');

    // Update price values
    document.getElementById('currentPrice').innerText = `৳${res.current_price.toFixed(2)}`;
    document.getElementById('optimizedPrice').innerText = `৳${res.optimized_price.toFixed(2)}`;

    // Calculate difference
    const diff = res.optimized_price - res.current_price;
    const diffPercent = ((diff / res.current_price) * 100).toFixed(1);

    document.getElementById('priceText').innerText =
      currentLang === 'bn'
        ? diff > 0
          ? `দাম ${diffPercent}% বৃদ্ধি করুন (৳${diff.toFixed(2)} বেশি) - এতে লাভ বাড়বে!`
          : `দাম ${Math.abs(diffPercent)}% কমান (৳${Math.abs(diff).toFixed(2)} কম) - বিক্রয় বাড়বে!`
        : diff > 0
          ? `Increase price by ${diffPercent}% (৳${diff.toFixed(2)} more) - Higher profit!`
          : `Decrease price by ${Math.abs(diffPercent)}% (৳${Math.abs(diff).toFixed(2)} less) - More sales!`;

    showToast(currentLang === 'bn' ? 'দাম অপটিমাইজ হয়েছে!' : 'Price optimized!', 'info');
  } catch (e) {
    showToast(`${t('toast_price_failed')}: ${e.message}`, 'error');
  }
});

document.getElementById('btnRecommend')?.addEventListener('click', async () => {
  showToast(t('toast_fetching_recommendations'));

  try {
    const res = await api('/api/recommend');
    const list = document.getElementById('recommendationsList');

    // Hide empty state, show list
    hideElement('recommendEmpty');
    showElement('recommendationsList');

    list.innerHTML = '';

    const recs = res.recommendations || [];
    if (recs.length === 0) {
      list.innerHTML = currentLang === 'bn'
        ? '<p class="text-muted">কোনো সুপারিশ পাওয়া যায়নি</p>'
        : '<p class="text-muted">No recommendations found</p>';
    } else {
      recs.forEach((p, idx) => {
        const div = document.createElement('div');
        div.className = 'recommendation-item';
        div.innerHTML = `
          <div class="rec-number">${idx + 1}</div>
          <div class="rec-content">
            <strong>${currentLang === 'bn' ? 'পণ্য' : 'Product'} ID:</strong> ${p}
          </div>
        `;
        list.appendChild(div);
      });
    }

    showToast(currentLang === 'bn' ? 'সুপারিশ লোড হয়েছে!' : 'Recommendations loaded!', 'info');
  } catch (e) {
    showToast(`${t('toast_recommend_failed')}: ${e.message}`, 'error');
  }
});

document.getElementById('btnGraph')?.addEventListener('click', async () => {
  const product = getSelectedProduct();
  if (!product) return;
  showToast(t('toast_loading_graph'));

  try {
    const res = await api('/api/graph', { product });
    renderGraph(res.nodes || [], res.edges || []);
  } catch (e) {
    showToast(`${t('toast_graph_failed')}: ${e.message}`, 'error');
  }
});

document.getElementById('btnSocial')?.addEventListener('click', async () => {
  const product = getSelectedProduct();
  if (!product) return;
  showToast(t('toast_loading_social'));

  try {
    const res = await api('/api/social_series', { product });
    const series = res.series || [];

    if (series.length === 0) {
      showToast(currentLang === 'bn' ? 'কোনো ডেটা পাওয়া যায়নি' : 'No data found', 'error');
      return;
    }

    // Hide empty state, show chart
    hideElement('socialEmpty');
    showElement('socialChart');

    // Expand the collapsible section
    const socialSection = document.getElementById('socialSection');
    if (socialSection && !socialSection.classList.contains('show')) {
      socialSection.classList.add('show');
    }

    const labels = series.map(s => s.date);
    const vals = series.map(s => s.sentiment);
    renderSocial(labels, vals);

    showToast(currentLang === 'bn' ? 'সোশ্যাল ডেটা লোড হয়েছে!' : 'Social data loaded!', 'info');
  } catch (e) {
    showToast(`${t('toast_social_failed')}: ${e.message}`, 'error');
  }
});

// === Chat Functions ===
async function handleChat() {
  const input = document.getElementById('chatInput');
  const q = input.value?.trim() || '';

  if (!q) return showToast(t('toast_type_question'));

  showToast(t('toast_asking_copilot'));

  try {
    const product = document.getElementById('productSelect')?.value || 'clothing';
    const chatLog = document.getElementById('chatLog');

    // Create user message bubble (WhatsApp style)
    const userWrapper = document.createElement('div');
    userWrapper.className = 'chat-bubble-wrapper chat-user';

    const userAvatar = document.createElement('div');
    userAvatar.className = 'chat-avatar chat-avatar-user';
    userAvatar.textContent = '👤';

    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble';

    const userContent = document.createElement('div');
    userContent.className = 'chat-message-content';
    userContent.innerHTML = escapeHtml(q);

    const userTime = document.createElement('span');
    userTime.className = 'chat-timestamp';
    const now = new Date();
    userTime.textContent = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });

    userBubble.appendChild(userContent);
    userBubble.appendChild(userTime);
    userWrapper.appendChild(userAvatar);
    userWrapper.appendChild(userBubble);

    saveChatMessage('user', q);
    chatLog.appendChild(userWrapper);

    // Create bot message bubble (WhatsApp style)
    const botWrapper = document.createElement('div');
    botWrapper.className = 'chat-bubble-wrapper chat-bot';

    const botAvatar = document.createElement('div');
    botAvatar.className = 'chat-avatar chat-avatar-bot';
    botAvatar.textContent = '🤖';

    const botBubble = document.createElement('div');
    botBubble.className = 'chat-bubble';

    const botContent = document.createElement('div');
    botContent.className = 'chat-message-content';

    const typing = document.createElement('div');
    typing.className = 'typing';
    typing.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
    botContent.appendChild(typing);
    botBubble.appendChild(botContent);

    botWrapper.appendChild(botAvatar);
    botWrapper.appendChild(botBubble);
    chatLog.appendChild(botWrapper);
    saveChatMessage('bot', '...');
    chatLog.scrollTop = chatLog.scrollHeight;

    input.value = '';

    try {
      const promptWithLang = currentLang === 'bn'
        ? `অনুগ্রহ করে বাংলায় উত্তর দিন: ${q}`
        : q;

      const resp = await fetch(
        `/api/chat/stream?product=${encodeURIComponent(product)}&include_context=true`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: promptWithLang })
        }
      );

      if (!resp.ok) {
        const txt = await resp.text();
        botContent.removeChild(typing);
        botContent.innerText = txt;

        // Add timestamp
        const botTime = document.createElement('span');
        botTime.className = 'chat-timestamp';
        botTime.textContent = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
        botBubble.appendChild(botTime);

        showFollowups(botWrapper);
        return;
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      const chunks = [];
      let firstChunk = true;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });

        if (firstChunk) {
          botContent.removeChild(typing);
          firstChunk = false;
        }

        botContent.innerHTML = nl2br(escapeHtml(chunks.join('') + chunk));
        chatLog.scrollTop = chatLog.scrollHeight;
        chunks.push(chunk);
      }

      // Add timestamp after message completes
      const botTime = document.createElement('span');
      botTime.className = 'chat-timestamp';
      botTime.textContent = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
      botBubble.appendChild(botTime);

      // Update persisted chat
      try {
        const key = 'ai_chat_history_v1';
        const existing = JSON.parse(localStorage.getItem(key) || '[]');
        for (let i = existing.length - 1; i >= 0; i--) {
          if (existing[i].role === 'bot') {
            existing[i].text = existing[i].text === '...' ? chunks.join('') : existing[i].text + chunks.join('');
            break;
          }
        }
        localStorage.setItem(key, JSON.stringify(existing));
      } catch (e) {
        console.warn('persist bot failed', e);
      }

      showFollowups(botWrapper);
    } catch (e) {
      botContent.innerText = `\n\n[${t('error')}: ${e.message}]`;
    }
  } catch (e) {
    showToast(`${t('toast_chat_failed')}: ${e.message}`, 'error');
  }
}

document.getElementById('btnChat')?.addEventListener('click', handleChat);
document.getElementById('btnChatTop')?.addEventListener('click', () => {
  const topInput = document.getElementById('chatInputTop');
  const mainInput = document.getElementById('chatInput');
  mainInput.value = topInput.value;
  topInput.value = '';
  handleChat();
});

document.getElementById('chatInput')?.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') handleChat();
});

// === Utility Functions ===
function formatDateLabel(dateString) {
  const date = new Date(dateString);
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const daysBengali = ['রবিবার', 'সোমবার', 'মঙ্গলবার', 'বুধবার', 'বৃহস্পতিবার', 'শুক্রবার', 'শনিবার'];
  const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const monthsBengali = ['জানুয়ারি', 'ফেব্রুয়ারি', 'মার্চ', 'এপ্রিল', 'মে', 'জুন', 'জুলাই', 'আগস্ট', 'সেপ্টেম্বর', 'অক্টোবর', 'নভেম্বর', 'ডিসেম্বর'];

  const dayName = currentLang === 'bn' ? daysBengali[date.getDay()] : days[date.getDay()];
  const day = date.getDate();
  const monthName = currentLang === 'bn' ? monthsBengali[date.getMonth()] : months[date.getMonth()];
  const year = date.getFullYear();

  return `${dayName} ${day} ${monthName} ${year}`;
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, s => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[s]));
}

function nl2br(str) {
  if (!str) return '';
  return str.replace(/\n/g, '<br>');
}

function showFollowups(container) {
  const box = document.createElement('div');
  box.className = 'followups';

  const opts = currentLang === 'bn'
    ? ['অপটিমাইজড দাম ব্যাখ্যা করুন', 'পূর্বাভাসের বিস্তারিত দেখান', 'পুনঃস্টক সুপারিশ করুন', 'কীভাবে ROI উন্নত করা যায়']
    : ['Explain optimized price', 'Show forecast details', 'Recommend restock', 'How to improve ROI'];

  opts.forEach(o => {
    const b = document.createElement('button');
    b.className = 'followup-btn';
    b.innerText = o;
    b.onclick = () => {
      document.getElementById('chatInput').value = o;
      handleChat();
    };
    box.appendChild(b);
  });

  container.appendChild(box);
}

// === Chart Rendering ===
let forecastChart = null, socialChart = null;

function renderForecast(labels, data) {
  const ctx = document.getElementById('forecastChart')?.getContext('2d');
  if (!ctx) return;

  if (forecastChart) forecastChart.destroy();

  forecastChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: t('card_forecast'),
        data,
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 3,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          padding: 12,
          titleFont: { size: 14, weight: 'bold' },
          bodyFont: { size: 13 }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.05)' }
        },
        x: {
          grid: { display: false },
          ticks: {
            maxRotation: 45,
            minRotation: 45,
            font: { size: 10 }
          }
        }
      }
    }
  });
}

function renderSocial(labels, data) {
  const ctx = document.getElementById('socialChart')?.getContext('2d');
  if (!ctx) return;

  if (socialChart) socialChart.destroy();

  socialChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: t('card_social'),
        data,
        backgroundColor: 'rgba(139, 92, 246, 0.7)',
        borderColor: '#8b5cf6',
        borderWidth: 2,
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          padding: 12
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.05)' }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

function renderGraph(nodes, edges) {
  const container = document.getElementById('network');
  if (!container) return;

  const visNodes = new vis.DataSet(nodes.map(n => ({
    id: n.id,
    label: n.label,
    color: {
      background: '#6366f1',
      border: '#4f46e5',
      highlight: { background: '#8b5cf6', border: '#7c3aed' }
    },
    font: { color: '#ffffff' }
  })));

  const visEdges = new vis.DataSet(edges.map(e => ({
    from: e.from,
    to: e.to,
    value: e.value,
    color: { color: '#cbd5e1' }
  })));

  const data = { nodes: visNodes, edges: visEdges };
  const options = {
    physics: { stabilization: true },
    edges: { smooth: true },
    interaction: { hover: true }
  };

  new vis.Network(container, data, options);
}

// === Chat History ===
function saveChatMessage(role, text) {
  try {
    const key = 'ai_chat_history_v1';
    const existing = JSON.parse(localStorage.getItem(key) || '[]');
    existing.push({ role, text, ts: Date.now() });
    localStorage.setItem(key, JSON.stringify(existing));
  } catch (e) {
    console.warn('saveChatMessage failed', e);
  }
}

function loadChatHistory() {
  try {
    const key = 'ai_chat_history_v1';
    const arr = JSON.parse(localStorage.getItem(key) || '[]');
    const chatLog = document.getElementById('chatLog');
    if (!chatLog) return;

    chatLog.innerHTML = '';

    arr.forEach(m => {
      const el = document.createElement('div');
      el.className = 'chat-bubble ' + (m.role === 'user' ? 'chat-user' : 'chat-bot');
      el.innerText = m.text;

      const meta = document.createElement('div');
      meta.className = 'chat-meta';
      meta.innerText = new Date(m.ts).toLocaleString();

      const wrap = document.createElement('div');
      wrap.style.display = 'flex';
      wrap.style.flexDirection = 'column';
      wrap.appendChild(el);
      wrap.appendChild(meta);

      chatLog.appendChild(wrap);
    });

    chatLog.scrollTop = chatLog.scrollHeight;
  } catch (e) {
    console.warn('loadChatHistory failed', e);
  }
}

// === Initialization ===
document.addEventListener('DOMContentLoaded', async () => {
  // Load translations
  await loadTranslations();

  // Apply saved theme
  applyTheme(currentTheme);

  // Apply saved language
  switchLanguage(currentLang);

  // Setup product selector
  setupProductSelector();

  // Load chat history
  loadChatHistory();

  // Setup event listeners
  document.getElementById('themeToggle')?.addEventListener('click', toggleTheme);

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const lang = btn.getAttribute('data-lang');
      switchLanguage(lang);
    });
  });

  // Setup help bubble
  const helpBubble = document.getElementById('helpBubble');
  if (helpBubble) {
    helpBubble.addEventListener('click', showTutorial);
  }

  // Check for first visit
  checkFirstVisit();

  // Show ready message
  showToast(t('toast_ready'), 'info');
});
// ==================== COPY THIS TO END OF main.js ====================
// Paste this at the very end of static/main.js file (after line 774)

document.getElementById('btnStock')?.addEventListener('click', async () => { showToast('স্টক তথ্য আনা হচ্ছে...'); try { const res = await api('/api/stock/alert'); if (res.error) throw new Error(res.error); let html = '<h6 class="mb-3">📦 স্টক সতর্কতা রিপোর্ট</h6>'; res.alerts.forEach(alert => { const statusBadge = alert.status === 'critical' ? 'bg-danger' : alert.status === 'warning' ? 'bg-warning' : 'bg-success'; const statusText = alert.status === 'critical' ? 'জরুরি' : alert.status === 'warning' ? 'সতর্কতা' : 'ভালো'; html += `<div class="alert alert-${alert.status === 'ok' ? 'success' : 'warning'} mb-3"><div class="d-flex justify-content-between align-items-center"><strong>${alert.product}</strong><span class="badge ${statusBadge}">${statusText}</span></div><div class="mt-2"><small>দৈনিক গড় বিক্রয়: ${alert.daily_avg_sales} ইউনিট</small><br><small>স্টক শেষ হবে: ${alert.days_until_stockout} দিনে</small><br><strong>💡 ${alert.recommendation}</strong></div></div>`; }); document.getElementById('chatLog').innerHTML = html; showToast('স্টক রিপোর্ট তৈরি হয়েছে!', 'success'); } catch (e) { showToast(`ত্রুটি: ${e.message}`, 'error'); } });

document.getElementById('btnTrends')?.addEventListener('click', async () => { showToast('বিক্রয় প্রবণতা বিশ্লেষণ হচ্ছে...'); try { const res = await api('/api/trends/analysis'); if (res.error) throw new Error(res.error); let html = `<h6 class="mb-3">📈 বিক্রয় প্রবণতা বিশ্লেষণ</h6><div class="card mb-3"><div class="card-body"><h5 class="text-primary">🏆 সেরা বিক্রয় দিন: ${res.best_day.name}</h5><p>আয়: ৳${res.best_day.revenue.toLocaleString()}</p></div></div><div class="card mb-3"><div class="card-body"><h6>সাপ্তাহিক প্যাটার্ন</h6><ul class="list-group">`; res.weekly_pattern.forEach(day => { html += `<li class="list-group-item d-flex justify-content-between"><span>${day.day}</span><strong>৳${day.revenue.toLocaleString()}</strong></li>`; }); html += `</ul></div></div><div class="alert alert-info"><strong>💡 পরামর্শ:</strong> ${res.recommendation}</div>`; document.getElementById('chatLog').innerHTML = html; showToast('প্রবণতা বিশ্লেষণ সম্পন্ন!', 'success'); } catch (e) { showToast(`ত্রুটি: ${e.message}`, 'error'); } });

document.getElementById('btnCustomer')?.addEventListener('click', async () => { showToast('ক্রেতা তথ্য বিশ্লেষণ হচ্ছে...'); try { const res = await api('/api/customer/insights'); if (res.error) throw new Error(res.error); let html = `<h6 class="mb-3">👥 ক্রেতা বিশ্লেষণ</h6><div class="row mb-3"><div class="col-md-6"><div class="card"><div class="card-body text-center"><h3 class="text-primary">${res.total_customers}</h3><p class="text-muted">মোট ক্রেতা</p></div></div></div><div class="col-md-6"><div class="card"><div class="card-body text-center"><h3 class="text-success">৳${res.avg_ltv.toLocaleString()}</h3><p class="text-muted">গড় LTV</p></div></div></div></div><h6>🏆 সেরা ৫ ক্রেতা</h6><ul class="list-group mb-3">`; res.top_customers.forEach((cust, idx) => { html += `<li class="list-group-item d-flex justify-content-between"><span>#${idx + 1} - ক্রেতা ${cust.customer_id}</span><div><strong>৳${cust.total_spent.toLocaleString()}</strong><small class="text-muted">(${cust.orders} অর্ডার)</small></div></li>`; }); html += `</ul><div class="alert alert-warning"><strong>⚠️ ঝুঁকি:</strong> ${res.at_risk_customers} জন ক্রেতা নিষ্ক্রিয়</div><div class="alert alert-info"><strong>💡 ${res.recommendation}</strong></div>`; document.getElementById('chatLog').innerHTML = html; showToast('ক্রেতা রিপোর্ট তৈরি!', 'success'); } catch (e) { showToast(`ত্রুটি: ${e.message}`, 'error'); } });

document.getElementById('btnProfit')?.addEventListener('click', async () => { showToast('লাভ হিসাব করা হচ্ছে...'); try { const res = await api('/api/profit/analysis'); if (res.error) throw new Error(res.error); let html = `<h6 class="mb-3">💵 লাভ বিশ্লেষণ</h6><div class="row mb-3"><div class="col-md-6"><div class="card bg-success text-white"><div class="card-body text-center"><h3>৳${res.total_profit.toLocaleString()}</h3><p>মোট লাভ</p></div></div></div><div class="col-md-6"><div class="card bg-info text-white"><div class="card-body text-center"><h3>${res.profit_margin.toFixed(1)}%</h3><p>লাভের হার</p></div></div></div></div><h6>🏆 সবচেয়ে লাভজনক পণ্য</h6><ul class="list-group mb-3">`; res.top_profitable.forEach((prod, idx) => { html += `<li class="list-group-item"><div class="d-flex justify-content-between"><strong>#${idx + 1} ${prod.product}</strong><span class="badge bg-success">${prod.margin.toFixed(1)}% মার্জিন</span></div><small>লাভ: ৳${prod.profit.toLocaleString()}</small></li>`; }); html += `</ul><div class="alert alert-success"><strong>💡 ${res.recommendation}</strong></div>`; document.getElementById('chatLog').innerHTML = html; showToast('লাভ রিপোর্ট প্রস্তুত!', 'success'); } catch (e) { showToast(`ত্রুটি: ${e.message}`, 'error'); } });

document.getElementById('btnSeasonal')?.addEventListener('click', async () => { showToast('মৌসুমী পূর্বাভাস করা হচ্ছে...'); try { const res = await api('/api/seasonal/predictor'); if (res.error) throw new Error(res.error); let html = `<h6 class="mb-3">🌟 মৌসুমী পূর্বাভাস</h6><div class="alert alert-primary"><h5>🎯 ${res.upcoming_season}</h5></div><div class="card mb-3"><div class="card-body"><h6>পিক মাস: ${res.peak_month.name}</h6><p>আয়: ৳${res.peak_month.revenue.toLocaleString()}</p></div></div><div class="row"><div class="col-md-6"><div class="card"><div class="card-header">ঈদ/রমজান জনপ্রিয়</div><ul class="list-group list-group-flush">`; res.eid_top_products.forEach(prod => { html += `<li class="list-group-item">${prod.product}</li>`; }); html += `</ul></div></div><div class="col-md-6"><div class="card"><div class="card-header">শীতকালীন জনপ্রিয়</div><ul class="list-group list-group-flush">`; res.winter_top_products.forEach(prod => { html += `<li class="list-group-item">${prod.product}</li>`; }); html += `</ul></div></div></div>`; document.getElementById('chatLog').innerHTML = html; showToast('মৌসুমী রিপোর্ট সম্পন্ন!', 'success'); } catch (e) { showToast(`ত্রুটি: ${e.message}`, 'error'); } });

document.getElementById('btnMarketing')?.addEventListener('click', async () => { showToast('মার্কেটিং পরিকল্পনা তৈরি হচ্ছে...'); try { const res = await api('/api/marketing/planner'); if (res.error) throw new Error(res.error); let html = `<h6 class="mb-3">🎯 মার্কেটিং পরিকল্পনা</h6><div class="alert alert-success"><h5>📅 সেরা ক্যাম্পেইন দিন: ${res.best_campaign_day}</h5></div><div class="card mb-3"><div class="card-header bg-warning">⚠️ বিক্রয় কমছে যেসব পণ্যে</div><ul class="list-group list-group-flush">`; res.declining_products.forEach(prod => { html += `<li class="list-group-item d-flex justify-content-between"><span>${prod.product}</span><span class="badge bg-danger">${prod.decline.toFixed(1)}% কমেছে</span></li>`; }); html += `</ul></div><div class="card mb-3"><div class="card-body"><h6>💰 প্রস্তাবিত ডিসকাউন্ট</h6><p><strong>${res.recommended_discount}</strong> - ${res.discount_recommendations.join(', ')}</p></div></div><div class="alert alert-info"><strong>💡 ${res.recommendation}</strong></div>`; document.getElementById('chatLog').innerHTML = html; showToast('মার্কেটিং পরিকল্পনা প্রস্তুত!', 'success'); } catch (e) { showToast(`ত্রুটি: ${e.message}`, 'error'); } });
