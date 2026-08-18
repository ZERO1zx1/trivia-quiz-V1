/* Public home page enhancements. */
(() => {
  "use strict";

  function renderNumber(id, value, fallback = "—") {
    const element = document.getElementById(id);
    if (!element) return;
    const number = Number(value);
    element.textContent = Number.isFinite(number) ? number.toLocaleString() : fallback;
  }

  async function loadLiveStats() {
    try {
      const response = await fetch("/api/stats", { headers: { Accept: "application/json" } });
      if (!response.ok) return;
      const data = await response.json();
      renderNumber("statPlayers", data.total_players);
      renderNumber("statQuestions", data.total_questions);
      renderNumber("statRooms", data.active_rooms);
    } catch {
      // The server-rendered player count remains useful if the optional endpoint is unavailable.
    }
  }

  function addParticles() {
    const container = document.getElementById("particles");
    if (!container || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const fragment = document.createDocumentFragment();
    for (let index = 0; index < 24; index += 1) {
      const particle = document.createElement("span");
      particle.className = "particle";
      particle.style.left = `${Math.round(Math.random() * 100)}%`;
      particle.style.top = `${Math.round(Math.random() * 100)}%`;
      particle.style.opacity = String(0.18 + Math.random() * 0.45);
      fragment.append(particle);
    }
    container.append(fragment);
  }

  document.addEventListener("DOMContentLoaded", () => {
    addParticles();
    loadLiveStats();
  }, { once: true });
})();
