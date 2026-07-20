let currentQuestion = 0;
let questions = [];
let score = 0;
let timerInterval = null;
let timeLeft = 20;
let userAnswers = [];

// Асуултуудыг татах
async function loadQuestions() {
    const resp = await fetch('/quiz/questions');
    const allQuestions = await resp.json();
    questions = allQuestions.slice(0, window.totalQuestions);
    if (questions.length > 0) {
        renderQuestion();
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
        <button class="option-btn answer-btn" onclick="submitAnswer(${idx})" data-id="${idx}">
            <span style="background:var(--accent);color:white;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.9rem;">${idx+1}</span>
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

async function submitAnswer(answerIdx) {
    clearInterval(timerInterval);
    const buttons = document.querySelectorAll('.answer-btn');
    buttons.forEach(btn => btn.disabled = true);

    const q = questions[currentQuestion];
    const correctIdx = q.answers.findIndex(a => a.is_correct);
    const isCorrect = (answerIdx === correctIdx);

    // Highlight correct/incorrect
    buttons.forEach(btn => {
        const idx = parseInt(btn.dataset.id);
        if (idx === correctIdx) btn.classList.add('correct');
        else if (idx === answerIdx && !isCorrect) btn.classList.add('incorrect');
        if (idx === answerIdx) btn.classList.add('selected');
    });

    if (isCorrect) {
        score += 100;
        document.getElementById('scoreDisplay').textContent = score;
    }

    userAnswers.push({
        question_id: q.id,
        correct: isCorrect,
        time_taken: 20 - timeLeft
    });

    // Show result popup briefly
    const popup = document.createElement('div');
    popup.className = 'answer-popup';
    popup.innerHTML = `<div style="font-size:3rem;">${isCorrect ? '✅' : '❌'}</div><div>${isCorrect ? 'Correct!' : 'Wrong!'}</div>`;
    document.body.appendChild(popup);
    setTimeout(() => popup.remove(), 1000);

    // Next question after 1.5 seconds
    setTimeout(() => {
        currentQuestion++;
        renderQuestion();
    }, 1500);
}

async function endGame() {
    const correctCount = userAnswers.filter(a => a.correct).length;
    // Save results via API
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

    document.getElementById('quizContainer').innerHTML = `
        <div style="text-align:center; padding:48px;">
            <h1>🏆 Practice Complete!</h1>
            <div style="font-size:3rem; font-weight:800;">${score} Points</div>
            <p>Correct: ${correctCount}/${questions.length}</p>
            <a href="/dashboard" class="btn btn-primary btn-lg">Back to Dashboard</a>
        </div>
    `;
}

document.addEventListener('DOMContentLoaded', loadQuestions);