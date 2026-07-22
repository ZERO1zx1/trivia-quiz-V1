let hoverTimeout;
let currentTargetUserId = null;

document.addEventListener('mouseover', (e) => {
    const target = e.target.closest('[data-user-id]');
    if (!target) return;
    const userId = target.dataset.userId;
    if (userId === window.currentUserId) return;

    clearTimeout(hoverTimeout);
    hoverTimeout = setTimeout(() => showHoverCard(userId, e), 300);
});

document.addEventListener('mouseout', (e) => {
    if (e.target.closest('[data-user-id]')) {
        clearTimeout(hoverTimeout);
        // hideHoverCard();
    }
});

async function showHoverCard(userId, event) {
    currentTargetUserId = userId;
    const resp = await fetch(`/api/user/hover-info/${userId}`);
    const user = await resp.json();

    document.getElementById('hcAvatar').src = user.avatar_url;
    document.getElementById('hcName').textContent = user.display_name || user.username;
    document.getElementById('hcBadge').innerHTML = user.role !== 'user' ? `<span style="color:${getRoleColor(user.role)}">${user.role.toUpperCase()}</span>` : '';
    document.getElementById('hcViews').textContent = user.profile_views;
    document.getElementById('hcRespect').textContent = user.respect_count;
    document.getElementById('hcWinrate').textContent = user.accuracy.toFixed(1) + '%';

    const card = document.getElementById('hoverCard');
    card.classList.remove('hidden');
    // Position
    let left = event.clientX + 15;
    let top = event.clientY - 100;
    if (left + 300 > window.innerWidth) left = event.clientX - 310;
    if (top < 10) top = 10;
    card.style.left = left + 'px';
    card.style.top = top + 'px';

    // Record view
    fetch(`/api/user/profile/view/${userId}`, { method: 'POST' });
}

function hideHoverCard() {
    document.getElementById('hoverCard').classList.add('hidden');
    currentTargetUserId = null;
}

// Actions
function challengeUser() {
    if (!currentTargetUserId) return;
    fetch(`/api/user/challenge/${currentTargetUserId}`, { method: 'POST' })
        .then(r => r.json())
        .then(d => showToast(d.message || 'Challenge sent!', d.success ? 'success' : 'warning'));
    hideHoverCard();
}

function sendGift() {
    if (!currentTargetUserId) return;
    const gift = prompt('Choose gift: coffee (10), crown (500), xp_boost (200)');
    if (!gift) return;
    apiFetch(`/api/user/gift/${currentTargetUserId}`, {
        method: 'POST',
        body: JSON.stringify({ gift_type: gift })
    }).then(d => showToast(d.message || 'Gift sent!', d.success ? 'success' : 'error'));
    hideHoverCard();
}

function giveRespect() {
    if (!currentTargetUserId) return;
    fetch(`/api/user/respect/${currentTargetUserId}`, { method: 'POST' })
        .then(r => r.json())
        .then(d => showToast(d.message || 'Respect given!', 'success'));
    hideHoverCard();
}