const api = (path, params={})=>{
  const url = new URL(path, window.location.origin);
  Object.keys(params).forEach(k=>{ if(params[k]!==undefined) url.searchParams.append(k, params[k])});
  return fetch(url).then(r=>r.json());
}

function showToast(msg, type='info'){
  // small on-page ephemeral message
  const el = document.createElement('div');
  el.className = `toast-msg ${type==='error' ? 'toast-error' : 'toast-info'}`;
  el.innerText = msg;
  document.body.appendChild(el);
  requestAnimationFrame(()=>el.classList.add('visible'));
  setTimeout(()=>el.classList.remove('visible'),4200);
  setTimeout(()=>el.remove(),5000);
}

document.getElementById('btnForecast').addEventListener('click', async ()=>{
  const product = document.getElementById('productInput').value || 'clothing';
  showToast('Fetching forecast...');
  try{
    const res = await api('/api/forecast',{product});
    if(res.error) throw new Error(res.error);
    const labels = res.map(r=>r.ds);
    const data = res.map(r=>r.yhat);
    renderForecast(labels, data);
    document.getElementById('forecastRaw').innerText = JSON.stringify(res.slice(-5),null,2);
  }catch(e){ showToast('Forecast failed: '+e.message,'error') }
});

document.getElementById('btnPrice').addEventListener('click', async ()=>{
  const product = document.getElementById('productInput').value || 'clothing';
  showToast('Optimizing price...');
  try{
    const res = await api('/api/price',{product});
    if(res.error) throw new Error(res.error);
    document.getElementById('priceResult').innerText = `Current: ${res.current_price.toFixed(2)} → Optimized: ${res.optimized_price.toFixed(2)}`;
    document.getElementById('priceExplanation').innerText = '';
  }catch(e){ showToast('Price failed: '+e.message,'error') }
});

document.getElementById('btnRecommend').addEventListener('click', async ()=>{
  showToast('Fetching recommendations...');
  try{
    const res = await api('/api/recommend');
    const list = document.getElementById('recommendations'); list.innerHTML='';
    (res.recommendations||[]).forEach(p=>{
      const li = document.createElement('li'); li.className='list-group-item'; li.innerText = p; list.appendChild(li);
    });
  }catch(e){ showToast('Recommend failed: '+e.message,'error') }
});

document.getElementById('btnGraph').addEventListener('click', async ()=>{
  showToast('Loading graph...');
  const product = document.getElementById('productInput').value || 'clothing';
  try{
    const res = await api('/api/graph',{product});
    renderGraph(res.nodes || [], res.edges || []);
  }catch(e){ showToast('Graph failed: '+e.message,'error') }
});

document.getElementById('btnSocial').addEventListener('click', async ()=>{
  showToast('Loading social sentiment...');
  const product = document.getElementById('productInput').value || 'clothing';
  try{
    const res = await api('/api/social_series',{product});
    const series = res.series || [];
    const labels = series.map(s=>s.date);
    const vals = series.map(s=>s.sentiment);
    renderSocial(labels, vals);
  }catch(e){ showToast('Social failed: '+e.message,'error') }
});

document.getElementById('btnChat').addEventListener('click', async ()=>{
  const q = document.getElementById('chatInput').value || '';
  if(!q) return showToast('Type a question first');
  showToast('Asking Copilot...');
  try{
    const product = document.getElementById('productInput').value || 'clothing';
    const chatLog = document.getElementById('chatLog');
    // render user bubble
    const userBubble = document.createElement('div'); userBubble.className='chat-bubble chat-user'; userBubble.innerHTML = escapeHtml(q);
    saveChatMessage('user', q);
    chatLog.appendChild(userBubble);
    // render bot bubble with typing indicator
    const botBubbleWrap = document.createElement('div'); botBubbleWrap.style.display='flex'; botBubbleWrap.style.flexDirection='column';
    const botBubble = document.createElement('div'); botBubble.className='chat-bubble chat-bot';
    const typing = document.createElement('div'); typing.className='typing'; typing.innerHTML = '<div class="dot active"></div><div class="dot"></div><div class="dot"></div>';
    botBubble.appendChild(typing);
    botBubbleWrap.appendChild(botBubble);
    chatLog.appendChild(botBubbleWrap);
    saveChatMessage('bot', '...');
    chatLog.scrollTop = chatLog.scrollHeight;

    // Prepare content container (will replace typing on first chunk)
    const content = document.createElement('div'); content.innerHTML = '';
    try{
      const resp = await fetch(`/api/chat/stream?product=${encodeURIComponent(product)}&include_context=true`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({prompt:q})});
      if(!resp.ok){
        const txt = await resp.text();
        botBubble.removeChild(typing);
        content.innerText = txt; botBubble.appendChild(content); showFollowups(botBubbleWrap); return
      }
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      const chunks = [];
      let firstChunk = true;
      while(true){
        const {done, value} = await reader.read();
        if(done) break;
        const chunk = decoder.decode(value, {stream:true});
        // On first data chunk, remove typing indicator and show content
        if(firstChunk){
          botBubble.removeChild(typing);
          botBubble.appendChild(content);
          firstChunk = false;
        }
        // append safely with simple newline -> <br>
        content.innerHTML = content.innerHTML + nl2br(escapeHtml(chunk));
        chatLog.scrollTop = chatLog.scrollHeight;
        chunks.push(chunk);
      }
      // update persisted last bot message
      try{
        const key='ai_chat_history_v1';
        const existing = JSON.parse(localStorage.getItem(key) || '[]');
        // replace last bot placeholder with full text
        for(let i=existing.length-1;i>=0;i--){ if(existing[i].role==='bot'){ existing[i].text = existing[i].text==='...' ? chunks.join('') : existing[i].text + chunks.join(''); break } }
        localStorage.setItem(key, JSON.stringify(existing));
      }catch(e){console.warn('persist bot failed',e)}
      showFollowups(botBubbleWrap);
    }catch(e){ content.innerText += '\n\n[Error receiving stream: '+e.message+']'; }
  }catch(e){ showToast('Chat failed: '+e.message,'error') }
});

function escapeHtml(str){
  if(!str) return '';
  return str.replace(/[&<>"']/g, s=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;" }[s]));
}

function nl2br(str){
  if(!str) return '';
  return str.replace(/\n/g, '<br>');
}

function showFollowups(container){
  const box = document.createElement('div'); box.className='followups';
  const opts = ['Explain optimized price','Show forecast details','Recommend restock','How to improve ROI'];
  opts.forEach(o=>{
    const b = document.createElement('button'); b.className='followup-btn'; b.innerText = o;
    b.onclick = ()=>{ document.getElementById('chatInput').value = o; document.getElementById('btnChat').click(); };
    box.appendChild(b);
  });
  container.appendChild(box);
}

// Chart rendering helpers
let forecastChart=null, socialChart=null;
function renderForecast(labels,data){
  const ctx = document.getElementById('forecastChart').getContext('2d');
  if(forecastChart) forecastChart.destroy();
  forecastChart = new Chart(ctx,{type:'line',data:{labels, datasets:[{label:'Forecast',data, borderColor:'#0d6efd', backgroundColor:'rgba(13,110,253,0.08)', tension:0.25}]}, options:{plugins:{legend:{display:false}}}});
}
function renderSocial(labels,data){
  const ctx = document.getElementById('socialChart').getContext('2d');
  if(socialChart) socialChart.destroy();
  socialChart = new Chart(ctx,{type:'bar',data:{labels,datasets:[{label:'Sentiment',data, backgroundColor:'#6c757d'}]}, options:{plugins:{legend:{display:false}}}});
}

function renderGraph(nodes, edges){
  const container = document.getElementById('network');
  const visNodes = new vis.DataSet(nodes.map(n=>({id:n.id, label:n.label})));
  const visEdges = new vis.DataSet(edges.map(e=>({from:e.from, to:e.to, value:e.value})));
  const data = {nodes: visNodes, edges: visEdges};
  const options = {physics:{stabilization:true}, edges:{smooth:true}};
  new vis.Network(container, data, options);
}

// Quick initial fetch to show UI is connected
document.addEventListener('DOMContentLoaded', ()=>{
  showToast('Ready — connected to API');
  loadChatHistory();
});

function saveChatMessage(role, text){
  try{
    const key='ai_chat_history_v1';
    const existing = JSON.parse(localStorage.getItem(key) || '[]');
    existing.push({role, text, ts: Date.now()});
    localStorage.setItem(key, JSON.stringify(existing));
  }catch(e){console.warn('saveChatMessage failed',e)}
}

function loadChatHistory(){
  try{
    const key='ai_chat_history_v1';
    const arr = JSON.parse(localStorage.getItem(key) || '[]');
    const chatLog = document.getElementById('chatLog');
    chatLog.innerHTML = '';
    arr.forEach(m=>{
      const el = document.createElement('div'); el.className = 'chat-bubble '+(m.role==='user'?'chat-user':'chat-bot');
      el.innerText = m.text;
      const meta = document.createElement('div'); meta.className='chat-meta'; meta.innerText = new Date(m.ts).toLocaleString();
      const wrap = document.createElement('div'); wrap.style.display='flex'; wrap.style.flexDirection='column'; wrap.appendChild(el); wrap.appendChild(meta);
      chatLog.appendChild(wrap);
    });
    chatLog.scrollTop = chatLog.scrollHeight;
  }catch(e){console.warn('loadChatHistory failed',e)}
}
