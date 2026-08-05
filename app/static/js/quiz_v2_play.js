/* =============================================
   Trivia Quiz V2 — Play Page Logic
   Timer, Scoring, Streak, Results, Supabase
   ============================================= */

(function() {
    'use strict';

    const config = window.quizV2Config || {};
    const t = config.translations || {};
    const T = (key) => t[key] || key;

    // Game state
    let questions = [];
    let currentQuestionIndex = 0;
    let score = 0;
    let streak = 0;
    let maxStreak = 0;
    let correctCount = 0;
    let wrongCount = 0;
    let timerInterval = null;
    let timeLeft = config.timerSeconds || 20;
    let totalTimeSpent = 0;
    let isAnswering = false;

    // DOM elements
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const emptyState = document.getElementById('emptyState');
    const questionArea = document.getElementById('questionArea');
    const resultsArea = document.getElementById('resultsArea');
    const quizContainer = document.getElementById('quizContainer');

    // ============ INITIALIZATION ============
    async function init() {
        try {
            showLoading();
            questions = await loadQuestions();

            if (questions.length === 0) {
                hideLoading();
                showEmpty();
                return;
            }

            // Shuffle answers for each question
            questions.forEach(q => {
                q.answers = shuffleArray(q.answers);
            });

            // Update question count
            config.totalQuestions = questions.length;

            hideLoading();
            showQuestionArea();
            renderQuestion();
        } catch (e) {
            console.error('Quiz init error:', e);
            hideLoading();
            showError();
        }
    }

    // ============ QUESTION LOADING ============
    async function loadQuestions() {
        const params = new URLSearchParams({
            category_id: config.categoryId,
            limit: config.totalQuestions,
            difficulty: 'mixed'
        });

        const resp = await fetch(`/quiz/v2/api/questions?${params}`);
        if (!resp.ok) throw new Error('Failed to load questions');
        return await resp.json();
    }

    // ============ RENDER QUESTION ============
    function renderQuestion() {
        if (currentQuestionIndex >= questions.length) {
            endGame();
            return;
        }

        isAnswering = false;
        const q = questions[currentQuestionIndex];

        // Update counter
        document.getElementById('questionCounter').textContent =
            `${T('question')} ${currentQuestionIndex + 1} ${T('of')} ${questions.length}`;

        // Update difficulty badge
        const diffBadge = document.getElementById('difficultyBadge');
        diffBadge.textContent = T(q.difficulty || 'medium');

        // Update progress bar
        const progress = ((currentQuestionIndex) / questions.length) * 100;
        document.getElementById('progressFill').style.width = `${progress}%`;

        // Set question text
        document.getElementById('questionText').textContent = q.question_text;

        // Render options
        const optionsContainer = document.getElementById('optionsContainer');
        const letters = ['A', 'B', 'C', 'D'];
        optionsContainer.innerHTML = q.answers.map((a, idx) => `
            <button class="v2-option-btn" data-id="${a.id}" data-index="${idx}" onclick="quizV2Play.selectAnswer(${a.id})">
                <span class="option-letter">${letters[idx]}</span>
                <span class="option-text">${a.text}</span>
            </button>
        `).join('');

        // Start timer if enabled
        if (config.timerMode === 'on') {
            startTimer();
        } else {
            const timerEl = document.getElementById('timerArea');
            if (timerEl) timerEl.style.display = 'none';
        }
    }

    // ============ TIMER ============
    function startTimer() {
        timeLeft = config.timerSeconds;
        clearInterval(timerInterval);

        const timerCircle = document.getElementById('timerCircle');
        const timerText = document.getElementById('timerText');
        const circumference = 339.292; // 2 * PI * 54

        timerText.textContent = timeLeft;
        timerCircle.style.strokeDashoffset = '0';
        timerCircle.style.stroke = 'var(--primary)';

        timerInterval = setInterval(() => {
            timeLeft--;
            timerText.textContent = timeLeft;

            // Update circle
            const offset = circumference - (timeLeft / config.timerSeconds) * circumference;
            timerCircle.style.strokeDashoffset = offset;

            // Color changes
            if (timeLeft <= 5) {
                timerCircle.style.stroke = 'var(--danger)';
                timerText.style.color = 'var(--danger)';
            } else if (timeLeft <= 10) {
                timerCircle.style.stroke = 'var(--accent)';
                timerText.style.color = 'var(--accent)';
            } else {
                timerCircle.style.stroke = 'var(--primary)';
                timerText.style.color = 'var(--text-primary)';
            }

            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                quizV2Play.selectAnswer(-1); // Time's up
            }
        }, 1000);
    }

    function stopTimer() {
        clearInterval(timerInterval);
    }

    // ============ ANSWER SELECTION ============
    async function selectAnswer(answerId) {
        if (isAnswering) return;
        isAnswering = true;
        stopTimer();

        const q = questions[currentQuestionIndex];
        const timeTaken = config.timerSeconds - timeLeft;
        totalTimeSpent += timeTaken;

        // Disable all buttons
        const buttons = document.querySelectorAll('.v2-option-btn');
        buttons.forEach(btn => btn.classList.add('disabled'));

        // Check answer
        try {
            const resp = await fetch('/quiz/v2/api/check_answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question_id: q.id,
                    answer_id: answerId,
                    time_taken: timeTaken
                })
            });

            const result = await resp.json();

            // Highlight buttons
            buttons.forEach(btn => {
                const btnId = parseInt(btn.dataset.id);
                if (btnId === result.correct_answer_id) {
                    btn.classList.add('correct');
                } else if (btnId === answerId && !result.correct) {
                    btn.classList.add('incorrect');
                }
            });

            if (result.correct) {
                correctCount++;
                streak++;
                if (streak > maxStreak) maxStreak = streak;

                // Calculate score: base + time bonus + streak bonus
                let points = 100;
                if (config.timerMode === 'on') {
                    points += timeLeft * 5; // Time bonus
                }
                points += (streak - 1) * 20; // Streak bonus
                score += points;

                // Update displays
                document.getElementById('scoreDisplay').textContent = score;
                document.getElementById('streakDisplay').textContent = streak;

                showFeedback(true);
            } else {
                wrongCount++;
                streak = 0;
                document.getElementById('streakDisplay').textContent = streak;
                showFeedback(false);
            }

            // Next question after delay
            setTimeout(() => {
                hideFeedback();
                currentQuestionIndex++;
                renderQuestion();
            }, 1500);

        } catch (e) {
            console.error('Check answer error:', e);
            // Continue on error
            currentQuestionIndex++;
            renderQuestion();
        }
    }

    // ============ FEEDBACK ============
    function showFeedback(isCorrect) {
        const overlay = document.getElementById('feedbackOverlay');
        const content = document.getElementById('feedbackContent');
        content.innerHTML = `
            <span class="feedback-icon">${isCorrect ? '✅' : '❌'}</span>
            <span class="feedback-text ${isCorrect ? 'correct-text' : 'wrong-text'}">
                ${isCorrect ? T('correct') : T('wrong')}
            </span>
        `;
        overlay.style.display = 'flex';
    }

    function hideFeedback() {
        document.getElementById('feedbackOverlay').style.display = 'none';
    }

    // ============ END GAME ============
    async function endGame() {
        stopTimer();
        questionArea.style.display = 'none';

        // Save score to Supabase
        try {
            await fetch('/quiz/v2/api/save_score', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    category_id: config.categoryId,
                    total_questions: questions.length,
                    correct_answers: correctCount,
                    wrong_answers: wrongCount,
                    score: score,
                    max_streak: maxStreak,
                    time_spent_seconds: totalTimeSpent,
                    timer_mode: config.timerMode
                })
            });
        } catch (e) {
            console.error('Save score error:', e);
        }

        // Show results
        const accuracy = questions.length > 0 ? Math.round((correctCount / questions.length) * 100) : 0;

        document.getElementById('finalScore').textContent = score;
        document.getElementById('correctCount').textContent = correctCount;
        document.getElementById('wrongCount').textContent = wrongCount;
        document.getElementById('maxStreak').textContent = maxStreak;
        document.getElementById('accuracy').textContent = accuracy + '%';

        // Icon based on performance
        let icon = '🏆';
        if (accuracy < 50) icon = '💪';
        else if (accuracy < 70) icon = '👍';
        else if (accuracy < 90) icon = '🎉';

        document.getElementById('resultsIcon').textContent = icon;

        resultsArea.style.display = 'block';

        // Play again button
        document.getElementById('playAgainBtn').addEventListener('click', () => {
            window.location.reload();
        });
    }

    // ============ STATE MANAGEMENT ============
    function showLoading() {
        loadingState.style.display = 'block';
    }

    function hideLoading() {
        loadingState.style.display = 'none';
    }

    function showError() {
        errorState.style.display = 'block';
    }

    function showEmpty() {
        emptyState.style.display = 'block';
    }

    function showQuestionArea() {
        questionArea.style.display = 'block';
    }

    // ============ UTILITIES ============
    function shuffleArray(arr) {
        const a = [...arr];
        for (let i = a.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [a[i], a[j]] = [a[j], a[i]];
        }
        return a;
    }

    // Quit button
    const quitBtn = document.getElementById('quitBtn');
    if (quitBtn) {
        quitBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to quit?')) {
                window.location.href = '/quiz/v2';
            }
        });
    }

    // ============ PUBLIC API ============
    window.quizV2Play = {
        selectAnswer: selectAnswer
    };

    // ============ START ============
    document.addEventListener('DOMContentLoaded', init);
})();
