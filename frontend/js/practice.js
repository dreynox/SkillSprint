document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const setupDiv = document.getElementById('practice-setup');
    const guideDiv = document.getElementById('guide-section');
    const practiceArea = document.getElementById('practice-area');
    const resultContainer = document.getElementById('result-container');
    const qCounter = document.getElementById('q-counter');
    const timerValue = document.getElementById('timer-value');
    const questionContent = document.getElementById('question-content');
    const optionsContent = document.getElementById('options-content');

    let currentQuestionIndex = 0;
    let questions = [];
    let correctCount = 0;
    let totalQuestions = 0;
    let timerInterval;
    let timeRemaining = 0;

    const generateQuestions = (lang, level, num) => {
        let qList = [];
        if (window.PRACTICE_QUESTIONS && window.PRACTICE_QUESTIONS[lang] && window.PRACTICE_QUESTIONS[lang][level]) {
            // Clone and shuffle to avoid reusing same order
            qList = [...window.PRACTICE_QUESTIONS[lang][level]];
            qList.sort(() => Math.random() - 0.5);
        } else {
            console.warn("Could not find practice data for", lang, level);
            qList = [{text: "Error loading questions", code: "Error", options: [], answer: ""}];
        }
        
        // Return only the requested amount
        return qList.slice(0, num);
    };

    const startPractice = () => {
        const lang = document.getElementById('language').value;
        const level = document.getElementById('level').value;
        totalQuestions = parseInt(document.getElementById('numQuestions').value) || 5;
        const timeLimit = parseInt(document.getElementById('timeLimit').value) || 10;

        questions = generateQuestions(lang, level, totalQuestions);
        timeRemaining = timeLimit * 60;
        currentQuestionIndex = 0;
        correctCount = 0;

        setupDiv.style.display = 'none';
        guideDiv.style.display = 'none';
        practiceArea.style.display = 'block';

        updateTimerDisplay();
        timerInterval = setInterval(tickTimer, 1000);
        
        loadQuestion();
    };

    const tickTimer = () => {
        timeRemaining--;
        updateTimerDisplay();
        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            endPractice();
        }
    };

    const updateTimerDisplay = () => {
        const m = Math.floor(timeRemaining / 60);
        const s = timeRemaining % 60;
        timerValue.textContent = `${m}:${s < 10 ? '0' : ''}${s}`;
    };

    const loadQuestion = () => {
        if (currentQuestionIndex >= totalQuestions) {
            clearInterval(timerInterval);
            endPractice();
            return;
        }

        const q = questions[currentQuestionIndex];
        qCounter.textContent = `Question ${currentQuestionIndex + 1} / ${totalQuestions}`;
        
        questionContent.innerHTML = `
            <div style="margin-bottom:10px; color:#e0ffe8;">${q.text}</div>
            <div class="code-gap-question">
                <pre style="margin:0; white-space: pre-wrap;">${q.code}</pre>
            </div>
        `;

        optionsContent.innerHTML = '';
        q.options.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.textContent = opt;
            btn.onclick = () => checkAnswer(opt, q.answer, btn);
            optionsContent.appendChild(btn);
        });
    };

    const checkAnswer = (selected, correct, btn) => {
        // Disable all buttons to prevent multiple clicks
        const allBtns = optionsContent.querySelectorAll('.option-btn');
        allBtns.forEach(b => b.disabled = true);

        if (selected === correct) {
            btn.classList.add('correct');
            correctCount++;
            setTimeout(() => {
                currentQuestionIndex++;
                loadQuestion();
            }, 800);
        } else {
            btn.classList.add('wrong');
            // Find correct one and highlight
            allBtns.forEach(b => {
                if (b.textContent === correct) {
                    b.classList.add('correct');
                }
            });
            setTimeout(() => {
                currentQuestionIndex++;
                loadQuestion();
            }, 1500);
        }
    };

    const endPractice = async () => {
        practiceArea.style.display = 'none';
        resultContainer.style.display = 'block';

        const xp = correctCount * 15; // 15 XP per correct answer
        document.getElementById('result-stats').innerHTML = `You answered <b style="color:#00ff88">${correctCount}</b> out of ${totalQuestions} correctly.`;
        document.getElementById('xp-earned').textContent = `+${xp} XP Earned!`;

        if (xp > 0) {
            await persistXP(xp);
        }
    };

    const persistXP = async (xp) => {
        try {
            const raw = localStorage.getItem('access_token') || localStorage.getItem('token') || '';
            const token = String(raw).trim().replace(/^"|"$/g, '').replace(/^Bearer\s+/i, '').trim();
            if (!token || token === 'undefined' || token === 'null') return;

            const API_BASE = window.API_BASE_URL || 'http://127.0.0.1:8000';
            const res = await fetch(`${API_BASE}/users/me/add-xp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                body: JSON.stringify({ xp }),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                console.warn('Failed to persist XP:', err.detail || res.status);
            }
        } catch (e) {
            console.warn('XP persist error:', e);
        }
    };

    if (startBtn) {
        startBtn.addEventListener('click', startPractice);
    }
});
