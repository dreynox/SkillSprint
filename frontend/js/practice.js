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

    // Mock questions based on selections
    const generateQuestions = (lang, level, num) => {
        const qList = [];
        for (let i = 0; i < num; i++) {
            let codeSnippet, options, answer;
            if (lang === 'Python') {
                codeSnippet = `def greet(name):\n    <span class="gap-blank">____</span> f"Hello, {name}"`;
                options = ['print', 'return', 'echo', 'yield'];
                answer = 'return';
            } else if (lang === 'JavaScript') {
                codeSnippet = `const arr = [1, 2, 3];\narr.<span class="gap-blank">____</span>((x) => x * 2);`;
                options = ['map', 'forEach', 'filter', 'reduce'];
                answer = 'map';
            } else if (lang === 'Java') {
                codeSnippet = `public static void <span class="gap-blank">____</span>(String[] args) {\n    System.out.println("Hello");\n}`;
                options = ['Main', 'start', 'main', 'run'];
                answer = 'main';
            } else {
                codeSnippet = `int a = 5;\n<span class="gap-blank">____</span> << a << std::endl;`;
                options = ['cout', 'std::cout', 'printf', 'print'];
                answer = 'std::cout';
            }
            
            // Randomize options
            options.sort(() => Math.random() - 0.5);

            qList.push({
                text: "Fill in the blank to complete the code correctly.",
                code: codeSnippet,
                options: options,
                answer: answer
            });
        }
        return qList;
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

    const endPractice = () => {
        practiceArea.style.display = 'none';
        resultContainer.style.display = 'block';

        const xp = correctCount * 15; // 15 XP per correct answer
        document.getElementById('result-stats').innerHTML = `You answered <b style="color:#00ff88">${correctCount}</b> out of ${totalQuestions} correctly.`;
        document.getElementById('xp-earned').textContent = `+${xp} XP Earned!`;

        // Update local user state for mockup
        try {
            let user = JSON.parse(localStorage.getItem('user'));
            if (user) {
                user.xp = (user.xp || 0) + xp;
                localStorage.setItem('user', JSON.stringify(user));
            }
        } catch(e) {}
    };

    if (startBtn) {
        startBtn.addEventListener('click', startPractice);
    }
});
