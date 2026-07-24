// =============================================
//  TriviaVerse Core Application Script
// =============================================

document.addEventListener('DOMContentLoaded', () => {
    // ========== SIDEBAR TOGGLE ==========
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');

    if (sidebarToggle && sidebar) {
        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true') {
            sidebar.classList.add('collapsed');
        }

        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
    }

    // ========== MOBILE SIDEBAR TOGGLE ==========
    const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
    if (mobileSidebarToggle && sidebar) {
        mobileSidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });

        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                if (!sidebar.contains(e.target) && e.target !== mobileSidebarToggle) {
                    sidebar.classList.remove('open');
                }
            }
        });
    }

    window.addEventListener('resize', () => {
        if (window.innerWidth > 768 && sidebar) {
            sidebar.classList.remove('open');
        }
    });

    // ========== USER DROPDOWN ==========
    window.toggleDropdown = () => {
        const dropdown = document.getElementById('userDropdown');
        if (dropdown) dropdown.classList.toggle('show');
    };

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu').forEach(d => d.classList.remove('show'));
        }
    });

    // ========== FLASH MESSAGES → TOAST ==========
    document.querySelectorAll('.flash').forEach(el => {
        const category = el.classList.contains('flash-success') ? 'success' :
            el.classList.contains('flash-error') ? 'error' :
                el.classList.contains('flash-warning') ? 'warning' : 'info';
        if (typeof showToast === 'function') {
            showToast(el.textContent.trim(), category);
        }
        el.remove();
    });

    // ========== SEARCH INPUT ==========
    const searchInput = document.querySelector('.navbar-search input');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = searchInput.value.trim();
                if (query) {
                    window.location.href = `/search?q=${encodeURIComponent(query)}`;
                }
            }
        });
    }

    // ========== THEME ==========
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    }
});

// ==================================
//  Global Utility Functions
// ==================================

window.getCSRFToken = () => {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 'csrf_token'.length + 1) === ('csrf_token' + '=')) {
                cookieValue = decodeURIComponent(cookie.substring('csrf_token'.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

window.copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        const input = document.createElement('textarea');
        input.value = text;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
        showToast('Copied!', 'success');
    });
};

window.showToast = (message, type = 'info') => {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.setAttribute('role', 'alert');
    document.body.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.transform = 'translateX(0)';
        toast.style.opacity = '1';
    });

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
};

window.apiFetch = async (url, options = {}) => {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    if (options.method && ['POST', 'PUT', 'DELETE'].includes(options.method.toUpperCase())) {
        headers['X-CSRFToken'] = getCSRFToken();
    }
    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Request failed' }));
        throw new Error(error.message || `HTTP ${response.status}`);
    }
    return response.json();
};

window.toggleTheme = function () {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
};

// ==================================
//  Toast CSS
// ==================================
const style = document.createElement('style');
style.textContent = `
.toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    padding: 14px 28px;
    border-radius: 14px;
    color: white;
    font-weight: 600;
    font-size: 0.95rem;
    z-index: 9999;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    transform: translateX(120%);
    opacity: 0;
    transition: transform 0.3s ease, opacity 0.3s ease;
    max-width: 380px;
    backdrop-filter: blur(12px);
}
.toast-success { background: linear-gradient(135deg, #22c55e, #16a34a); }
.toast-error   { background: linear-gradient(135deg, #ef4444, #dc2626); }
.toast-warning { background: linear-gradient(135deg, #f59e0b, #d97706); }
.toast-info    { background: linear-gradient(135deg, #3b82f6, #2563eb); }
`;
document.head.appendChild(style);

// ==================================
//  Mobile Sidebar
// ==================================
const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
const sidebar = document.getElementById('sidebar');
const overlay = document.createElement('div');
overlay.className = 'sidebar-overlay';
document.body.appendChild(overlay);

if (mobileSidebarToggle && sidebar) {
    mobileSidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('active');
    });
    overlay.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
    });
}

window.addEventListener('resize', () => {
    if (window.innerWidth > 768 && sidebar) {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
    }
});

function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ==================================
//  Mini Chat
// ==================================
let miniChatUser = null;

window.openMiniChat = function(userId, username) {
    miniChatUser = {id: userId, name: username};
    const titleEl = document.getElementById('miniChatTitle');
    if (titleEl) titleEl.textContent = '💬 ' + username;
    const chatEl = document.getElementById('miniChat');
    if (chatEl) chatEl.classList.remove('hidden');
    const msgEl = document.getElementById('miniChatMessages');
    if (msgEl) msgEl.innerHTML = '';
};

window.closeMiniChat = function() {
    const chatEl = document.getElementById('miniChat');
    if (chatEl) chatEl.classList.add('hidden');
    miniChatUser = null;
};

window.toggleMiniChat = function() {
    const chatEl = document.getElementById('miniChat');
    if (chatEl) chatEl.classList.toggle('hidden');
};

window.sendMiniChat = function() {
    const input = document.getElementById('miniChatInput');
    if (!input) return;
    const msg = input.value.trim();
    if (!msg || !miniChatUser) return;
    // Use the global socket if available
    if (typeof socket !== 'undefined' && socket) {
        socket.emit('direct_message', {to_user_id: miniChatUser.id, message: msg});
    }
    appendMiniChatMessage('You', msg, true);
    input.value = '';
};

function appendMiniChatMessage(sender, message, isSelf) {
    const container = document.getElementById('miniChatMessages');
    if (!container) return;
    const div = document.createElement('div');
    div.style.cssText = `text-align:${isSelf ? 'right' : 'left'}; margin-bottom:8px;`;
    div.innerHTML = `<div style="display:inline-block; padding:8px 12px; border-radius:12px; background:${isSelf ? 'var(--primary)' : 'var(--surface)'}; max-width:80%;">
        <div style="font-size:0.8rem; font-weight:600;">${escapeHtml(sender)}</div>
        <div>${escapeHtml(message)}</div>
    </div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}
