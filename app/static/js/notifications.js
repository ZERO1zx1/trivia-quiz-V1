/* TriviaVerse notifications — rebuilt to work with the shared application controller. */
(() => {
  "use strict";

  const badge = () => document.getElementById("notifBadge");
  const items = () => document.getElementById("notifItems");

  function typeToIcon(type) {
    return ({ success: "✓", warning: "!", game_invite: "▶", info: "i" })[type] || "i";
  }

  function formatTime(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    const minutes = Math.floor((Date.now() - date.getTime()) / 60000);
    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  }

  async function updateNotifBadge() {
    try {
      const response = await fetch("/api/notifications/unread-count");
      if (!response.ok) return;
      const data = await response.json();
      const target = badge();
      if (!target) return;
      const count = Number(data.count || 0);
      target.textContent = count > 99 ? "99+" : String(count);
      target.hidden = count < 1;
    } catch {
      // A notification badge should never interrupt gameplay or navigation.
    }
  }

  function renderNotifications(notifications) {
    const container = items();
    if (!container) return;
    container.replaceChildren();

    if (!notifications?.length) {
      const empty = document.createElement("p");
      empty.className = "notif-item";
      empty.textContent = "No notifications yet";
      container.append(empty);
      return;
    }

    notifications.forEach((notification) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = `notif-item${notification.is_read ? "" : " unread"}`;
      item.dataset.notificationId = notification.id;
      item.innerHTML = `
        <span class="notif-icon" aria-hidden="true">${typeToIcon(notification.type)}</span>
        <span class="notif-content">
          <span class="notif-title"></span>
          <span class="notif-message"></span>
          <span class="notif-time"></span>
        </span>`;
      item.querySelector(".notif-title").textContent = notification.title || "Notification";
      item.querySelector(".notif-message").textContent = notification.message || "";
      item.querySelector(".notif-time").textContent = formatTime(notification.created_at);
      container.append(item);
    });
  }

  async function loadNotifications() {
    try {
      const response = await fetch("/api/notifications");
      if (!response.ok) throw new Error("Notification request failed");
      renderNotifications(await response.json());
    } catch {
      const container = items();
      if (container) container.textContent = "Could not load notifications.";
    }
  }

  async function markAsRead(notificationId) {
    if (!notificationId) return;
    try {
      await window.apiFetch(`/api/notifications/${notificationId}/read`, { method: "POST" });
      await Promise.all([loadNotifications(), updateNotifBadge()]);
    } catch {
      window.showToast?.("Could not update this notification.", "error");
    }
  }

  async function markAllRead() {
    try {
      await window.apiFetch("/api/notifications/read-all", { method: "POST" });
      await Promise.all([loadNotifications(), updateNotifBadge()]);
    } catch {
      window.showToast?.("Could not mark notifications as read.", "error");
    }
  }

  function connectSocket() {
    if (!window.io) return;
    const socket = window.io("/notifications");
    socket.on("new_notification", (data) => {
      window.showToast?.(`${data.title}: ${data.message || ""}`, data.type || "info");
      updateNotifBadge();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    connectSocket();
    updateNotifBadge();
    items()?.addEventListener("click", (event) => {
      const notification = event.target.closest("[data-notification-id]");
      if (notification) markAsRead(notification.dataset.notificationId);
    });
  }, { once: true });

  window.loadNotifications = loadNotifications;
  window.markAsRead = markAsRead;
  window.markAllRead = markAllRead;
  window.updateNotifBadge = updateNotifBadge;
})();
