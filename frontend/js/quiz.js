// script.js
const quizData = [
    {
        question: "What does HTML stand for?",
        options: ["Hyper Text Markup Language", "High Text Markup Language", "Hyper Tabular Markup Language", "None of these"],
        answer: 0
    },
    {
        question: "Which HTML tag is used to create a hyperlink?",
        options: ["<a>", "<link>", "<href>", "<url>"],
        answer: 0
    },
    {
        question: "Which CSS property controls text size?",
        options: ["font-style", "text-size", "font-size", "text-style"],
        answer: 2
    },
    {
        question: "Which JavaScript method adds a new element to the end of an array?",
        options: ["push()", "pop()", "shift()", "unshift()"],
        answer: 0
    },
    {
        question: "What is the correct syntax for referring to an external script?",
        options: ['<script src="script.js"></script>', '<script href="script.js"></script>', '<script ref="script.js"></script>', '<script name="script.js"></script>'],
        answer: 0
    },
    {
        question: "How do you create a function in JavaScript?",
        options: ["function = myFunction()", "function myFunction()", "function:myFunction()", "function myFunction"],
        answer: 1
    },
    {
        question: "Which character is used to indicate an end tag?",
        options: ["<", "/", "*", "="],
        answer: 1
    },
    {
        question: "What does CSS stand for?",
        options: ["Creative Style Sheets", "Colorful Style Sheets", "Cascading Style Sheets", "Computer Style Sheets"],
        answer: 2
    },
    {
        question: "Which event occurs when the user clicks on an HTML element?",
        options: ["onmouseover", "onclick", "onmouseclick", "onload"],
        answer: 1
    },
    {
        question: "How do you insert a comment in JavaScript?",
        options: ["<!-- This is a comment -->", "// This is a comment", "/* This is a comment */", "* This is a comment "],
        answer: 1
    }
];

let currentQuestion = 0;
let score = 0;
let userAnswers = [];

const questionEl = document.getElementById('question');
const optionsEl = document.getElementById('options');
const nextBtn = document.getElementById('next-btn');
const progressFill = document.getElementById('progress-fill');
const currentQEl = document.getElementById('current-q');
const quizContainer = document.getElementById('question-container');
const resultContainer = document.getElementById('result-container');
const scoreEl = document.getElementById('score');

function loadQuestion() {
    const q = quizData[currentQuestion];
    questionEl.textContent = q.question;
    currentQEl.textContent = currentQuestion + 1;
    progressFill.style.width = ((currentQuestion / 9) * 100) + '%';

    optionsEl.innerHTML = '';
    q.options.forEach((option, index) => {
        const div = document.createElement('div');
        div.className = 'option';
        div.textContent = `${String.fromCharCode(65 + index)}. ${option}`;
        div.onclick = () => selectOption(index, div);
        optionsEl.appendChild(div);
    });

    nextBtn.disabled = true;
}

function selectOption(answer, element) {
    document.querySelectorAll('.option').forEach(opt => opt.classList.remove('selected'));
    element.classList.add('selected');
    userAnswers[currentQuestion] = answer;
    nextBtn.disabled = false;
}

nextBtn.onclick = () => {
    if (userAnswers[currentQuestion] === quizData[currentQuestion].answer) {
        score++;
    }

    currentQuestion++;

    if (currentQuestion < quizData.length) {
        loadQuestion();
    } else {
        showResult();
    }
};

function showResult() {
    quizContainer.style.display = 'none';
    resultContainer.style.display = 'block';
    scoreEl.textContent = score;
}

loadQuestion();
