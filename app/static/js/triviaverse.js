/**
 * TriviaVerse Enterprise JavaScript
 * Version 3.0 - Full Feature Support
 */

// === Utility Functions ===
const TriviaVerse = {
    // API Helper
    api: {
        async get(url, params = {}) {
            const query = new URLSearchParams(params).toString();
            const fullUrl = query ? `${url}?${query}` : url;
            const response = await fetch(fullUrl);
            return response.json();
        },
        async post(url, data = {}, isForm = false) {
            const options = {
                method: 'POST',
                headers: isForm ? { 'Content-Type': 'application/x-www-form-urlencoded' } : { 'Content-Type': 'application/json' },
                body: isForm ? new URLSearchParams(data).toString() : JSON.stringify(data),
            };
            const response = await fetch(url, options);
            return response.json();
        }
    },

    // Toast Notifications
    toast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    // Confirm Dialog
    async confirm(message) {
        return new Promise((resolve) => {
            if (window.confirm(message)) resolve(true);
            else resolve(false);
        });
    },

    // Format Numbers
    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    },

    // Format Time
    formatDuration(seconds) {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m}:${s.toString().padStart(2, '0')}`;
    },

    // Countdown Timer
    countdown(elementId, endTime) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const update = () => {
            const now = new Date().getTime();
            const distance = new Date(endTime).getTime() - now;

            if (distance < 0) {
                element.textContent = 'Ended';
                return;
            }

            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);

            element.textContent = `${days}d ${hours}h ${minutes}m ${seconds}s`;
        };

        update();
        return setInterval(update, 1000);
    },

    // Sound Effects
    audio: {
        play(type) {
            const sounds = {
                correct: '/static/sounds/correct.mp3',
                wrong: '/static/sounds/wrong.mp3',
                click: '/static/sounds/click.mp3',
                levelup: '/static/sounds/levelup.mp3',
                reward: '/static/sounds/reward.mp3',
                victory: '/static/sounds/victory.mp3',
                defeat: '/static/sounds/defeat.mp3',
                notification: '/static/sounds/notification.mp3',
            };
            const audio = new Audio(sounds[type] || sounds.click);
            audio.volume = 0.5;
            audio.play().catch(() => {});
        }
    },

    // Animations
    animate: {
        fadeIn(element, duration = 300) {
            element.style.opacity = '0';
            element.style.transition = `opacity ${duration}ms ease`;
            requestAnimationFrame(() => {
                element.style.opacity = '1';
            });
        },
        slideIn(element, direction = 'up', duration = 300) {
            const transforms = {
                up: 'translateY(20px)',
                down: 'translateY(-20px)',
                left: 'translateX(-20px)',
                right: 'translateX(20px)',
            };
            element.style.transform = transforms[direction];
            element.style.opacity = '0';
            element.style.transition = `all ${duration}ms ease`;
            requestAnimationFrame(() => {
                element.style.transform = 'translate(0)';
                element.style.opacity = '1';
            });
        },
        pulse(element) {
            element.style.transition = 'transform 0.3s ease';
            element.style.transform = 'scale(1.05)';
            setTimeout(() => {
                element.style.transform = 'scale(1)';
            }, 300);
        }
    },

    // Local Storage
    storage: {
        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch { return defaultValue; }
        },
        set(key, value) {
            try { localStorage.setItem(key, JSON.stringify(value)); } catch {}
        },
        remove(key) {
            try { localStorage.removeItem(key); } catch {}
        }
    },

    // Debounce
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Copy to Clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.toast('Copied to clipboard!', 'success');
            return true;
        } catch {
            // Fallback
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            this.toast('Copied!', 'success');
            return true;
        }
    },

    // Fullscreen toggle
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(() => {});
        } else {
            document.exitFullscreen().catch(() => {});
        }
    },

    // Keyboard Shortcuts
    shortcuts: {
        register(key, callback) {
            document.addEventListener('keydown', (e) => {
                if (e.key === key && !e.ctrlKey && !e.metaKey && !e.altKey) {
                    if (document.activeElement.tagName !== 'INPUT' &&
                        document.activeElement.tagName !== 'TEXTAREA') {
                        e.preventDefault();
                        callback();
                    }
                }
            });
        }
    }
};

// === Initialize ===
document.addEventListener('DOMContentLoaded', () => {
    // Global keyboard shortcuts
    TriviaVerse.shortcuts.register('n', () => {
        // Notification toggle placeholder
    });

    // Initialize tooltips
    document.querySelectorAll('[data-tooltip]').forEach(el => {
        el.addEventListener('mouseenter', (e) => {
            const tooltip = document.createElement('div');
            tooltip.className = 'absolute bg-gray-900 text-white text-xs px-2 py-1 rounded shadow-lg z-50';
            tooltip.textContent = el.dataset.tooltip;
            tooltip.style.top = `${e.target.offsetTop - 30}px`;
            tooltip.style.left = `${e.target.offsetLeft}px`;
            el.style.position = 'relative';
            el.appendChild(tooltip);
        });
        el.addEventListener('mouseleave', () => {
            const tooltip = el.querySelector('[class*="bg-gray-900"]');
            if (tooltip) tooltip.remove();
        });
    });
});

// Export for modules
if (typeof module !== 'undefined') module.exports = TriviaVerse;
