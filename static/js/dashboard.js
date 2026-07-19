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
            // Амжилттай авсан
            let message = `✅ Claimed ${data.reward} coins!`;
            if (data.xp_earned) {
                message += ` +${data.xp_earned} XP`;
            }
            showToast(message, 'success');

            // Level up болсон эсэхийг шалгах
            if (data.level_up) {
                showToast(`🎉 Level Up! You are now level ${data.new_level}!`, 'success');
            }

            btn.textContent = '✅ Claimed';
            btn.disabled = true; // дахин дарахгүй

            // Шинэ coins-г дэлгэцэнд харуулах
            if (data.new_coins !== undefined) {
                const coinEl = document.querySelector('.stat-card-value:last-child');
                if (coinEl) coinEl.textContent = data.new_coins;
            }

            // Шинэ xp, level шинэчлэх
            if (data.new_xp !== undefined || data.level_up) {
                updateDashboardStats();
            }
        } else {
            // Аль хэдийн авсан эсвэл хугацаа болоогүй
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

        // Статистик картуудыг шинэчлэх
        const statCards = document.querySelectorAll('.stat-card-value');
        if (statCards.length >= 4) {
            statCards[0].textContent = stats.wins ?? '0';
            statCards[1].textContent = (stats.accuracy ?? 0).toFixed(1) + '%';
            statCards[2].textContent = stats.level ?? '1';
            statCards[3].textContent = stats.coins ?? '0';
        }

        // Sidebar footer-н coins-г шинэчлэх
        const sidebarCoins = document.querySelector('.user-coins span');
        if (sidebarCoins && stats.coins !== undefined) {
            sidebarCoins.textContent = `🪙 ${stats.coins}`;
        }

        // Profile карт доторх XP progress bar шинэчлэх
        if (stats.xp !== undefined && stats.level !== undefined) {
            const xpForNext = stats.level * stats.level * 100;
            const progress = Math.min((stats.xp / xpForNext) * 100, 100);
            const progressBar = document.querySelector('.profile-xp-bar');
            if (progressBar) {
                progressBar.style.width = progress + '%';
            }
            const xpText = document.querySelector('.profile-xp-text');
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
        if (!quests.length) {
            container.innerHTML = '<p style="color:var(--text-secondary);">No quests today.</p>';
            return;
        }
        container.innerHTML = quests.map(q => `
            <div style="margin-bottom:12px;">
                <div style="font-weight:600;">${q.quest_type.replace('_',' ').toUpperCase()}: ${q.current_value}/${q.target_value}</div>
                <div style="background:var(--surface);border-radius:10px;height:8px;overflow:hidden;margin:4px 0;">
                    <div style="width:${q.progress}%;height:100%;background:linear-gradient(90deg, var(--primary), var(--accent));"></div>
                </div>
                <div style="font-size:0.8rem;color:var(--text-secondary);">
                    Reward: 🪙 ${q.reward_coins} + ${q.reward_xp} XP
                    ${q.is_completed && !q.is_claimed ? `<button onclick="claimQuest(${q.id})" class="btn btn-sm btn-primary">Claim</button>` : ''}
                    ${q.is_claimed ? '✅ Claimed' : ''}
                </div>
            </div>
        `).join('');
    } catch(e) { console.error(e); }
}

async function claimQuest(questId) {
    try {
        const data = await apiFetch(`/quests/daily-quests/${questId}/claim`, { method: 'POST' });
        if (data.success) {
            showToast(`Claimed ${data.reward_coins} coins + ${data.reward_xp} XP!`, 'success');
            loadDailyQuests();
            updateDashboardStats();
        }
    } catch(e) { showToast('Failed to claim', 'error'); }
}

document.addEventListener('DOMContentLoaded', () => {
    loadDailyQuests();
    // ... бусад
});