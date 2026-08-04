/**
 * TriviaVerse Quiz Engine
 * Version 3.0 - Full Game Logic
 */

const QuizEngine = {
    // Game State
    state: {
        currentQuestion: null,
        questionIndex: 0,
        totalQuestions: 0,
        score: 0,
        combo: 0,
        maxCombo: 0,
        correctAnswers: 0,
        wrongAnswers: 0,
        startTime: null,
        timer: null,
        timeLeft: 0,
        timePerQuestion: 30,
        isLocked: false,
        difficulty: 'medium',
        category: 'general',
        mode: 'classic',
        bonusMultiplier: 1,
        lifelines: {
            fiftyFifty: true,
            timeBonus: true,
            skip: false
        }
    },

    // Quiz Types
    modes: {
        classic: { timePerQuestion: 30, scoreMultiplier: 1, category: 'general' },
        speed: { timePerQuestion: 10, scoreMultiplier: 2, category: 'general' },
        expert: { timePerQuestion: 45, scoreMultiplier: 3, category: 'mixed', hardOnly: true },
        duel: { timePerQuestion: 15, scoreMultiplier: 1.5, category: 'general' },
        daily: { timePerQuestion: 20, scoreMultiplier: 1.5, category: 'general', isDaily: true },
        tournament: { timePerQuestion: 20, scoreMultiplier: 2, category: 'general' },
        voice: { timePerQuestion: 30, scoreMultiplier: 1.5, type: 'voice' },
        image: { timePerQuestion: 25, scoreMultiplier: 1.5, type: 'image' },
        video: { timePerQuestion: 30, scoreMultiplier: 2, type: 'video' },
        music: { timePerQuestion: 30, scoreMultiplier: 1.5, type: 'music' },
        puzzle: { timePerQuestion: 60, scoreMultiplier: 3, type: 'puzzle' }
    },

    // Initialize quiz
    init(config = {}) {
        this.state.mode = config.mode || 'classic';
        this.state.category = config.category || 'general';
        this.state.difficulty = config.difficulty || 'medium';

        const modeConfig = this.modes[this.state.mode] || this.modes.classic;
        this.state.timePerQuestion = config.timePerQuestion || modeConfig.timePerQuestion;
        this.state.bonusMultiplier = modeConfig.scoreMultiplier;

        this.state.startTime = Date.now();
        this.state.totalQuestions = config.totalQuestions || 10;
    },

    // Load question
    async loadQuestion() {
        try {
            const response = await fetch('/api/question', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mode: this.state.mode,
                    category: this.state.category,
                    difficulty: this.state.difficulty,
                    question_index: this.state.questionIndex
                })
            });
            const data = await response.json();
            this.state.currentQuestion = data;
            return data;
        } catch (error) {
            console.error('Failed to load question:', error);
            return null;
        }
    },

    // Answer question
    submitAnswer(answer, timeRemaining) {
        if (this.state.isLocked) return;
        this.state.isLocked = true;

        const isCorrect = answer === this.state.currentQuestion.correct_answer;
        const baseScore = 100;
        const timeBonus = Math.floor(timeRemaining * 5);
        const comboBonus = Math.floor(this.state.combo * 10);
        const totalScore = Math.floor(
            (baseScore + timeBonus + comboBonus) * this.state.bonusMultiplier
        );

        if (isCorrect) {
            this.state.score += totalScore;
            this.state.combo++;
            this.state.correctAnswers++;
            this.state.maxCombo = Math.max(this.state.maxCombo, this.state.combo);
            if (this.state.audioEnabled) TriviaVerse.audio.play('correct');
        } else {
            this.state.wrongAnswers++;
            this.state.combo = 0;
            if (this.state.audioEnabled) TriviaVerse.audio.play('wrong');
        }

        this.state.questionIndex++;
        this.state.isLocked = false;

        return {
            correct: isCorrect,
            score: totalScore,
            combo: this.state.combo,
            totalScore: this.state.score,
            timeBonus,
            comboBonus,
            progress: {
                current: this.state.questionIndex,
                total: this.state.totalQuestions,
                accuracy: this.calculateAccuracy()
            }
        };
    },

    // Calculate accuracy
    calculateAccuracy() {
        const total = this.state.correctAnswers + this.state.wrongAnswers;
        if (total === 0) return 0;
        return (this.state.correctAnswers / total) * 100;
    },

    // Timer management
    startTimer(callback) {
        this.state.timeLeft = this.state.timePerQuestion;
        this.state.timer = setInterval(() => {
            this.state.timeLeft--;
            if (callback) callback(this.state.timeLeft);

            if (this.state.timeLeft <= 0) {
                this.stopTimer();
                if (callback) callback(0);
                this.submitAnswer(null, 0); // Time out
            }
        }, 1000);
    },

    stopTimer() {
        if (this.state.timer) {
            clearInterval(this.state.timer);
            this.state.timer = null;
        }
    },

    // Lifelines
    useFiftyFifty() {
        if (!this.state.lifelines.fiftyFifty) return false;
        this.state.lifelines.fiftyFifty = false;

        const question = this.state.currentQuestion;
        const wrongOptions = question.options.filter(o => o !== question.correct_answer);
        const removed = wrongOptions.sort(() => Math.random() - 0.5).slice(0, 2);

        return {
            removed: removed,
            remaining: question.options.filter(o => !removed.includes(o))
        };
    },

    useTimeBonus() {
        if (!this.state.lifelines.timeBonus) return false;
        this.state.lifelines.timeBonus = false;
        this.state.timeLeft += 15;
        return true;
    },

    // Get final results
    getResults() {
        const duration = Math.floor((Date.now() - this.state.startTime) / 1000);
        return {
            mode: this.state.mode,
            category: this.state.category,
            difficulty: this.state.difficulty,
            score: this.state.score,
            correctAnswers: this.state.correctAnswers,
            wrongAnswers: this.state.wrongAnswers,
            accuracy: this.calculateAccuracy(),
            maxCombo: this.state.maxCombo,
            duration: duration,
            questionsAnswered: this.state.questionIndex,
            lifelinesUsed: {
                fiftyFifty: !this.state.lifelines.fiftyFifty,
                timeBonus: !this.state.lifelines.timeBonus
            }
        };
    },

    // Reset
    reset() {
        this.stopTimer();
        this.state = {
            currentQuestion: null,
            questionIndex: 0,
            totalQuestions: 0,
            score: 0,
            combo: 0,
            maxCombo: 0,
            correctAnswers: 0,
            wrongAnswers: 0,
            startTime: null,
            timer: null,
            timeLeft: 0,
            timePerQuestion: 30,
            isLocked: false,
            difficulty: 'medium',
            category: 'general',
            mode: 'classic',
            bonusMultiplier: 1,
            lifelines: { fiftyFifty: true, timeBonus: true, skip: false }
        };
    }
};
