/**
 * Simulador Examen Complexivo - Derecho 2026
 * Main application logic
 */

// ============================================
// Configuration
// ============================================

const SIMULATOR_TOTAL = 50;

// Proportional distribution of 50 questions by topic
// Based on: Const=375, Procesal=225, Penal=270, Civil=270, Admin=150, IntroFilo=60, Laboral=150
const TOPIC_DISTRIBUTION = {
    "Derecho Constitucional": 13,
    "Derecho Procesal": 8,
    "Derecho Penal": 9,
    "Derecho Civil": 9,
    "Derecho Administrativo": 5,
    "Introducción y Filosofía del Derecho": 2,
    "Derecho Laboral": 5
};
// Sum = 51, adjust one down: Constitucional 13->12 to get 50
// Actually let's keep it at 50: 13+8+9+9+5+2+4=50
// Adjust Laboral from 5 to 4
const TOPIC_DISTRIBUTION_FINAL = {
    "Derecho Constitucional": 13,
    "Derecho Procesal": 8,
    "Derecho Penal": 9,
    "Derecho Civil": 9,
    "Derecho Administrativo": 5,
    "Introducción y Filosofía del Derecho": 2,
    "Derecho Laboral": 4
};

const TOPIC_COLORS = {
    "Derecho Constitucional": "#f59e0b",
    "Derecho Procesal": "#3b82f6",
    "Derecho Penal": "#ef4444",
    "Derecho Civil": "#10b981",
    "Derecho Administrativo": "#8b5cf6",
    "Introducción y Filosofía del Derecho": "#ec4899",
    "Derecho Laboral": "#06b6d4"
};

const TOPIC_SHORT = {
    "Derecho Constitucional": "Constitucional",
    "Derecho Procesal": "Procesal",
    "Derecho Penal": "Penal",
    "Derecho Civil": "Civil",
    "Derecho Administrativo": "Administrativo",
    "Introducción y Filosofía del Derecho": "Intro/Filosofía",
    "Derecho Laboral": "Laboral"
};

// ============================================
// State
// ============================================

let state = {
    mode: null,           // 'simulator' or 'practice'
    questions: [],        // Current quiz questions
    currentIndex: 0,      // Current question index
    answers: [],          // User's answers [{selected, correct, questionIndex}]
    answered: false,      // Whether current question is answered
    totalQuestions: 0
};

// ============================================
// Screen Management
// ============================================

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const screen = document.getElementById(screenId);
    if (screen) {
        screen.classList.add('active');
        window.scrollTo(0, 0);
    }
}

function goHome() {
    state = { mode: null, questions: [], currentIndex: 0, answers: [], answered: false, totalQuestions: 0 };
    showScreen('screen-home');
}

// ============================================
// Home Screen
// ============================================

function initHome() {
    // Update total count
    const totalEl = document.getElementById('stat-total');
    if (totalEl && typeof QUESTIONS !== 'undefined') {
        totalEl.textContent = QUESTIONS.length;
    }

    // Build topic bars
    const topicCounts = {};
    if (typeof QUESTIONS !== 'undefined') {
        QUESTIONS.forEach(q => {
            topicCounts[q.topic] = (topicCounts[q.topic] || 0) + 1;
        });
    }

    const maxCount = Math.max(...Object.values(topicCounts), 1);
    const barsContainer = document.getElementById('topic-bars');
    if (!barsContainer) return;

    barsContainer.innerHTML = '';
    const sortedTopics = Object.entries(topicCounts).sort((a, b) => b[1] - a[1]);

    sortedTopics.forEach(([topic, count]) => {
        const pct = (count / maxCount) * 100;
        const color = TOPIC_COLORS[topic] || '#f59e0b';
        const shortName = TOPIC_SHORT[topic] || topic;

        const item = document.createElement('div');
        item.className = 'topic-bar-item';
        item.innerHTML = `
            <span class="topic-bar-label" title="${topic}">${shortName}</span>
            <div class="topic-bar-track">
                <div class="topic-bar-fill" style="background: ${color};" data-width="${pct}%"></div>
            </div>
            <span class="topic-bar-count">${count}</span>
        `;
        barsContainer.appendChild(item);
    });

    // Animate bars after a short delay
    requestAnimationFrame(() => {
        setTimeout(() => {
            document.querySelectorAll('.topic-bar-fill').forEach(bar => {
                bar.style.width = bar.dataset.width;
            });
        }, 200);
    });
}

// ============================================
// Quiz Logic
// ============================================

function shuffleArray(arr) {
    const shuffled = [...arr];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

function selectSimulatorQuestions() {
    const byTopic = {};
    QUESTIONS.forEach(q => {
        if (!byTopic[q.topic]) byTopic[q.topic] = [];
        byTopic[q.topic].push(q);
    });

    const selected = [];
    for (const [topic, count] of Object.entries(TOPIC_DISTRIBUTION_FINAL)) {
        const available = byTopic[topic] || [];
        const shuffled = shuffleArray(available);
        selected.push(...shuffled.slice(0, count));
    }

    return shuffleArray(selected);
}

function startSimulator() {
    if (typeof QUESTIONS === 'undefined' || QUESTIONS.length === 0) {
        alert('Error: No se pudieron cargar las preguntas.');
        return;
    }

    state.mode = 'simulator';
    state.questions = selectSimulatorQuestions();
    state.totalQuestions = state.questions.length;
    state.currentIndex = 0;
    state.answers = [];
    state.answered = false;

    setupQuizUI();
    showScreen('screen-quiz');
    renderQuestion();
}

function startPractice() {
    if (typeof QUESTIONS === 'undefined' || QUESTIONS.length === 0) {
        alert('Error: No se pudieron cargar las preguntas.');
        return;
    }

    state.mode = 'practice';
    state.questions = shuffleArray(QUESTIONS);
    state.totalQuestions = state.questions.length;
    state.currentIndex = 0;
    state.answers = [];
    state.answered = false;

    setupQuizUI();
    showScreen('screen-quiz');
    renderQuestion();
}

function setupQuizUI() {
    const badge = document.getElementById('quiz-mode-badge');
    if (state.mode === 'simulator') {
        badge.textContent = 'Simulador';
        badge.classList.remove('practice');
    } else {
        badge.textContent = 'Práctica';
        badge.classList.add('practice');
    }

    document.getElementById('quiz-total').textContent = state.totalQuestions;
}

function renderQuestion() {
    const q = state.questions[state.currentIndex];
    if (!q) return;

    state.answered = false;

    // Update progress
    document.getElementById('quiz-current').textContent = state.currentIndex + 1;
    const progress = ((state.currentIndex) / state.totalQuestions) * 100;
    document.getElementById('quiz-progress-bar').style.width = progress + '%';

    // Topic badge
    const topicName = document.getElementById('quiz-topic-name');
    topicName.textContent = q.subtopic || q.topic;
    const topicDot = document.querySelector('.topic-dot');
    topicDot.style.background = TOPIC_COLORS[q.topic] || '#f59e0b';

    // Question
    document.getElementById('question-number').textContent = `Pregunta ${state.currentIndex + 1}`;
    document.getElementById('question-text').textContent = q.question;

    // Options
    const container = document.getElementById('options-container');
    container.innerHTML = '';

    // Shuffle options for practice mode
    const options = state.mode === 'practice' ? shuffleArray(q.options) : q.options;

    options.forEach(opt => {
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.dataset.letter = opt.letter;
        btn.innerHTML = `
            <span class="option-letter">${opt.letter.toUpperCase()}</span>
            <span class="option-text">${opt.text}</span>
            <span class="option-indicator"></span>
        `;
        btn.addEventListener('click', () => selectOption(opt.letter, q));
        container.appendChild(btn);
    });

    // Hide feedback and navigation
    document.getElementById('feedback-card').style.display = 'none';
    document.getElementById('btn-next').style.display = 'none';
    document.getElementById('btn-finish').style.display = 'none';

    // Animate question card
    const card = document.getElementById('question-card');
    card.style.animation = 'none';
    card.offsetHeight; // force reflow
    card.style.animation = 'fadeIn 0.3s ease-out';
}

function selectOption(letter, question) {
    if (state.answered) return;
    state.answered = true;

    const isCorrect = letter === question.correct;

    // Record answer
    state.answers.push({
        questionIndex: state.currentIndex,
        selected: letter,
        correct: question.correct,
        isCorrect: isCorrect,
        question: question
    });

    // Update option styles
    const optionBtns = document.querySelectorAll('.option-btn');
    optionBtns.forEach(btn => {
        btn.classList.add('disabled');
        const btnLetter = btn.dataset.letter;

        if (btnLetter === question.correct) {
            btn.classList.add('correct');
            btn.querySelector('.option-indicator').textContent = '✅';
        }
        if (btnLetter === letter && !isCorrect) {
            btn.classList.add('incorrect');
            btn.querySelector('.option-indicator').textContent = '❌';
        }
    });

    // Practice mode: show feedback immediately
    if (state.mode === 'practice') {
        showFeedback(isCorrect, question);
    }

    // Show navigation
    showNavigation();
}

function showFeedback(isCorrect, question) {
    const card = document.getElementById('feedback-card');
    const icon = document.getElementById('feedback-icon');
    const label = document.getElementById('feedback-label');
    const text = document.getElementById('feedback-text');

    card.className = 'feedback-card glass-card ' + (isCorrect ? 'correct' : 'incorrect');
    icon.textContent = isCorrect ? '✅' : '❌';
    label.textContent = isCorrect ? '¡Correcto!' : 'Incorrecto';

    if (question.feedback) {
        text.textContent = question.feedback;
    } else {
        const correctOpt = question.options.find(o => o.letter === question.correct);
        text.textContent = `La respuesta correcta es: ${question.correct.toUpperCase()}) ${correctOpt ? correctOpt.text : ''}`;
    }

    card.style.display = 'block';
}

function showNavigation() {
    const isLast = state.currentIndex >= state.totalQuestions - 1;

    if (state.mode === 'simulator') {
        if (isLast) {
            document.getElementById('btn-finish').style.display = 'flex';
        } else {
            document.getElementById('btn-next').style.display = 'flex';
        }
    } else {
        // Practice mode: always show next (infinite)
        document.getElementById('btn-next').style.display = 'flex';
    }
}

function nextQuestion() {
    state.currentIndex++;

    if (state.mode === 'practice' && state.currentIndex >= state.totalQuestions) {
        // Reshuffle and continue
        state.questions = shuffleArray(QUESTIONS);
        state.currentIndex = 0;
        state.totalQuestions = state.questions.length;
    }

    renderQuestion();
}

function finishQuiz() {
    showResults();
}

// ============================================
// Results
// ============================================

function showResults() {
    showScreen('screen-results');

    const correctCount = state.answers.filter(a => a.isCorrect).length;
    const total = state.answers.length;
    const percentage = Math.round((correctCount / total) * 100);

    // Animate score circle
    const scoreFill = document.getElementById('score-fill');
    const circumference = 2 * Math.PI * 85; // r=85
    const offset = circumference - (percentage / 100) * circumference;

    // Add SVG gradient definition if not exists
    addScoreGradient();

    setTimeout(() => {
        scoreFill.style.strokeDashoffset = offset;
    }, 100);

    // Score text
    document.getElementById('score-percentage').textContent = percentage + '%';
    document.getElementById('score-fraction').textContent = `${correctCount}/${total}`;

    // Score message
    const emoji = document.getElementById('score-emoji');
    const msg = document.getElementById('score-message-text');

    if (percentage >= 90) {
        emoji.textContent = '🏆';
        msg.textContent = '¡Excelente, Oscar! Dominas la materia.';
    } else if (percentage >= 70) {
        emoji.textContent = '🎯';
        msg.textContent = '¡Muy bien! Vas por buen camino.';
    } else if (percentage >= 50) {
        emoji.textContent = '💪';
        msg.textContent = 'Buen esfuerzo. ¡Sigue practicando!';
    } else {
        emoji.textContent = '📚';
        msg.textContent = 'Necesitas repasar más. ¡No te rindas!';
    }

    // Score percentage color
    const scorePercentage = document.getElementById('score-percentage');
    if (percentage >= 70) {
        scorePercentage.style.color = '#10b981';
    } else if (percentage >= 50) {
        scorePercentage.style.color = '#f59e0b';
    } else {
        scorePercentage.style.color = '#ef4444';
    }

    // Topic breakdown
    renderTopicBreakdown();

    // Review list
    renderReviewList('all');
}

function addScoreGradient() {
    const svg = document.querySelector('.score-circle');
    if (!svg) return;
    if (svg.querySelector('#scoreGradient')) return;

    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML = `
        <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#f59e0b"/>
            <stop offset="50%" stop-color="#ef4444"/>
            <stop offset="100%" stop-color="#8b5cf6"/>
        </linearGradient>
    `;
    svg.insertBefore(defs, svg.firstChild);
}

function renderTopicBreakdown() {
    const container = document.getElementById('results-topics');
    container.innerHTML = '';

    // Group answers by topic
    const byTopic = {};
    state.answers.forEach(a => {
        const topic = a.question.topic;
        if (!byTopic[topic]) byTopic[topic] = { correct: 0, total: 0 };
        byTopic[topic].total++;
        if (a.isCorrect) byTopic[topic].correct++;
    });

    Object.entries(byTopic).sort((a, b) => b[1].total - a[1].total).forEach(([topic, data]) => {
        const pct = Math.round((data.correct / data.total) * 100);
        const color = TOPIC_COLORS[topic] || '#f59e0b';
        const shortName = TOPIC_SHORT[topic] || topic;

        const item = document.createElement('div');
        item.className = 'breakdown-item';
        item.innerHTML = `
            <span class="breakdown-topic" style="color: ${color}">${shortName}</span>
            <span class="breakdown-score">${data.correct}/${data.total}</span>
            <div class="breakdown-bar">
                <div class="breakdown-bar-fill" style="width: ${pct}%; background: ${color};"></div>
            </div>
        `;
        container.appendChild(item);
    });
}

function renderReviewList(filter) {
    const container = document.getElementById('review-list');
    container.innerHTML = '';

    let items = state.answers;
    if (filter === 'correct') items = items.filter(a => a.isCorrect);
    if (filter === 'wrong') items = items.filter(a => !a.isCorrect);

    items.forEach((answer, idx) => {
        const q = answer.question;
        const selectedOpt = q.options.find(o => o.letter === answer.selected);
        const correctOpt = q.options.find(o => o.letter === q.correct);

        const item = document.createElement('div');
        item.className = 'review-item';
        item.dataset.filter = answer.isCorrect ? 'correct' : 'wrong';

        let detailHTML = '';
        if (!answer.isCorrect) {
            detailHTML += `
                <div class="review-answer-label yours">Tu respuesta:</div>
                <div class="review-answer-text">${answer.selected.toUpperCase()}) ${selectedOpt ? selectedOpt.text : ''}</div>
            `;
        }
        detailHTML += `
            <div class="review-answer-label correct-label">Respuesta correcta:</div>
            <div class="review-answer-text">${q.correct.toUpperCase()}) ${correctOpt ? correctOpt.text : ''}</div>
        `;
        if (q.feedback) {
            detailHTML += `<div class="review-feedback">${q.feedback}</div>`;
        }

        item.innerHTML = `
            <div class="review-item-header">
                <span class="review-status">${answer.isCorrect ? '✅' : '❌'}</span>
                <span class="review-question">${q.question}</span>
            </div>
            <div class="review-detail">${detailHTML}</div>
        `;

        item.addEventListener('click', () => {
            item.classList.toggle('expanded');
        });

        container.appendChild(item);
    });
}

function filterReview(filter) {
    // Update active filter button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === filter);
    });
    renderReviewList(filter);
}

// ============================================
// Modal
// ============================================

function confirmQuit() {
    document.getElementById('modal-quit').style.display = 'flex';
}

function closeModal() {
    document.getElementById('modal-quit').style.display = 'none';
}

function quitQuiz() {
    closeModal();
    goHome();
}

// Close modal on overlay click
document.getElementById('modal-quit')?.addEventListener('click', (e) => {
    if (e.target.id === 'modal-quit') closeModal();
});

// ============================================
// Keyboard Shortcuts
// ============================================

document.addEventListener('keydown', (e) => {
    if (document.getElementById('modal-quit').style.display === 'flex') {
        if (e.key === 'Escape') closeModal();
        return;
    }

    const quizScreen = document.getElementById('screen-quiz');
    if (!quizScreen.classList.contains('active')) return;

    // Option selection: a, b, c, d keys
    if (!state.answered && ['a', 'b', 'c', 'd'].includes(e.key.toLowerCase())) {
        const q = state.questions[state.currentIndex];
        const optExists = q.options.find(o => o.letter === e.key.toLowerCase());
        if (optExists) {
            selectOption(e.key.toLowerCase(), q);
        }
    }

    // Next question: Enter or ArrowRight
    if (state.answered && (e.key === 'Enter' || e.key === 'ArrowRight')) {
        if (state.currentIndex >= state.totalQuestions - 1 && state.mode === 'simulator') {
            finishQuiz();
        } else {
            nextQuestion();
        }
    }

    // Quit: Escape
    if (e.key === 'Escape') {
        confirmQuit();
    }
});

// ============================================
// Init
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initHome();
});
