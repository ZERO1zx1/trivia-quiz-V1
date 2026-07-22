// =============================================
//  TriviaVerse Solo Quiz Logic (Secure)
// =============================================

let currentQuestion = 0;
let questions = [];
let score = 0;
let timerInterval = null;
let timeLeft = 20;
let userAnswers = [];

// Fisher-Yates Shuffle
function shuffleArray(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
}

// Асуултуудыг татах
async function loadQuestions() {
    try {
        const resp = await fetch('/quiz/questions');
        const allQuestions = await resp.json();
        questions = allQuestions.slice(0, window.totalQuestions || 10);
        if (questions.length > 0) {
            // Хариултуудыг холих
            questions.forEach(q => {
                q.answers = shuffleArray(q.answers);
            });
            renderQuestion();
        } else {
            document.getElementById('quizContainer').innerHTML = `
                <div style="text-align:center; padding:48px;">
                    <h2>No questions available</h2>
                    <a href="/dashboard" class="btn btn-primary">Back to Dashboard</a>
                </div>`;
        }
    } catch (e) {
        document.getElementById('quizContainer').innerHTML = `
            <div style="text-align:center; padding:48px;">
                <h2>Failed to load questions</h2>
                <button onclick="location.reload()" class="btn btn-primary">Retry</button>
            </div>`;
    }
}

function renderQuestion() {
    if (currentQuestion >= questions.length) {
        endGame();
        return;
    }

    const q = questions[currentQuestion];
    document.getElementById('questionNumber').textContent = `Question ${currentQuestion + 1}/${questions.length}`;
    document.getElementById('questionText').textContent = q.question_text;
    document.getElementById('categoryLabel').textContent = q.category || 'General';

    const optionsContainer = document.getElementById('optionsContainer');
    optionsContainer.innerHTML = q.answers.map((a, idx) => `
        <button class="option-btn answer-btn" onclick="submitAnswer(${a.id})" data-id="${a.id}">
            <span style="background:var(--accent);color:white;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.9rem;">${idx + 1}</span>
            ${a.answer_text}
        </button>
    `).join('');

    startTimer(q.time_limit || 20);
}

function startTimer(seconds) {
    timeLeft = seconds;
    clearInterval(timerInterval);
    const timerDisplay = document.getElementById('timerDisplay');
    timerDisplay.textContent = timeLeft + 's';
    timerDisplay.style.color = 'var(--accent)';

    timerInterval = setInterval(() => {
        timeLeft--;
        timerDisplay.textContent = timeLeft + 's';
        if (timeLeft <= 5) timerDisplay.style.color = '#ef4444';
        else if (timeLeft <= 10) timerDisplay.style.color = '#f59e0b';

        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            submitAnswer(-1); // time's up
        }
    }, 1000);
}

async function submitAnswer(answerId) {
    clearInterval(timerInterval);
    const buttons = document.querySelectorAll('.answer-btn');
    buttons.forEach(btn => btn.disabled = true);

    if (answerId === -1) {
        // Хугацаа дууссан
        userAnswers.push({ question_id: questions[currentQuestion].id, correct: false, time_taken: 20 });
        currentQuestion++;
        setTimeout(() => renderQuestion(), 500);
        return;
    }

    // Сервер лүү шалгуулах
    try {
        const resp = await apiFetch('/quiz/solo/check_answer', {
            method: 'POST',
            body: JSON.stringify({
                question_id: questions[currentQuestion].id,
                answer_id: answerId
            })
        });
        const { correct, correct_answer_id } = resp;

        // Товчлууруудыг будна
        buttons.forEach(btn => {
            const btnId = parseInt(btn.dataset.id);
            if (btnId === correct_answer_id) btn.classList.add('correct');
            else if (btnId === answerId && !correct) btn.classList.add('incorrect');
            if (btnId === answerId) btn.classList.add('selected');
        });

        if (correct) {
            score += 100;
            document.getElementById('scoreDisplay').textContent = score;
        }

        userAnswers.push({
            question_id: questions[currentQuestion].id,
            correct: correct,
            time_taken: 20 - timeLeft
        });

        // Popup
        const popup = document.createElement('div');
        popup.className = 'answer-popup';
        popup.innerHTML = `<div style="font-size:3rem;">${correct ? '✅' : '❌'}</div><div>${correct ? 'Correct!' : 'Wrong!'}</div>`;
        document.body.appendChild(popup);
        setTimeout(() => popup.remove(), 1000);

        // Дараагийн асуулт
        setTimeout(() => {
            currentQuestion++;
            renderQuestion();
        }, 1500);
    } catch (e) {
        // Алдаа гарвал цааш нь үргэлжлүүл
        currentQuestion++;
        renderQuestion();
    }
}

async function endGame() {
    const correctCount = userAnswers.filter(a => a.correct).length;
    try {
        await apiFetch('/quiz/solo/submit', {
            method: 'POST',
            body: JSON.stringify({
                room_code: window.roomCode,
                score: score,
                correct: correctCount,
                total: questions.length,
                answers: userAnswers
            })
        });
    } catch (e) { /* чимээгүй */ }

    document.getElementById('quizContainer').innerHTML = `
        <div style="text-align:center; padding:48px;">
            <h1>🏆 Practice Complete!</h1>
            <div style="font-size:3rem; font-weight:800; color:var(--accent);">${score} Points</div>
            <div style="margin-top:16px; color:var(--text-secondary);">
                Correct: ${correctCount}/${questions.length}
            </div>
            <a href="/dashboard" class="btn btn-primary btn-lg" style="margin-top:24px;">Back to Dashboard</a>
        </div>
    `;
}

document.addEventListener('DOMContentLoaded', loadQuestions);