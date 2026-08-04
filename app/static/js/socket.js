// =============================================
//  TriviaVerse Socket.IO Client
// =============================================

let socket = null;
let currentRoom = null;

function initSocket() {
    if (socket) {
        socket.disconnect();
        socket = null;
    }

    socket = io({
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        timeout: 20000
    });

    // ---------- Core Events ----------
    socket.on('connect', () => {
        console.log('✅ Connected to TriviaVerse');
        document.body.classList.remove('socket-disconnected');
    });

    socket.on('disconnect', (reason) => {
        console.warn('⚠️ Disconnected:', reason);
        document.body.classList.add('socket-disconnected');
        if (reason === 'io server disconnect') {
            socket.connect();
        }
        showToast('Connection lost. Reconnecting...', 'warning');
    });

    socket.on('reconnect', () => {
        console.log('🔁 Reconnected');
        showToast('Reconnected!', 'success');
        if (currentRoom) {
            socket.emit('join_room', { room_code: currentRoom });
        }
    });

    socket.on('reconnect_error', (error) => {
        console.error('Reconnect error:', error);
        showToast('Could not reconnect. Please refresh.', 'error');
    });

    // ---------- Application Events ----------
    socket.on('error', (data) => {
        console.error('Server error:', data);
        showToast(data.message || 'An error occurred', 'error');
    });

    socket.on('player_joined', (data) => {
        updatePlayerList(data.players);
        showToast(`${data.player?.username || 'A player'} joined`, 'info');
    });

    socket.on('player_left', (data) => {
        updatePlayerList(data.players);
    });

    socket.on('player_ready_changed', (data) => {
        updatePlayerList(data.players);
        const btn = document.getElementById('readyBtn');
        if (btn && data.user_id === window.currentUserId) {
            btn.textContent = data.is_ready ? '✓ Ready' : 'Ready Up';
            btn.classList.toggle('btn-success', data.is_ready);
        }
    });

    socket.on('chat_message', (data) => {
        addChatMessage(data);
    });

    socket.on('game_started', (data) => {
        if (data.redirect_url) {
            window.location.href = data.redirect_url;
        } else if (currentRoom) {
            window.location.href = `/quiz/play/${currentRoom}`;
        }
    });

    socket.on('kicked_from_room', () => {
        showToast('You were kicked from the room', 'error');
        setTimeout(() => {
            window.location.href = '/rooms/lobby';
        }, 2000);
    });
}

// ==================================
//  Room & Game Actions
// ==================================

function joinRoomSocket(roomCode) {
    currentRoom = roomCode;
    if (socket && socket.connected) {
        socket.emit('join_room', { room_code: roomCode });
    } else {
        if (!socket) initSocket();
        socket.once('connect', () => {
            socket.emit('join_room', { room_code: roomCode });
        });
    }
}

function toggleReady(roomCode) {
    if (socket) {
        socket.emit('toggle_ready', { room_code: roomCode });
    }
}

function sendChat(roomCode, message) {
    if (socket && message.trim()) {
        socket.emit('send_chat', {
            room_code: roomCode,
            message: message.trim()
        });
    }
}

function startGame(roomCode) {
    if (socket) {
        socket.emit('start_game_lobby', { room_code: roomCode });
    }
}

// ==================================
//  UI Update Functions
// ==================================

function updatePlayerList(players) {
    const container = document.getElementById('playerList');
    if (!container) return;

    container.innerHTML = players.map(p => `
        <div class="player-card ${p.is_ready ? 'ready' : ''} ${p.user_id === window.hostId ? 'host' : ''}">
            ${p.user_id === window.hostId ? '<span class="host-badge">HOST</span>' : ''}
            <img src="${p.avatar || '/static/avatars/default.png'}" alt="${p.username}" onerror="this.src='/static/avatars/default.png'">
            <div class="player-name">${escapeHtml(p.username)}</div>
            <div class="ready-indicator ${p.is_ready ? 'ready' : ''}"></div>
        </div>
    `).join('');
}

function addChatMessage(data) {
    const container = document.getElementById('chatMessages');
    if (!container) return;

    const isSelf = data.user_id === window.currentUserId;
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${isSelf ? 'chat-message-self' : ''}`;

    const avatarUrl = data.avatar || '/static/avatars/default.png';
    const safeUsername = escapeHtml(data.username);
    const safeMessage = escapeHtml(data.message);

    messageDiv.innerHTML = `
        <img src="${avatarUrl}" alt="${safeUsername}" onerror="this.src='/static/avatars/default.png'">
        <div class="chat-message-content">
            <div class="chat-message-username">${safeUsername}</div>
            <div class="chat-message-text">${safeMessage}</div>
        </div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

// ==================================
//  Escape HTML utility
// ==================================
function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ==================================
//  Initialization
// ==================================
if (document.querySelector('.app-layout')) {
    initSocket();
}