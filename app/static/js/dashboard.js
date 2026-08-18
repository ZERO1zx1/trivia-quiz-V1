/* Dashboard interaction controller. */
(() => {
  "use strict";

  const get = (selector) => document.querySelector(selector);
  const escapeText = (value) => window.escapeHtml?.(value) ?? String(value ?? "");

  function setButtonState(button, label, disabled = true) {
    if (!button) return;
    button.disabled = disabled;
    button.textContent = label;
  }

  async function claimDaily() {
    const button = get("#dailyBtn");
    setButtonState(button, "Claiming…");
    try {
      const data = await window.apiFetch("/dashboard/daily-reward", { method: "POST" });
      if (!data.success) throw new Error(data.message || "Could not claim reward.");

      const reward = `${data.reward} coins${data.xp_earned ? ` + ${data.xp_earned} XP` : ""}`;
      window.showToast?.(`Daily reward claimed: ${reward}.`, "success");
      setButtonState(button, "Claimed");
      if (data.level_up) window.showToast?.(`Level up! You are now level ${data.new_level}.`, "success");
      await updateDashboardStats();
    } catch (error) {
      window.showToast?.(error.message || "Network error. Please try again.", "error");
      setButtonState(button, "Claim", false);
    }
  }

  async function spinFortune(event) {
    const button = event?.currentTarget || get("#fortuneBtn");
    setButtonState(button, "Spinning…");
    try {
      const data = await window.apiFetch("/fortune/spin", { method: "POST" });
      if (!data.success) throw new Error(data.message || "Could not spin the wheel.");
      window.showToast?.(`You won: ${data.prize.icon} ${data.prize.name}!`, "success");
    } catch (error) {
      window.showToast?.(error.message || "Failed to spin. Try again later.", "error");
    } finally {
      setButtonState(button, "Spin", false);
    }
  }

  async function updateDashboardStats() {
    try {
      const response = await fetch("/api/user/stats", { headers: { Accept: "application/json" } });
      if (!response.ok) return;
      const stats = await response.json();
      const values = {
        dashboardWins: stats.wins ?? 0,
        dashboardAccuracy: `${Number(stats.accuracy ?? 0).toFixed(1)}%`,
        dashboardLevel: stats.level ?? 1,
        dashboardCoins: stats.coins ?? 0,
      };
      Object.entries(values).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) element.textContent = String(value);
      });

      if (stats.xp !== undefined && stats.level !== undefined) {
        const required = stats.level * stats.level * 100;
        const progress = Math.min((stats.xp / required) * 100, 100);
        const fill = get(".progress-fill");
        const label = get(".xp-label strong");
        if (fill) fill.style.width = `${progress}%`;
        if (label) label.textContent = `${stats.xp} / ${required}`;
      }
    } catch {
      // Dashboard remains usable with its server-rendered values.
    }
  }

  function questRow(quest) {
    const article = document.createElement("article");
    article.className = "quest-row";
    article.innerHTML = `
      <div class="quest-row__top"><strong>${escapeText(quest.quest_type.replaceAll("_", " "))}</strong><span>${quest.current_value}/${quest.target_value}</span></div>
      <div class="quest-row__track"><span style="width:${Math.max(0, Math.min(Number(quest.progress) || 0, 100))}%"></span></div>
      <div class="quest-row__footer"><span>Reward · ${quest.reward_coins} coins + ${quest.reward_xp} XP</span></div>`;

    const footer = article.querySelector(".quest-row__footer");
    if (quest.is_completed && !quest.is_claimed) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "btn btn-primary btn-sm";
      button.textContent = "Claim";
      button.addEventListener("click", () => claimQuest(quest.id));
      footer.append(button);
    } else if (quest.is_claimed) {
      const claimed = document.createElement("span");
      claimed.className = "quest-row__claimed";
      claimed.textContent = "Claimed";
      footer.append(claimed);
    }
    return article;
  }

  async function loadDailyQuests() {
    const container = get("#dailyQuests");
    if (!container) return;
    try {
      const quests = await window.apiFetch("/quests/daily-quests");
      container.replaceChildren();
      if (!quests?.length) {
        const empty = document.createElement("p");
        empty.className = "panel-empty";
        empty.textContent = "No daily quests are available yet.";
        container.append(empty);
        return;
      }
      quests.forEach((quest) => container.append(questRow(quest)));
    } catch {
      container.textContent = "Daily quests are unavailable right now.";
      container.classList.add("panel-empty");
    }
  }

  async function claimQuest(questId) {
    try {
      const data = await window.apiFetch(`/quests/daily-quests/${questId}/claim`, { method: "POST" });
      if (!data.success) throw new Error("Could not claim this quest.");
      window.showToast?.(`Quest claimed: ${data.reward_coins} coins + ${data.reward_xp} XP.`, "success");
      await Promise.all([loadDailyQuests(), updateDashboardStats()]);
    } catch (error) {
      window.showToast?.(error.message || "Failed to claim quest.", "error");
    }
  }

  async function loadCoachAdvice() {
    const target = get("#aiCoachAdvice");
    if (!target) return;
    target.replaceChildren();
    const spinner = document.createElement("span");
    spinner.className = "loading-spinner";
    spinner.setAttribute("aria-hidden", "true");
    target.append(spinner, document.createTextNode(" Thinking…"));
    try {
      const response = await fetch("/api/coach/advice", { headers: { Accept: "application/json" } });
      const data = await response.json();
      target.textContent = data.advice ? `“${data.advice}”` : "Coach is taking a break. Try again later.";
    } catch {
      target.textContent = "Advice is unavailable right now. Try again later.";
    }
  }

  function bindActions() {
    document.querySelectorAll("[data-dashboard-action]").forEach((control) => {
      control.addEventListener("click", async (event) => {
        const action = control.dataset.dashboardAction;
        if (action === "solo") window.location.href = control.dataset.soloUrl;
        if (action === "daily") await claimDaily();
        if (action === "fortune") await spinFortune(event);
        if (action === "coach") await loadCoachAdvice();
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindActions();
    updateDashboardStats();
    loadDailyQuests();
    loadCoachAdvice();
    window.setInterval(updateDashboardStats, 30000);
  }, { once: true });

  window.claimDaily = claimDaily;
  window.spinFortune = spinFortune;
  window.claimQuest = claimQuest;
})();
