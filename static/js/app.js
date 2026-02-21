// ===== GLOBALS =====
let currentSessionId = null;
let cameraStream = null;
const audioPlayer = document.getElementById('audioPlayer');
let currentlyPlaying = null;

const EMOTION_EMOJIS = {
    happy: '😊', sad: '😢', angry: '😤', fear: '😰',
    surprise: '😲', disgust: '🤢', neutral: '😐'
};

const EMOTION_COLORS = {
    happy: '#FFD93D', sad: '#6C9BCF', angry: '#FF6B6B', fear: '#A78BFA',
    surprise: '#F472B6', disgust: '#6EE7B7', neutral: '#94A3B8'
};

// ===== PAGE ROUTING =====
function showPage(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.getElementById('page-' + page).classList.add('active');
    document.querySelector(`[data-page="${page}"]`)?.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });

    if (page === 'history') loadHistory();
    if (page === 'detect') resetDetection();
    if (page !== 'detect' && cameraStream) stopCamera();
}

// ===== NAVIGATION =====
window.addEventListener('scroll', () => {
    document.getElementById('navbar').classList.toggle('scrolled', window.scrollY > 40);
});

function toggleMobile() {
    document.querySelector('.nav-links').classList.toggle('open');
}

document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
        document.querySelector('.nav-links').classList.remove('open');
    });
});

// ===== API HELPER =====
async function api(url, method = 'GET', body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    try {
        const res = await fetch(url, opts);
        return await res.json();
    } catch (e) {
        console.error('API Error:', e);
        toast('Connection error. Please try again.', 'error');
        return null;
    }
}

// ===== TOAST =====
function toast(msg, type = 'success') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'toast show ' + type;
    setTimeout(() => t.className = 'toast', 3500);
}

// ===== DETECTION MODES =====
function selectMode(mode) {
    document.getElementById('modeSelect').style.display = 'none';
    if (mode === 'text') {
        document.getElementById('textInput').style.display = 'block';
        document.getElementById('faceInput').style.display = 'none';
        document.getElementById('emotionText').focus();
    } else {
        document.getElementById('textInput').style.display = 'none';
        document.getElementById('faceInput').style.display = 'block';
        startCamera();
    }
}

function showModeSelect() {
    document.getElementById('modeSelect').style.display = 'block';
    document.getElementById('textInput').style.display = 'none';
    document.getElementById('faceInput').style.display = 'none';
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('resultsPanel').style.display = 'none';
    stopCamera();
}

function resetDetection() {
    showModeSelect();
    setAmbientMood('');
}

// ===== TEXT ANALYSIS =====
const emotionText = document.getElementById('emotionText');
if (emotionText) {
    emotionText.addEventListener('input', function () {
        document.getElementById('charCount').textContent = this.value.length;
    });
}

function setQuickMood(text) {
    document.getElementById('emotionText').value = text;
    document.getElementById('charCount').textContent = text.length;
}

async function analyzeText() {
    const text = document.getElementById('emotionText').value.trim();
    if (!text) {
        toast('Please write something first', 'error');
        return;
    }

    const btn = document.getElementById('analyzeTextBtn');
    btn.disabled = true;

    document.getElementById('textInput').style.display = 'none';
    document.getElementById('loadingState').style.display = 'flex';

    const result = await api('/api/analyze/text', 'POST', { text });

    setTimeout(() => {
        document.getElementById('loadingState').style.display = 'none';
        btn.disabled = false;
        if (result && !result.error) {
            showResults(result);
        } else {
            showModeSelect();
            toast(result?.error || 'Analysis failed', 'error');
        }
    }, 1500);
}

// ===== CAMERA =====
async function startCamera() {
    const status = document.getElementById('cameraStatus');
    const captureBtn = document.getElementById('captureBtn');
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } }
        });
        document.getElementById('cameraFeed').srcObject = cameraStream;
        status.innerHTML = '<span class="material-icons-outlined">videocam</span> Camera active — smile!';
        captureBtn.disabled = false;
    } catch (e) {
        status.innerHTML = '<span class="material-icons-outlined">videocam_off</span> Camera not available';
        console.error('Camera error:', e);
        toast('Could not access camera. Please check permissions.', 'error');
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(t => t.stop());
        cameraStream = null;
    }
}

async function capturePhoto() {
    const video = document.getElementById('cameraFeed');
    const canvas = document.getElementById('captureCanvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0);
    const imageData = canvas.toDataURL('image/jpeg', 0.8);

    stopCamera();
    document.getElementById('faceInput').style.display = 'none';
    document.getElementById('loadingState').style.display = 'flex';

    const result = await api('/api/analyze/face', 'POST', { image: imageData });

    setTimeout(() => {
        document.getElementById('loadingState').style.display = 'none';
        if (result && !result.error) {
            showResults(result);
        } else {
            showModeSelect();
            toast(result?.error || 'Analysis failed', 'error');
        }
    }, 2000);
}

// ===== RESULTS =====
function showResults(result) {
    currentSessionId = result.session_id;
    const emotion = result.emotion;

    setAmbientMood(emotion);

    document.getElementById('resultEmoji').textContent = EMOTION_EMOJIS[emotion] || '🎵';
    document.getElementById('resultEmotion').textContent = emotion;
    document.getElementById('resultMood').textContent = result.mood;

    const confPercent = Math.round(result.confidence * 100);
    document.getElementById('confidenceFill').style.width = confPercent + '%';
    document.getElementById('confidenceValue').textContent = confPercent + '%';

    const emotionColor = EMOTION_COLORS[emotion] || '#C084FC';
    document.getElementById('emotionResultCard').style.borderLeftColor = emotionColor;
    document.getElementById('emotionResultCard').style.borderLeft = `4px solid ${emotionColor}`;

    const tracks = result.tracks || [];
    document.getElementById('tracksCount').textContent = tracks.length + ' tracks';

    document.getElementById('tracksGrid').innerHTML = tracks.map((t, i) => `
        <div class="track-card" onclick="${t.preview ? `playPreview('${t.preview}', ${i})` : `window.open('${t.url}','_blank')`}">
            <div class="track-art">
                ${t.image ? `<img src="${t.image}" alt="${t.name}" loading="lazy">` : `<div style="width:100%;height:100%;background:var(--surface-3);display:flex;align-items:center;justify-content:center"><span class="material-icons-outlined" style="color:var(--text-3)">music_note</span></div>`}
                <div class="play-overlay">
                    <span class="material-icons-outlined">${t.preview ? 'play_arrow' : 'open_in_new'}</span>
                </div>
            </div>
            <div class="track-info">
                <h4>${escapeHtml(t.name)}</h4>
                <p>${escapeHtml(t.artist)}</p>
            </div>
            ${t.url ? `<a href="${t.url}" target="_blank" class="track-link" onclick="event.stopPropagation()"><span class="material-icons-outlined">open_in_new</span></a>` : ''}
        </div>
    `).join('');

    document.getElementById('feedbackBtns').style.display = 'flex';
    document.getElementById('resultsPanel').style.display = 'block';
}

function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}

function setAmbientMood(emotion) {
    const bg = document.getElementById('ambientBg');
    bg.className = 'ambient-bg';
    if (emotion) bg.classList.add('mood-' + emotion);
}

// ===== AUDIO =====
function playPreview(url, index) {
    if (currentlyPlaying === index) {
        audioPlayer.pause();
        currentlyPlaying = null;
        return;
    }
    audioPlayer.src = url;
    audioPlayer.volume = 0.5;
    audioPlayer.play().catch(() => {});
    currentlyPlaying = index;
}

// ===== FEEDBACK =====
async function sendFeedback(rating) {
    if (!currentSessionId) return;
    await api('/api/feedback', 'POST', { session_id: currentSessionId, rating });
    document.getElementById('feedbackBtns').innerHTML = '<span style="color:var(--accent-4)">Thanks for your feedback! 🎵</span>';
    toast('Feedback recorded', 'success');
}

// ===== HISTORY =====
async function loadHistory() {
    const [stats, history] = await Promise.all([api('/api/stats'), api('/api/history')]);

    if (stats) {
        document.getElementById('statsCards').innerHTML = `
            <div class="stat-box"><strong>${stats.total_sessions}</strong><span>Total Sessions</span></div>
            <div class="stat-box"><strong>${Math.round(stats.avg_confidence * 100)}%</strong><span>Avg Confidence</span></div>
            <div class="stat-box"><strong>${stats.by_emotion?.[0]?.detected_emotion || '—'}</strong><span>Top Emotion</span></div>
        `;
    }

    if (history && history.length > 0) {
        document.getElementById('historyList').innerHTML = history.map(h => {
            const dt = new Date(h.created_at);
            const timeStr = dt.toLocaleDateString() + ' ' + dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            return `
                <div class="history-item">
                    <div class="hi-emoji">${EMOTION_EMOJIS[h.detected_emotion] || '🎵'}</div>
                    <div class="hi-info">
                        <h4>${h.detected_emotion}</h4>
                        <p>${h.mood} • Confidence: ${Math.round((h.confidence || 0) * 100)}%${h.input_text ? ' • "' + escapeHtml(h.input_text.substring(0, 60)) + (h.input_text.length > 60 ? '...' : '') + '"' : ''}</p>
                    </div>
                    <div class="hi-meta">
                        <div class="hi-badge ${h.input_type === 'text' ? 'hi-badge-text' : 'hi-badge-face'}">${h.input_type === 'text' ? '✏️ Text' : '📸 Face'}</div>
                        <div class="hi-time">${timeStr}</div>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        document.getElementById('historyList').innerHTML = `
            <div style="text-align:center;padding:60px 20px;color:var(--text-3)">
                <span class="material-icons-outlined" style="font-size:48px;display:block;margin-bottom:12px">history</span>
                <p>No sessions yet. Start by detecting your emotions!</p>
            </div>
        `;
    }
}

// ===== AUTH =====
function checkAuth() {
    api('/api/auth/status').then(data => {
        if (data?.logged_in) {
            document.getElementById('authSection').innerHTML = `
                <div class="auth-user">
                    <strong>${escapeHtml(data.username)}</strong>
                    <button class="auth-btn" onclick="handleLogout()">Logout</button>
                </div>`;
        } else {
            document.getElementById('authSection').innerHTML = `
                <button class="auth-btn" onclick="openModal('authModal')">Login</button>`;
        }
    });
}

function openModal(id) { document.getElementById(id).classList.add('active'); }
function closeModal(id) { document.getElementById(id).classList.remove('active'); }

function switchAuthTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.auth-tab:${tab === 'login' ? 'first-child' : 'last-child'}`).classList.add('active');
    document.getElementById('loginForm').style.display = tab === 'login' ? 'block' : 'none';
    document.getElementById('registerForm').style.display = tab === 'register' ? 'block' : 'none';
}

async function handleLogin(e) {
    e.preventDefault();
    const res = await api('/api/auth/login', 'POST', {
        email: document.getElementById('loginEmail').value,
        password: document.getElementById('loginPassword').value,
    });
    if (res?.success) {
        closeModal('authModal');
        checkAuth();
        toast('Welcome back!', 'success');
    } else {
        toast(res?.message || 'Login failed', 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const res = await api('/api/auth/register', 'POST', {
        username: document.getElementById('regUsername').value,
        email: document.getElementById('regEmail').value,
        password: document.getElementById('regPassword').value,
    });
    if (res?.success) {
        closeModal('authModal');
        checkAuth();
        toast('Account created! Welcome to Rooha.', 'success');
    } else {
        toast(res?.message || 'Registration failed', 'error');
    }
}

async function handleLogout() {
    await api('/api/auth/logout', 'POST');
    checkAuth();
    toast('Logged out', 'info');
}

// Close modal on backdrop click
document.querySelectorAll('.modal-overlay').forEach(m => {
    m.addEventListener('click', e => { if (e.target === m) m.classList.remove('active'); });
});

// ===== INIT =====
checkAuth();
