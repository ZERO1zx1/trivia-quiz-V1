// =============================================
//  TriviaVerse Core Application Script
// =============================================

document.addEventListener('DOMContentLoaded', () => {
    // ---------- Sidebar Toggle ----------
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');

    if (sidebarToggle && sidebar) {
        // LocalStorage-с төлөвийг унших
        if (localStorage.getItem('sidebarCollapsed') === 'true') {
            sidebar.classList.add('collapsed');
        }

        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
    }

    // ---------- User Dropdown ----------
    window.toggleDropdown = () => {
        const dropdown = document.getElementById('userDropdown');
        if (dropdown) dropdown.classList.toggle('show');
    };

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu').forEach(d => d.classList.remove('show'));
        }
    });

    // ---------- Flash Messages → Toast (шуурхай) ----------
    document.querySelectorAll('.flash').forEach(el => {
        const category = el.classList.contains('flash-success') ? 'success' :
                         el.classList.contains('flash-error') ? 'error' :
                         el.classList.contains('flash-warning') ? 'warning' : 'info';
        if (typeof showToast === 'function') {
            showToast(el.textContent.trim(), category);
        }
        el.remove();
    });

    // ---------- Search Input ----------
    const searchInput = document.querySelector('.navbar-search input');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = searchInput.value.trim();
                if (query) {
                    // Хайлтын хуудас руу чиглүүлэх (одоогоор placeholder)
                    window.location.href = `/search?q=${encodeURIComponent(query)}`;
                }
            }
        });
    }

    // ---------- Notification Button ----------
    const notifBtn = document.getElementById('notifBtn');
    if (notifBtn) {
        notifBtn.addEventListener('click', () => {
            // Мэдэгдлийн цонх нээх (одоогоор toast харуулна)
            showToast('Notifications not yet implemented', 'info');
        });
    }
});

// ==================================
//  Global Utility Functions
// ==================================

/**
 * CSRF Token авах (meta tag эсвэл cookie-оос)
 * @returns {string|null}
 */
window.getCSRFToken = () => {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');

    // Fallback: cookie-с хайх
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

/**
 * Clipboard-д хуулах
 * @param {string} text
 */
window.copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        // Fallback
        const input = document.createElement('textarea');
        input.value = text;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
        showToast('Copied!', 'success');
    });
};

/**
 * Toast мэдэгдэл харуулах
 * @param {string} message
 * @param {string} type - 'success', 'error', 'warning', 'info'
 */
window.showToast = (message, type = 'info') => {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.setAttribute('role', 'alert');
    document.body.appendChild(toast);

    // Slide in
    requestAnimationFrame(() => {
        toast.style.transform = 'translateX(0)';
        toast.style.opacity = '1';
    });

    // Автоматаар устгах
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
};

/**
 * API хүсэлт илгээхэд зориулсан туслах функц
 * @param {string} url
 * @param {object} options
 * @returns {Promise<any>}
 */
window.apiFetch = async (url, options = {}) => {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    // Хэрэв POST/PUT/DELETE бол CSRF токен нэмэх
    if (options.method && ['POST', 'PUT', 'DELETE'].includes(options.method.toUpperCase())) {
        headers['X-CSRFToken'] = getCSRFToken();
    }

    const response = await fetch(url, {
        ...options,
        headers
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Request failed' }));
        throw new Error(error.message || `HTTP ${response.status}`);
    }

    return response.json();
};

// ==================================
//  Sidebar Active State Updater
// ==================================
// Хуудас ачаалагдах үед одоогийн URL-д тохирох nav-item-г идэвхжүүлэх
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href)) {
            link.classList.add('active');
        }
    });
});

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

window.apiFetch = async (url, options = {}) => {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (options.method && ['POST', 'PUT', 'DELETE'].includes(options.method.toUpperCase())) {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
    }

    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Request failed' }));
        throw new Error(error.message || `HTTP ${response.status}`);
    }

    return response.json();
};

// =====================
//  Dark/Light Mode Toggle
// =====================
window.toggleTheme = function() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
};

document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('theme');
    if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
    }
});