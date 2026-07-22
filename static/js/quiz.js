// =============================================
//  TriviaVerse Quiz Game Logic
// =============================================

// ---------- Helper Functions ----------
function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function getSocket() {
    // socket.io глобал socket байгаа эсэхийг шалгах
    if (typeof socket !== 'undefined') return socket;
    console.error('Socket.IO not initialized');
    return null;
}

// ---------- Game State ----------
let gameState = {
    currentQuestion: 0,
    totalQuestions: 0,
    timeLeft: 20,
    timerInterval: null,
    answers: {},
    score: 0,
    questionStartTime: null,
    endTime: null,
};

function resetGameState() {
    gameState.currentQuestion = 0;
    gameState.totalQuestions = 0;
    gameState.timeLeft = 20;
    if (gameState.timerInterval) {
        clearInterval(gameState.timerInterval);
        gameState.timerInterval = null;
    }
    gameState.answers = {};
    gameState.score = 0;
    gameState.questionStartTime = null;
    gameState.endTime = null;
}

// ---------- Initialization ----------
function initQuiz(roomCode) {
    const sock = getSocket();
    if (!sock) {
        showToast('Connection lost. Please refresh.', 'error');
        return;
    }

    resetGameState();

    // Show quiz container, hide loading
    document.getElementById('quizLoading').style.display = 'none';
    document.getElementById('quizError').style.display = 'none';
    document.getElementById('quizContainer').style.display = 'block';

    // Socket event listeners
    sock.off('question').on('question', (data) => {
        renderQuestion(data);
        startTimer(data.time_limit || 20);
    });

    sock.off('answer_result').on('answer_result', (data) => {
        showAnswerResult(data);
    });

    sock.off('round_results').on('round_results', (data) => {
        showRoundResults(data);
    });

    sock.off('game_over').on('game_over', (data) => {
        showGameOver(data);
    });

    sock.off('error').on('error', (err) => {
        showToast(err.message || 'An error occurred', 'error');
    });

    // Request first question
    sock.emit('request_question', { room_code: roomCode });

    // Keyboard support (1-4 keys)
    document.addEventListener('keydown', handleKeyboard);
}

// ---------- Keyboard Handler ----------
function handleKeyboard(e) {
    const key = parseInt(e.key);
    if (isNaN(key) || key < 1 || key > 4) return;
    const buttons = document.querySelectorAll('.answer-btn');
    if (buttons.length > 0 && !buttons[0].disabled) {
        const targetBtn = buttons[key - 1];
        if (targetBtn) {
            const answerId = parseInt(targetBtn.dataset.id);
            submitAnswer(answerId);
        }
    }
}

// ---------- Question Rendering ----------
function renderQuestion(data) {
    gameState.currentQuestion = data.question_number;
    gameState.totalQuestions = data.total_questions;
    gameState.timeLeft = data.time_limit;

    const container = document.getElementById('quizContainer');
    container.innerHTML = `
        <div class="quiz-layout">
            <div class="quiz-main">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                    <div>
                        <h2 style="font-weight:700; margin-bottom:4px;" id="questionNumber">Question ${data.question_number}/${data.total_questions}</h2>
                        <span style="color:var(--text-secondary);" id="categoryLabel">${escapeHtml(data.category || 'General')}</span>
                    </div>
                    <div class="timer" id="timerDisplay" style="font-size:1.8rem; font-weight:800; color:var(--accent);">
                        ${data.time_limit}s
                    </div>
                </div>
                <div id="questionText" style="font-size:1.3rem; font-weight:600; margin-bottom:32px; line-height:1.6;">
                    ${escapeHtml(data.question_text)}
                </div>
                ${data.image_url ? `<img src="${data.image_url}" alt="Question image" style="max-width:100%;border-radius:12px;margin-bottom:20px;">` : ''}
                <div id="optionsContainer" class="options-grid" style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                    ${data.answers.map((a, idx) => `
                        <button class="option-btn answer-btn" onclick="submitAnswer(${a.id})" data-id="${a.id}">
                            <span style="background:var(--accent);color:white;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.9rem;">${idx + 1}</span>
                            ${escapeHtml(a.answer_text)}
                        </button>
                    `).join('')}
                </div>
                <div style="margin-top:auto; padding-top:24px; display:flex; justify-content:center;">
                    <button id="leaveGameBtn" class="btn btn-ghost" style="background:rgba(255,77,77,0.2); color:#ff4d4d;" onclick="confirmLeave()">
                        🚪 Leave Game
                    </button>
                </div>
            </div>
            <div class="quiz-sidebar">
                <h3 style="font-weight:700; margin-bottom:16px;">Players</h3>
                <div id="playersList" style="margin-bottom:20px;">${renderPlayers(data.players || [])}</div>
                <hr style="border-color:var(--border); margin:16px 0;">
                <h3 style="font-weight:700; margin-bottom:12px;">Scoreboard</h3>
                <div id="scoreboard">${renderScoreboard(data.scores || [])}</div>
            </div>
        </div>
    `;
}

function renderPlayers(players) {
    if (!players.length) return '<p style="color:var(--text-secondary);">No players</p>';
    return players.map(p => `
        <div style="display:flex;align-items:center;gap:8px;padding:8px 0;">
            <span class="player-dot ${p.online ? '' : 'offline'}"></span>
            <img src="${p.avatar || '/static/avatars/default.png'}" style="width:24px;height:24px;border-radius:50%;" onerror="this.src='/static/avatars/default.png'">
            <span style="flex:1;font-size:0.9rem;">${escapeHtml(p.username)}</span>
            <span style="font-weight:600;color:var(--accent);">${p.score || 0}</span>
        </div>
    `).join('');
}

function renderScoreboard(scores) {
    if (!scores.length) return '<p style="color:var(--text-secondary);">Waiting for scores...</p>';
    return scores.slice(0, 5).map((s, i) => `
        <div style="display:flex;align-items:center;gap:8px;padding:6px 0;font-size:0.9rem;">
            <span style="width:20px;font-weight:700;">#${i + 1}</span>
            <span style="flex:1;">${escapeHtml(s.username)}</span>
            <span style="font-weight:700;">${s.score}</span>
        </div>
    `).join('');
}

// ---------- Timer ----------
function startTimer(seconds) {
    clearInterval(gameState.timerInterval);
    gameState.timeLeft = seconds;
    gameState.questionStartTime = Date.now();
    gameState.endTime = gameState.questionStartTime + seconds * 1000;

    const timerDisplay = document.getElementById('timerDisplay');
    if (!timerDisplay) return;

    function update() {
        const now = Date.now();
        const remaining = Math.max(0, gameState.endTime - now);
        gameState.timeLeft = remaining / 1000;

        const displayTime = Math.ceil(gameState.timeLeft);
        timerDisplay.textContent = displayTime + 's';

        // Color changes
        if (gameState.timeLeft <= 5) {
            timerDisplay.style.color = '#ef4444';
        } else if (gameState.timeLeft <= 10) {
            timerDisplay.style.color = '#f59e0b';
        } else {
            timerDisplay.style.color = 'var(--accent)';
        }

        if (remaining <= 0) {
            clearInterval(gameState.timerInterval);
            submitAnswer(null); // Time's up
        } else {
            gameState.timerInterval = requestAnimationFrame(update);
        }
    }

    gameState.timerInterval = requestAnimationFrame(update);
}

// ---------- Answer Submission ----------
function submitAnswer(answerId) {
    if (gameState.timerInterval) {
        cancelAnimationFrame(gameState.timerInterval);
        gameState.timerInterval = null;
    }

    const buttons = document.querySelectorAll('.answer-btn');
    buttons.forEach(btn => {
        btn.disabled = true;
        if (parseInt(btn.dataset.id) === answerId) {
            btn.classList.add('selected');
        }
    });

    const timeTaken = gameState.timeLeft ? (gameState.endTime ? (gameState.endTime - Date.now()) / 1000 : 0) : 0;
    const sock = getSocket();
    if (sock) {
        sock.emit('submit_answer', {
            room_code: window.roomCode,
            answer_id: answerId,
            time_taken: Math.max(0, timeTaken)
        });
    }
}

// ---------- Answer Result Popup ----------
function showAnswerResult(data) {
    const popup = document.createElement('div');
    popup.className = 'answer-popup';
    popup.innerHTML = `
        <div style="font-size:3rem;margin-bottom:8px;">${data.correct ? '✅' : '❌'}</div>
        <div style="font-size:1.5rem;font-weight:800;">${data.correct ? 'Correct!' : 'Wrong!'}</div>
        <div style="color:var(--text-secondary);margin-top:8px;">+${data.score_earned} points</div>
        <div style="margin-top:16px;font-size:0.9rem;">Streak: ${data.streak} 🔥</div>
    `;
    document.body.appendChild(popup);

    // Highlight correct/incorrect buttons
    const buttons = document.querySelectorAll('.answer-btn');
    buttons.forEach(btn => {
        const btnId = parseInt(btn.dataset.id);
        if (btnId === data.correct_answer_id) btn.classList.add('correct');
        else if (btn.classList.contains('selected') && !data.correct) btn.classList.add('incorrect');
    });

    setTimeout(() => {
        popup.style.opacity = '0';
        setTimeout(() => popup.remove(), 300);
    }, 2000);
}

// ---------- Round Results ----------
function showRoundResults(data) {
    const container = document.getElementById('quizContainer');
    container.innerHTML = `
        <div class="quiz-layout">
            <div class="quiz-main" style="text-align:center;">
                <h2 style="margin-bottom:24px;">Round Results</h2>
                <div style="display:flex;flex-direction:column;gap:12px;">
                    ${data.leaderboard.map((p, i) => `
                        <div style="display:flex;align-items:center;gap:16px;padding:16px;background:var(--surface);border-radius:12px;border:${i === 0 ? '2px solid var(--warning)' : '1px solid var(--border)'};">
                            <div style="font-size:1.5rem;font-weight:800;width:40px;">#${i + 1}</div>
                            <img src="${p.avatar || '/static/avatars/default.png'}" style="width:40px;height:40px;border-radius:50%;">
                            <div style="flex:1;text-align:left;">
                                <div style="font-weight:700;">${escapeHtml(p.username)}</div>
                                <div style="font-size:0.85rem;color:var(--text-secondary);">Streak: ${p.streak}</div>
                            </div>
                            <div style="font-size:1.3rem;font-weight:800;color:var(--accent);">${p.score}</div>
                        </div>
                    `).join('')}
                </div>
                <button class="btn btn-primary btn-full" style="margin-top:24px;" onclick="nextQuestion()">Next Question →</button>
            </div>
        </div>
    `;
}

function nextQuestion() {
    const sock = getSocket();
    if (sock) {
        sock.emit('next_question', { room_code: window.roomCode });
    }
}

// ---------- Game Over ----------
function showGameOver(data) {
    const container = document.getElementById('quizContainer');
    container.innerHTML = `
        <div class="quiz-layout">
            <div class="quiz-main" style="text-align:center;">
                <h1 style="font-size:3rem;margin-bottom:8px;">🏆</h1>
                <h2 style="margin-bottom:32px;">Game Over!</h2>

                <div style="display:flex;justify-content:center;gap:32px;margin:32px 0;">
                    ${data.results.slice(0, 3).map((p, i) => `
                        <div style="text-align:center;">
                            <img src="${p.avatar || '/static/avatars/default.png'}" style="width:80px;height:80px;border-radius:50%;border:3px solid var(--accent);">
                            <div style="font-weight:800;margin-top:8px;">${escapeHtml(p.username)}</div>
                            <div style="font-weight:700;color:var(--warning);">${p.score} pts</div>
                            <div style="font-size:0.85rem;">#${i + 1}</div>
                        </div>
                    `).join('')}
                </div>

                <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:32px;">
                    ${data.results.map((p, i) => `
                        <div style="display:flex;align-items:center;gap:12px;padding:12px 16px;background:var(--surface);border-radius:12px;">
                            <span style="font-weight:800;width:30px;">#${i + 1}</span>
                            <span style="flex:1;">${escapeHtml(p.username)}</span>
                            <span style="color:var(--accent);font-weight:700;">${p.score}</span>
                            <span style="font-size:0.85rem;color:var(--text-secondary);">${p.correct}/${data.total_questions}</span>
                        </div>
                    `).join('')}
                </div>

                <a href="/rooms/lobby" class="btn btn-primary btn-lg">Back to Lobby</a>
            </div>
        </div>
    `;

    createConfetti();
}

function createConfetti() {
    const colors = ['#FFD700', '#00D4FF', '#5865F2', '#EC4899', '#22C55E'];
    for (let i = 0; i < 100; i++) {
        const confetti = document.createElement('div');
        confetti.style.cssText = `
            position:fixed;
            width:10px;height:10px;
            background:${colors[Math.floor(Math.random() * colors.length)]};
            left:${Math.random() * 100}%;
            top:-10px;
            border-radius:${Math.random() > 0.5 ? '50%' : '0'};
            animation:confettiFall ${3 + Math.random() * 4}s linear forwards;
            z-index:9999;
            pointer-events:none;
        `;
        document.body.appendChild(confetti);
        setTimeout(() => confetti.remove(), 7000);
    }
}

// ---------- Leave Game ----------
window.confirmLeave = function () {
    if (confirm('Are you sure you want to leave the game?')) {
        const sock = getSocket();
        if (sock) {
            sock.emit('leave_room', { room_code: window.roomCode });
        }
        window.location.href = '/rooms/lobby';
    }
};

// ---------- Animations & Style ----------
const quizStyles = document.createElement('style');
quizStyles.textContent = `
    @keyframes confettiFall {
        to { transform: translateY(100vh) rotate(720deg); opacity:0; }
    }
    @keyframes scaleIn {
        from { transform:translate(-50%,-50%) scale(0.8); opacity:0; }
        to { transform:translate(-50%,-50%) scale(1); opacity:1; }
    }
    .answer-popup {
        position:fixed; top:50%; left:50%;
        transform:translate(-50%,-50%);
        background: var(--glass-bg, rgba(255,255,255,0.1));
        backdrop-filter: blur(16px);
        padding:32px 48px;
        border-radius:24px;
        border:1px solid var(--border);
        text-align:center;
        z-index:100;
        animation:scaleIn 0.3s ease;
    }
    .option-btn.correct {
        background: #22c55e !important;
        border-color: #22c55e !important;
        color: white !important;
    }
    .option-btn.incorrect {
        background: #ef4444 !important;
        border-color: #ef4444 !important;
        color: white !important;
    }
    .option-btn.selected {
        border-color: var(--accent);
    }
`;
document.head.appendChild(quizStyles);

// ---------- Error Handling ----------
window.addEventListener('error', (e) => {
    console.error('Quiz error:', e.error);
    if (document.getElementById('quizLoading')) {
        document.getElementById('quizLoading').style.display = 'none';
    }
    if (document.getElementById('quizError')) {
        document.getElementById('quizError').style.display = 'block';
    }
});

// Auto-init if roomCode is set
if (window.roomCode) {
    document.addEventListener('DOMContentLoaded', () => {
        initQuiz(window.roomCode);
    });
}

socket.on('level_up', (data) => {
    if (data.user_id === window.currentUserId) {
        showToast(`🎉 Level Up! You are now level ${data.new_level}!`, 'success');
    }
});

// quiz.js дотор тоглогчийн жагсаалтад admin товч нэмэх
function renderPlayers(players) {
    let adminButtons = '';
    if (window.currentUserRole && ['admin', 'moderator', 'owner'].includes(window.currentUserRole)) {
        adminButtons = `<button onclick="skipQuestion()">⏭️ Skip</button>
                        <button onclick="kickPlayer('${p.user_id}')">👢 Kick</button>`;
    }
}