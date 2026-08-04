// =============================================
//  TriviaVerse Dashboard Page Script
// =============================================

document.addEventListener('DOMContentLoaded', () => {
    // ----- Өдрийн шагнал (Daily Reward) -----
    const dailyBtn = document.getElementById('dailyBtn');
    if (dailyBtn) {
        dailyBtn.addEventListener('click', claimDaily);
    }

    // ----- Хурдан шинэчлэлт (Live stats) -----
    updateDashboardStats();
    // 30 секунд тутамд шинэчлэх
    setInterval(updateDashboardStats, 30000);

    // ----- Fortune Wheel button -----
    const fortuneBtn = document.getElementById('fortuneBtn');
    if (fortuneBtn) {
        fortuneBtn.addEventListener('click', spinFortune);
    }

    // ----- Daily Quests -----
    loadDailyQuests();
});

// ==================================
//  Дэд функцууд
// ==================================

/**
 * Өдрийн шагналыг авах
 */
async function claimDaily() {
    const btn = document.getElementById('dailyBtn');
    if (!btn) return;
    btn.disabled = true;
    btn.textContent = '⏳ Claiming...';

    try {
        const data = await apiFetch('/dashboard/daily-reward', { method: 'POST' });

        if (data.success) {
            let message = `✅ Claimed ${data.reward} coins!`;
            if (data.xp_earned) {
                message += ` +${data.xp_earned} XP`;
            }
            showToast(message, 'success');

            if (data.level_up) {
                showToast(`🎉 Level Up! You are now level ${data.new_level}!`, 'success');
            }

            btn.textContent = '✅ Claimed';
            btn.disabled = true;

            if (data.new_coins !== undefined) {
                const coinEl = document.getElementById('dashboardCoins');
                if (coinEl) coinEl.textContent = data.new_coins;
            }

            if (data.new_xp !== undefined || data.level_up) {
                updateDashboardStats();
            }
        } else {
            showToast(data.message || 'Could not claim reward.', 'warning');
            btn.disabled = false;
            btn.textContent = '🎁 Claim 100 Coins';
        }
    } catch (error) {
        showToast('Network error. Please try again.', 'error');
        btn.disabled = false;
        btn.textContent = '🎁 Claim 100 Coins';
    }
}

/**
 * Dashboard статистикуудыг шинэчлэх
 */
async function updateDashboardStats() {
    try {
        const resp = await fetch('/api/user/stats');
        if (!resp.ok) return;
        const stats = await resp.json();

        // Update stat cards
        const statCards = document.querySelectorAll('.stat-card-value');
        if (statCards.length >= 4) {
            statCards[0].textContent = stats.wins ?? '0';
            statCards[1].textContent = (stats.accuracy ?? 0).toFixed(1) + '%';
            statCards[2].textContent = stats.level ?? '1';
            statCards[3].textContent = stats.coins ?? '0';
        }

        // Update specific IDs if they exist
        const winsEl = document.getElementById('dashboardWins');
        if (winsEl) winsEl.textContent = stats.wins ?? '0';
        const accuracyEl = document.getElementById('dashboardAccuracy');
        if (accuracyEl) accuracyEl.textContent = (stats.accuracy ?? 0).toFixed(1) + '%';
        const levelEl = document.getElementById('dashboardLevel');
        if (levelEl) levelEl.textContent = stats.level ?? '1';
        const coinsEl = document.getElementById('dashboardCoins');
        if (coinsEl) coinsEl.textContent = stats.coins ?? '0';

        // Sidebar footer coins
        const sidebarCoins = document.querySelector('.user-coins span');
        if (sidebarCoins && stats.coins !== undefined) {
            sidebarCoins.textContent = `${stats.coins}`;
        }

        // XP progress bar
        if (stats.xp !== undefined && stats.level !== undefined) {
            const xpForNext = stats.level * stats.level * 100;
            const progress = Math.min((stats.xp / xpForNext) * 100, 100);

            // Try multiple selector patterns
            const progressBar = document.querySelector('.xp-progress-fill') ||
                               document.querySelector('.profile-xp-bar') ||
                               document.querySelector('.stat-bar-fill');
            if (progressBar) {
                progressBar.style.width = progress + '%';
            }

            const xpText = document.querySelector('.profile-xp-text') ||
                          document.querySelector('.xp-text');
            if (xpText) {
                xpText.textContent = `${stats.xp} / ${xpForNext} XP`;
            }
        }
    } catch (e) {
        console.error('Dashboard stats update failed:', e);
    }
}

async function loadDailyQuests() {
    try {
        const quests = await apiFetch('/quests/daily-quests');
        const container = document.getElementById('dailyQuests');
        if (!container) return;
        if (!quests || !quests.length) {
            container.innerHTML = '<p style="color:var(--text-secondary);">No quests today.</p>';
            return;
        }
        container.innerHTML = quests.map(q => `
            <div style="margin-bottom:12px;padding:12px;background:var(--surface);border-radius:12px;border:1px solid var(--border);">
                <div style="font-weight:600;">${escapeHtml(q.quest_type.replace('_', ' ').toUpperCase())}: ${q.current_value}/${q.target_value}</div>
                <div style="background:rgba(0,0,0,0.2);border-radius:10px;height:8px;overflow:hidden;margin:8px 0;">
                    <div style="width:${q.progress}%;height:100%;background:linear-gradient(90deg, var(--primary), var(--accent));border-radius:10px;transition:width 0.3s;"></div>
                </div>
                <div style="font-size:0.85rem;color:var(--text-secondary);display:flex;justify-content:space-between;align-items:center;">
                    <span>Reward: 🪙 ${q.reward_coins} + ${q.reward_xp} XP</span>
                    ${q.is_completed && !q.is_claimed ? `<button onclick="claimQuest(${q.id})" class="btn btn-sm btn-primary">Claim</button>` : ''}
                    ${q.is_claimed ? '<span>✅ Claimed</span>' : ''}
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed to load quests:', e);
        const container = document.getElementById('dailyQuests');
        if (container) container.innerHTML = '<p style="color:var(--text-secondary);">Failed to load quests.</p>';
    }
}

async function claimQuest(questId) {
    try {
        const data = await apiFetch(`/quests/daily-quests/${questId}/claim`, { method: 'POST' });
        if (data.success) {
            showToast(`Claimed ${data.reward_coins} coins + ${data.reward_xp} XP!`, 'success');
            loadDailyQuests();
            updateDashboardStats();
        }
    } catch (e) {
        showToast('Failed to claim quest.', 'error');
    }
}

// Fortune Wheel
window.spinFortune = async function() {
    const btn = document.getElementById('fortuneBtn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = '🎰 Spinning...';
    }
    try {
        const data = await apiFetch('/fortune/spin', { method: 'POST' });
        if (data.success) {
            showToast(`You won: ${data.prize.icon} ${data.prize.name}!`, 'success');
        } else {
            showToast(data.message || 'Could not spin.', 'warning');
        }
    } catch (e) {
        showToast('Failed to spin. Try again later.', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = '🎰 Spin Wheel';
        }
    }
};

window.startSoloPractice = function () {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/quiz/solo/start';
    const csrf = document.querySelector('meta[name="csrf-token"]');
    if (csrf) {
        form.innerHTML = `<input type="hidden" name="csrf_token" value="${csrf.getAttribute('content')}">`;
    }
    document.body.appendChild(form);
    form.submit();
};

window.openSoloModal = function () {
    const modal = document.getElementById('soloModal');
    if (modal) modal.style.display = 'flex';
};

window.startSoloWithDifficulty = function (difficulty) {
    const modal = document.getElementById('soloModal');
    if (modal) modal.style.display = 'none';
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/quiz/solo/start';
    const csrf = document.querySelector('meta[name="csrf-token"]');
    form.innerHTML = `<input type="hidden" name="csrf_token" value="${csrf ? csrf.getAttribute('content') : ''}">
                      <input type="hidden" name="difficulty" value="${escapeHtml(difficulty)}">`;
    document.body.appendChild(form);
    form.submit();
};

function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
