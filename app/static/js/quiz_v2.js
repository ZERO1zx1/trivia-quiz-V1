/* =============================================
   Trivia Quiz V2 — Common JS (Theme, Language)
   ============================================= */

(function() {
    'use strict';

    // Theme toggle
    const themeBtn = document.getElementById('themeToggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const html = document.documentElement;
            const current = html.getAttribute('data-theme') || 'light';
            const next = current === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', next);
            const icon = themeBtn.querySelector('.theme-icon');
            if (icon) icon.textContent = next === 'dark' ? '☀️' : '🌙';

            // Save preference
            fetch('/quiz/v2/api/user_settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ theme: next })
            }).catch(() => {});
        });

        // Set initial icon
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const icon = themeBtn.querySelector('.theme-icon');
        if (icon) icon.textContent = currentTheme === 'dark' ? '☀️' : '🌙';
    }

    // Auto-detect system dark mode preference
    if (window.matchMedia && !document.querySelector('[data-theme]')) {
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
    }
})();
