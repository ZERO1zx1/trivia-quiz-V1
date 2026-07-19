// ==================================
//  Notification System
// ==================================
let notificationsUnread = 0;

// Socket холболт (мэдэгдлийн namespace)
const notifSocket = io('/notifications');

notifSocket.on('new_notification', (data) => {
    // Шинэ мэдэгдэл ирэхэд badge шинэчлэх, toast харуулах
    notificationsUnread++;
    updateNotifBadge();
    showToast(data.title + ': ' + (data.message || ''), data.type || 'info');
    // Хэрэв dropdown нээлттэй бол жагсаалтыг дахин татах
    if (document.getElementById('notifMenu').classList.contains('show')) {
        loadNotifications();
    }
});

// Dropdown toggle
window.toggleNotifDropdown = () => {
    const menu = document.getElementById('notifMenu');
    const isOpen = menu.classList.toggle('show');
    if (isOpen) {
        loadNotifications();
    }
    // Бусад dropdown-уудыг хаах
    document.querySelectorAll('.dropdown-menu').forEach(d => {
        if (d !== menu) d.classList.remove('show');
    });
};

// Badge шинэчлэх
async function updateNotifBadge() {
    try {
        const resp = await fetch('/api/notifications/unread-count');
        const data = await resp.json();
        notificationsUnread = data.count;
        const badge = document.getElementById('notifBadge');
        if (data.count > 0) {
            badge.textContent = data.count > 99 ? '99+' : data.count;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    } catch(e) { console.error(e); }
}

// Мэдэгдлүүдийг татах
async function loadNotifications() {
    try {
        const resp = await fetch('/api/notifications');
        const notifications = await resp.json();
        renderNotifications(notifications);
    } catch(e) { console.error(e); }
}

// Жагсаалтыг дүрслэх
function renderNotifications(notifications) {
    const container = document.getElementById('notifItems');
    if (!notifications.length) {
        container.innerHTML = '<div class="notif-item" style="justify-content:center;color:var(--text-secondary);">No notifications yet</div>';
        return;
    }
    container.innerHTML = notifications.map(n => `
        <div class="notif-item ${n.is_read ? '' : 'unread'}" onclick="markAsRead(${n.id})">
            <div class="notif-icon" style="background:${typeToColor(n.type)};">
                ${typeToIcon(n.type)}
            </div>
            <div class="notif-content">
                <div class="notif-title">${escapeHtml(n.title)}</div>
                <div class="notif-message">${escapeHtml(n.message || '')}</div>
                <div class="notif-time">${formatTime(n.created_at)}</div>
            </div>
        </div>
    `).join('');
}

// Туслах функцүүд
function typeToColor(type) {
    const colors = { info:'rgba(59,130,246,0.2)', success:'rgba(34,197,94,0.2)', warning:'rgba(250,204,21,0.2)', game_invite:'rgba(139,92,246,0.2)' };
    return colors[type] || 'rgba(255,255,255,0.1)';
}

function typeToIcon(type) {
    const icons = { info:'💬', success:'✅', warning:'⚠️', game_invite:'🎮' };
    return `<span>${icons[type] || 'ℹ️'}</span>`;
}

function formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHrs = Math.floor(diffMins / 60);
    if (diffHrs < 24) return `${diffHrs}h ago`;
    return date.toLocaleDateString();
}

// Уншсан болгох
async function markAsRead(notifId) {
    try {
        await fetch(`/api/notifications/${notifId}/read`, { method: 'POST' });
        notifSocket.emit('mark_read', { notif_id: notifId });
        // Дэлгэц шинэчлэх
        loadNotifications();
        updateNotifBadge();
    } catch(e) { console.error(e); }
}

// Бүгдийг уншсан болгох
async function markAllRead() {
    try {
        await fetch('/api/notifications/read-all', { method: 'POST' });
        loadNotifications();
        updateNotifBadge();
    } catch(e) { console.error(e); }
}

// Хуудас ачаалагдах үед badge-г шинэчлэх
document.addEventListener('DOMContentLoaded', () => {
    updateNotifBadge();
});