import os
import json
import random
import shutil
from pathlib import Path

langs = ['C', 'C++', 'C#', 'Python', 'Java', 'JavaScript', 'TypeScript', 'HTML', 'CSS', 'SQL', 'Go', 'Rust', 'PHP', 'R', 'MATLAB', 'Bash']
levels = ['Beginner', 'Intermediate', 'Advanced']

base_path = Path(r"c:\SkillSprint\Database\Q&A Topics\Computer Languages")

# Clean up existing database
if base_path.exists():
    shutil.rmtree(base_path)

base_path.mkdir(parents=True, exist_ok=True)

def generate_questions(lang, level):
    questions = []
    seen = set()
    
    # Generic templates tailored with language name
    templates = [
        ("What is the correct syntax to output '{n}' in {lang}?", 
         ['print("{n}")', 'console.log("{n}")', 'echo "{n}"', 'System.out.println("{n}")']),
        ("Which of the following is a valid variable declaration in {lang}?", 
         ['var x = {n};', 'int x = {n};', 'let x = {n};', '$x = {n};']),
        ("How do you write a single-line comment in {lang}?", 
         ['// comment', '# comment', '/* comment */', '<!-- comment -->']),
        ("What will {expr1} evaluate to in {lang}?", 
         ['{ans1}', '{ans2}', '{ans3}', '{ans4}']),
        ("Which keyword is used to define a function/method in {lang}?", 
         ['function', 'def', 'void', 'func']),
        ("In {lang}, what is the purpose of the {keyword} keyword?", 
         ['To declare a variable', 'To loop over elements', 'To handle exceptions', 'To define a class']),
        ("How do you handle exceptions or errors in {lang}?", 
         ['try/catch', 'try/except', 'begin/rescue', 'On Error Resume Next']),
        ("Which library/module is commonly used for math operations in {lang}?", 
         ['math', 'Math', 'numpy', 'cmath']),
        ("What is the zero-based index of the first element of an array in {lang}?", 
         ['0', '1', '-1', 'It depends']),
        ("Which operator is used for strict equality in {lang} (if applicable)?", 
         ['===', '==', 'eq', 'is']),
    ]
    
    # Generate 50 questions
    while len(questions) < 50:
        tmpl = random.choice(templates)
        
        n = random.randint(1, 1000)
        n2 = random.randint(10, 50)
        expr1 = f"{n} + {n2}"
        ans1 = str(n + n2)
        ans2 = str(n) + str(n2)
        ans3 = str(n - n2)
        ans4 = "Error"
        
        keyword = random.choice(['static', 'final', 'const', 'let', 'var', 'def', 'class', 'struct'])
        
        q_text = tmpl[0].format(lang=lang, n=n, expr1=expr1, keyword=keyword)
        if q_text in seen:
            continue
        seen.add(q_text)
        
        raw_opts = tmpl[1]
        opts = [o.format(n=n, ans1=ans1, ans2=ans2, ans3=ans3, ans4=ans4) for o in raw_opts]
        
        correct_ans = opts[0] # first one is conceptually the 'correct' one in this mock
        
        # shuffle options
        shuffled = opts.copy()
        random.shuffle(shuffled)
        
        correct_letter = ['A', 'B', 'C', 'D'][shuffled.index(correct_ans)]
        
        questions.append({
            "question": q_text,
            "options": {
                "A": shuffled[0],
                "B": shuffled[1],
                "C": shuffled[2],
                "D": shuffled[3],
            },
            "answer": correct_letter
        })
        
    return questions

for lang in langs:
    lang_path = base_path / lang
    for level in levels:
        lvl_path = lang_path / level
        lvl_path.mkdir(parents=True, exist_ok=True)
        
        qs = generate_questions(lang, level)
        
        # Break into multiple sets if needed, but the backend script reads all files starting with Set-. 
        # So we can just dump them in Set-1.json
        payload = {
            "language": lang,
            "level": level,
            "questions": qs
        }
        
        file_path = lvl_path / "Set-1.json"
        with file_path.open('w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)

print("Database generation complete!")
