/* TriviaVerse application controller — rebuilt from scratch. */
(() => {
  "use strict";

  const selectors = {
    sidebar: "#sidebar",
    backdrop: "#sidebarBackdrop",
    toastRegion: "#toastRegion",
    userMenu: "#userDropdown",
    notifMenu: "#notifMenu",
    miniChat: "#miniChat",
    miniChatInput: "#miniChatInput",
    miniChatMessages: "#miniChatMessages",
    miniChatTitle: "#miniChatTitle",
  };

  let miniChatUser = null;

  const getElement = (selector) => document.querySelector(selector);
  const getAll = (selector) => Array.from(document.querySelectorAll(selector));

  function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");
    if (token) return token;

    const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  async function apiFetch(url, options = {}) {
    const method = (options.method || "GET").toUpperCase();
    const headers = { ...options.headers };

    if (options.body && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }
    if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
      headers["X-CSRFToken"] = getCSRFToken();
    }

    const response = await fetch(url, { ...options, method, headers });
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json") ? await response.json() : null;

    if (!response.ok) {
      throw new Error(payload?.message || payload?.error || `Request failed (${response.status})`);
    }
    return payload;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function showToast(message, type = "info") {
    const region = getElement(selectors.toastRegion);
    if (!region || !message) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.setAttribute("role", type === "error" ? "alert" : "status");
    toast.textContent = message;
    region.append(toast);

    window.setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(.4rem)";
      window.setTimeout(() => toast.remove(), 180);
    }, 4200);
  }

  function closeMenus(except = null) {
    getAll(".dropdown-menu.show").forEach((menu) => {
      if (menu !== except) menu.classList.remove("show");
    });
    getAll('[aria-controls="userDropdown"], [aria-controls="notifMenu"]').forEach((trigger) => {
      const controls = trigger.getAttribute("aria-controls");
      if (getElement(`#${controls}`) !== except) trigger.setAttribute("aria-expanded", "false");
    });
  }

  function toggleMenu(menuSelector, triggerSelector) {
    const menu = getElement(menuSelector);
    const trigger = getElement(triggerSelector);
    if (!menu) return false;

    const shouldOpen = !menu.classList.contains("show");
    closeMenus(menu);
    menu.classList.toggle("show", shouldOpen);
    trigger?.setAttribute("aria-expanded", String(shouldOpen));
    return shouldOpen;
  }

  function setSidebarOpen(isOpen) {
    const sidebar = getElement(selectors.sidebar);
    const backdrop = getElement(selectors.backdrop);
    const trigger = getElement("#mobileSidebarToggle");
    if (!sidebar || !backdrop) return;

    sidebar.classList.toggle("open", isOpen);
    backdrop.hidden = !isOpen;
    backdrop.classList.toggle("is-visible", isOpen);
    trigger?.setAttribute("aria-expanded", String(isOpen));
    document.body.style.overflow = isOpen ? "hidden" : "";
  }

  function toggleSidebarCollapsed() {
    const sidebar = getElement(selectors.sidebar);
    const trigger = getElement("#sidebarToggle");
    if (!sidebar || window.matchMedia("(max-width: 54rem)").matches) return;

    const collapsed = !sidebar.classList.contains("collapsed");
    sidebar.classList.toggle("collapsed", collapsed);
    trigger?.setAttribute("aria-pressed", String(collapsed));
    trigger?.setAttribute("aria-label", collapsed ? "Expand navigation" : "Collapse navigation");
    localStorage.setItem("triviaverse.sidebar.collapsed", String(collapsed));
  }

  function applyTheme(theme, { sync = false } = {}) {
    const safeTheme = theme === "light" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", safeTheme);
    localStorage.setItem("triviaverse.theme", safeTheme);

    if (sync) {
      apiFetch("/account/settings/theme", {
        method: "POST",
        body: JSON.stringify({ theme: safeTheme }),
      }).catch(() => showToast("Theme saved locally; server sync will retry next time.", "warning"));
    }
    return safeTheme;
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme");
    applyTheme(current === "dark" ? "light" : "dark", { sync: true });
  }

  function copyToClipboard(value) {
    const text = String(value ?? "");
    if (!text) return;

    const fallback = () => {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.append(textarea);
      textarea.select();
      document.execCommand("copy");
      textarea.remove();
    };

    (navigator.clipboard?.writeText ? navigator.clipboard.writeText(text) : Promise.reject())
      .catch(fallback)
      .finally(() => showToast("Copied to clipboard.", "success"));
  }

  function openMiniChat(userId, username) {
    const chat = getElement(selectors.miniChat);
    const title = getElement(selectors.miniChatTitle);
    const messages = getElement(selectors.miniChatMessages);
    if (!chat) return;

    miniChatUser = { id: userId, name: username || "Chat" };
    if (title) title.textContent = miniChatUser.name;
    if (messages) messages.replaceChildren();
    chat.classList.remove("hidden");
    getElement(selectors.miniChatInput)?.focus();
  }

  function closeMiniChat() {
    getElement(selectors.miniChat)?.classList.add("hidden");
    miniChatUser = null;
  }

  function toggleMiniChat() {
    getElement(selectors.miniChat)?.classList.toggle("hidden");
  }

  function appendMiniChatMessage(sender, message, isSelf) {
    const container = getElement(selectors.miniChatMessages);
    if (!container) return;

    const wrapper = document.createElement("article");
    wrapper.className = `mini-chat-message${isSelf ? " is-self" : ""}`;
    wrapper.innerHTML = `<strong>${escapeHtml(sender)}</strong><p>${escapeHtml(message)}</p>`;
    container.append(wrapper);
    container.scrollTop = container.scrollHeight;
  }

  function sendMiniChat() {
    const input = getElement(selectors.miniChatInput);
    const message = input?.value.trim();
    if (!message || !miniChatUser) return;

    if (window.socket?.emit) {
      window.socket.emit("direct_message", { to_user_id: miniChatUser.id, message });
    }
    appendMiniChatMessage("You", message, true);
    input.value = "";
  }

  function hydrateFlashMessages() {
    getAll(".flash").forEach((flash) => {
      const type = flash.classList.contains("flash-danger") || flash.classList.contains("flash-error")
        ? "error"
        : flash.classList.contains("flash-warning")
          ? "warning"
          : flash.classList.contains("flash-success")
            ? "success"
            : "info";
      showToast(flash.textContent.trim(), type);
      flash.remove();
    });
  }

  function bindEvents() {
    document.addEventListener("click", (event) => {
      const action = event.target.closest("[data-ui]")?.dataset.ui;
      if (!action) {
        if (!event.target.closest(".dropdown")) closeMenus();
        return;
      }

      switch (action) {
        case "collapse-sidebar":
          toggleSidebarCollapsed();
          break;
        case "open-sidebar":
          setSidebarOpen(true);
          break;
        case "toggle-theme":
          toggleTheme();
          break;
        case "toggle-user-menu":
          toggleMenu(selectors.userMenu, "#userMenuButton");
          break;
        case "toggle-notifications": {
          const opened = toggleMenu(selectors.notifMenu, "#notifBtn");
          if (opened && typeof window.loadNotifications === "function") window.loadNotifications();
          break;
        }
        case "mark-notifications-read":
          window.markAllRead?.();
          break;
        case "close-mini-chat":
          closeMiniChat();
          break;
        case "toggle-mini-chat":
          toggleMiniChat();
          break;
        default:
          break;
      }
    });

    getElement(selectors.backdrop)?.addEventListener("click", () => setSidebarOpen(false));
    getElement("#miniChatForm")?.addEventListener("submit", (event) => {
      event.preventDefault();
      sendMiniChat();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeMenus();
        setSidebarOpen(false);
      }
      if (event.key === "/" && !event.metaKey && !event.ctrlKey && !event.altKey) {
        const target = event.target;
        if (!(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target?.isContentEditable)) {
          event.preventDefault();
          getElement("#global-search")?.focus();
        }
      }
    });

    window.addEventListener("resize", () => {
      if (!window.matchMedia("(max-width: 54rem)").matches) setSidebarOpen(false);
    });
  }

  function initialize() {
    const storedTheme = localStorage.getItem("triviaverse.theme");
    if (storedTheme) applyTheme(storedTheme);

    const sidebar = getElement(selectors.sidebar);
    const trigger = getElement("#sidebarToggle");
    const collapsed = localStorage.getItem("triviaverse.sidebar.collapsed") === "true";
    if (sidebar && collapsed && !window.matchMedia("(max-width: 54rem)").matches) {
      sidebar.classList.add("collapsed");
      trigger?.setAttribute("aria-pressed", "true");
    }

    bindEvents();
    hydrateFlashMessages();
  }

  window.getCSRFToken = getCSRFToken;
  window.apiFetch = apiFetch;
  window.showToast = showToast;
  window.copyToClipboard = copyToClipboard;
  window.toggleTheme = toggleTheme;
  window.setTheme = applyTheme;
  window.toggleDropdown = () => toggleMenu(selectors.userMenu, "#userMenuButton");
  window.toggleNotifDropdown = () => {
    const opened = toggleMenu(selectors.notifMenu, "#notifBtn");
    if (opened && typeof window.loadNotifications === "function") window.loadNotifications();
  };
  window.openMiniChat = openMiniChat;
  window.closeMiniChat = closeMiniChat;
  window.toggleMiniChat = toggleMiniChat;
  window.sendMiniChat = sendMiniChat;
  window.appendMiniChatMessage = appendMiniChatMessage;
  window.escapeHtml = escapeHtml;

  document.addEventListener("DOMContentLoaded", initialize, { once: true });
})();
