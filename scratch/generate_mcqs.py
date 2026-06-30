import json
import random

languages = ['Python', 'JavaScript', 'C++', 'Java']
levels = ['Beginner', 'Intermediate', 'Advanced']

data = {lang: {lvl: [] for lvl in levels} for lang in languages}

# Templates for each language and level
templates = {
    'Python': {
        'Beginner': [
            ("def greet_{n}():\n    <span class=\"gap-blank\">____</span> \"Hello\"", ['return', 'print', 'yield', 'def'], 'return'),
            ("x = {n}\n<span class=\"gap-blank\">____</span>(x)", ['print', 'echo', 'console.log', 'System.out.println'], 'print'),
            ("items = [{n}, {n2}]\nitems.<span class=\"gap-blank\">____</span>({n3})", ['append', 'push', 'add', 'insert'], 'append'),
            ("for i in <span class=\"gap-blank\">____</span>({n}):\n    pass", ['range', 'xrange', 'len', 'count'], 'range'),
            ("name = \"Alice\"\n<span class=\"gap-blank\">____</span>(name)", ['len', 'length', 'size', 'count'], 'len'),
        ],
        'Intermediate': [
            ("squares = [x*x for x in range({n}) <span class=\"gap-blank\">____</span> x % 2 == 0]", ['if', 'while', 'for', 'when'], 'if'),
            ("def add(a, b={n}):\n    <span class=\"gap-blank\">____</span> a + b", ['return', 'yield', 'print', 'pass'], 'return'),
            ("with open('file{n}.txt', 'r') as <span class=\"gap-blank\">____</span>:\n    pass", ['f', 'file', 'fp', 'any_valid_var'], 'f'),
            ("import math\nmath.<span class=\"gap-blank\">____</span>({n})", ['sqrt', 'square', 'root', 'pow2'], 'sqrt'),
            ("my_dict = {{'a': {n}}}\nval = my_dict.<span class=\"gap-blank\">____</span>('b', 0)", ['get', 'fetch', 'pop', 'retrieve'], 'get'),
        ],
        'Advanced': [
            ("def generator():\n    <span class=\"gap-blank\">____</span> {n}", ['yield', 'return', 'raise', 'pass'], 'yield'),
            ("class MyClass:\n    def __init__(self):\n        <span class=\"gap-blank\">____</span>.val = {n}", ['self', 'this', 'cls', 'super'], 'self'),
            ("map(lambda x: x*{n}, <span class=\"gap-blank\">____</span>)", ['[1,2,3]', '1,2,3', 'range(3)', 'None'], '[1,2,3]'),
            ("try:\n    pass\n<span class=\"gap-blank\">____</span> Exception as e:\n    pass", ['except', 'catch', 'finally', 'else'], 'except'),
            ("def decorator(func):\n    def wrapper():\n        return func()\n    return <span class=\"gap-blank\">____</span>", ['wrapper', 'func', 'decorator', 'None'], 'wrapper'),
        ]
    },
    'JavaScript': {
        'Beginner': [
            ("let x = {n};\n<span class=\"gap-blank\">____</span>.log(x);", ['console', 'print', 'System', 'log'], 'console'),
            ("const arr = [{n}, {n2}];\narr.<span class=\"gap-blank\">____</span>({n3});", ['push', 'append', 'add', 'insert'], 'push'),
            ("function add(a, b) {{\n    <span class=\"gap-blank\">____</span> a + b;\n}}", ['return', 'yield', 'print', 'output'], 'return'),
            ("let name = \"Bob\";\nconsole.log(name.<span class=\"gap-blank\">____</span>);", ['length', 'size', 'len', 'count'], 'length'),
            ("if (x <span class=\"gap-blank\">____</span> {n}) {{\n    // strict equality\n}}", ['===', '==', '=', 'equals'], '==='),
        ],
        'Intermediate': [
            ("const arr = [{n}, {n2}];\narr.<span class=\"gap-blank\">____</span>(x => x * 2);", ['map', 'forEach', 'filter', 'reduce'], 'map'),
            ("setTimeout(() => {{\n    console.log({n});\n}}, <span class=\"gap-blank\">____</span>);", ['1000', '1s', 'one', '1000ms'], '1000'),
            ("const obj = {{ a: {n} }};\nconst {{ <span class=\"gap-blank\">____</span> }} = obj;", ['a', 'b', 'obj', 'val'], 'a'),
            ("document.<span class=\"gap-blank\">____</span>('myId');", ['getElementById', 'querySelector', 'getId', 'findId'], 'getElementById'),
            ("let x = {n};\nx <span class=\"gap-blank\">____</span> 2; // add 2", ['+=', '=+', '++', '+'], '+='),
        ],
        'Advanced': [
            ("const promise = new <span class=\"gap-blank\">____</span>((resolve, reject) => {{ resolve({n}); }});", ['Promise', 'Async', 'Task', 'Future'], 'Promise'),
            ("async function fetch() {{\n    <span class=\"gap-blank\">____</span> Promise.resolve({n});\n}}", ['return', 'await', 'yield', 'async'], 'return'),
            ("class MyClass {{\n    constructor() {{\n        <span class=\"gap-blank\">____</span>.val = {n};\n    }}\n}}", ['this', 'self', 'super', 'cls'], 'this'),
            ("const arr = [{n}, {n2}];\narr.<span class=\"gap-blank\">____</span>((acc, val) => acc + val, 0);", ['reduce', 'map', 'filter', 'forEach'], 'reduce'),
            ("export <span class=\"gap-blank\">____</span> function foo() {{ return {n}; }}", ['default', 'const', 'let', 'main'], 'default'),
        ]
    },
    'C++': {
        'Beginner': [
            ("int x = {n};\n<span class=\"gap-blank\">____</span> << x << std::endl;", ['std::cout', 'printf', 'print', 'cout'], 'std::cout'),
            ("int arr[{n}];\n<span class=\"gap-blank\">____</span>(int i=0; i<{n}; i++) {{}}", ['for', 'while', 'do', 'if'], 'for'),
            ("int main() {{\n    <span class=\"gap-blank\">____</span> 0;\n}}", ['return', 'exit', 'yield', 'break'], 'return'),
            ("#include <span class=\"gap-blank\">____</span>\nint main() {{}}", ['<iostream>', 'iostream.h', '"iostream"', 'iostream'], '<iostream>'),
            ("int x = {n};\nx<span class=\"gap-blank\">____</span>; // increment", ['++', '+=', '+', '--'], '++'),
        ],
        'Intermediate': [
            ("std::vector<int> v;\nv.<span class=\"gap-blank\">____</span>({n});", ['push_back', 'push', 'append', 'add'], 'push_back'),
            ("int* ptr = new int;\n<span class=\"gap-blank\">____</span> ptr;", ['delete', 'free', 'remove', 'clear'], 'delete'),
            ("std::string s = \"Hello\";\ns.<span class=\"gap-blank\">____</span>();", ['length', 'size', 'len', 'count'], 'length'),
            ("class MyClass {{\n<span class=\"gap-blank\">____</span>:\n    int x;\n}};", ['public', 'private', 'protected', 'virtual'], 'public'),
            ("void func(int <span class=\"gap-blank\">____</span>x) {{ x = {n}; }} // pass by reference", ['&', '*', 'ref', 'const'], '&'),
        ],
        'Advanced': [
            ("template <typename <span class=\"gap-blank\">____</span>>\nT add(T a, T b) {{ return a+b; }}", ['T', 'Class', 'Type', 'Arg'], 'T'),
            ("std::unique_ptr<int> p = std::<span class=\"gap-blank\">____</span><int>({n});", ['make_unique', 'new_unique', 'create_unique', 'unique'], 'make_unique'),
            ("auto f = []() <span class=\"gap-blank\">____</span> {{ return {n}; }}; // lambda return type", ['-> int', 'int', ': int', '=> int'], '-> int'),
            ("class Derived : public <span class=\"gap-blank\">____</span> {{}};", ['Base', 'super', 'parent', 'Object'], 'Base'),
            ("std::vector<int> v = {{{n}, {n2}}};\nstd::sort(v.<span class=\"gap-blank\">____</span>(), v.end());", ['begin', 'start', 'first', 'front'], 'begin'),
        ]
    },
    'Java': {
        'Beginner': [
            ("int x = {n};\nSystem.out.<span class=\"gap-blank\">____</span>(x);", ['println', 'print', 'log', 'out'], 'println'),
            ("public static void <span class=\"gap-blank\">____</span>(String[] args) {{}}", ['main', 'Main', 'start', 'run'], 'main'),
            ("int[] arr = new int[{n}];\narr[0] = {n2};", ['int', 'Integer', 'array', 'List'], 'int'),
            ("String s = \"Hello\";\ns.<span class=\"gap-blank\">____</span>();", ['length', 'size', 'len', 'count'], 'length'),
            ("boolean flag = <span class=\"gap-blank\">____</span>;", ['true', 'True', '1', 'yes'], 'true'),
        ],
        'Intermediate': [
            ("ArrayList<Integer> list = new <span class=\"gap-blank\">____</span><>();", ['ArrayList', 'List', 'Array', 'Vector'], 'ArrayList'),
            ("class MyClass <span class=\"gap-blank\">____</span> BaseClass {{}}", ['extends', 'implements', 'inherits', 'super'], 'extends'),
            ("public void run() throws <span class=\"gap-blank\">____</span> {{}}", ['Exception', 'Error', 'Throwable', 'Fault'], 'Exception'),
            ("String s = \"Java\";\ns.<span class=\"gap-blank\">____</span>(1); // gets 'a'", ['charAt', 'get', 'indexOf', 'char'], 'charAt'),
            ("interface Printable {{\n    void <span class=\"gap-blank\">____</span>();\n}}", ['print', 'Print', 'show', 'display'], 'print'),
        ],
        'Advanced': [
            ("List<Integer> list = Arrays.asList({n}, {n2});\nlist.stream().<span class=\"gap-blank\">____</span>(x -> x*{n});", ['map', 'filter', 'reduce', 'forEach'], 'map'),
            ("class MyThread implements <span class=\"gap-blank\">____</span> {{}}", ['Runnable', 'Thread', 'Callable', 'Task'], 'Runnable'),
            ("@<span class=\"gap-blank\">____</span>\npublic void toString() {{}}", ['Override', 'Overload', 'Super', 'Method'], 'Override'),
            ("Optional<String> opt = Optional.<span class=\"gap-blank\">____</span>(\"Hi\");", ['of', 'from', 'create', 'make'], 'of'),
            ("public <span class=\"gap-blank\">____</span> Singleton getInstance() {{ return instance; }}", ['static', 'final', 'const', 'public'], 'static'),
        ]
    }
}

for lang in languages:
    for lvl in levels:
        tmps = templates[lang][lvl]
        seen = set()
        while len(data[lang][lvl]) < 50:
            tmp = random.choice(tmps)
            n = random.randint(1, 100)
            n2 = random.randint(101, 200)
            n3 = random.randint(201, 300)
            
            code = tmp[0].format(n=n, n2=n2, n3=n3)
            if code not in seen:
                seen.add(code)
                opts = list(tmp[1])
                # add some random variations to options to make them unique if needed
                if random.random() > 0.5:
                    opts = [opt if opt == tmp[2] else opt + str(random.randint(1,9)) for opt in opts]
                
                random.shuffle(opts)
                data[lang][lvl].append({
                    "text": "Fill in the blank to complete the code correctly.",
                    "code": code,
                    "options": opts,
                    "answer": tmp[2]
                })

with open(r'c:\SkillSprint\frontend\js\practice-data.js', 'w', encoding='utf-8') as f:
    f.write('window.PRACTICE_QUESTIONS = ')
    json.dump(data, f, indent=2)
    f.write(';\n')
