import json
import random

languages = ['Python', 'JavaScript', 'C++', 'Java']
levels = ['Beginner', 'Intermediate', 'Advanced']

data = {lang: {lvl: [] for lvl in levels} for lang in languages}

templates = {
    'Python': {
        'Beginner': [
            ("def greet_{n}():\n    <span class=\"gap-blank\">____</span> \"Hello\"", ['return', 'print', 'yield', 'def'], 'return'),
            ("x = {n}\n<span class=\"gap-blank\">____</span>(x)", ['print', 'echo', 'console.log', 'System.out.println'], 'print'),
            ("items = [{n}, {n2}]\nitems.<span class=\"gap-blank\">____</span>({n3})", ['append', 'push', 'add', 'insert'], 'append'),
            ("for i in <span class=\"gap-blank\">____</span>({n}):\n    pass", ['range', 'xrange', 'len', 'count'], 'range'),
            ("name = \"Alice_{n}\"\n<span class=\"gap-blank\">____</span>(name)", ['len', 'length', 'size', 'count'], 'len'),
        ],
        'Intermediate': [
            ("squares_{n} = [x*x for x in range({n2}) <span class=\"gap-blank\">____</span> x % 2 == 0]", ['if', 'while', 'for', 'when'], 'if'),
            ("def add_{n}(a, b={n2}):\n    <span class=\"gap-blank\">____</span> a + b", ['return', 'yield', 'print', 'pass'], 'return'),
            ("with open('file_{n}.txt', 'r') as <span class=\"gap-blank\">____</span>:\n    pass", ['f', 'file', 'fp', 'any_valid_var'], 'f'),
            ("import math\nmath.<span class=\"gap-blank\">____</span>({n})", ['sqrt', 'square', 'root', 'pow2'], 'sqrt'),
            ("my_dict = {{'key_{n}': {n2}}}\nval = my_dict.<span class=\"gap-blank\">____</span>('key_b', 0)", ['get', 'fetch', 'pop', 'retrieve'], 'get'),
        ],
        'Advanced': [
            ("def generator_{n}():\n    <span class=\"gap-blank\">____</span> {n2}", ['yield', 'return', 'raise', 'pass'], 'yield'),
            ("class MyClass_{n}:\n    def __init__(self):\n        <span class=\"gap-blank\">____</span>.val = {n2}", ['self', 'this', 'cls', 'super'], 'self'),
            ("map(lambda x: x*{n}, <span class=\"gap-blank\">____</span>)", ['[1,2,3]', '1,2,3', 'range(3)', 'None'], '[1,2,3]'),
            ("try:\n    do_task_{n}()\n<span class=\"gap-blank\">____</span> Exception as e:\n    pass", ['except', 'catch', 'finally', 'else'], 'except'),
            ("def decorator_{n}(func):\n    def wrapper():\n        return func()\n    return <span class=\"gap-blank\">____</span>", ['wrapper', 'func', 'decorator', 'None'], 'wrapper'),
        ]
    },
    'JavaScript': {
        'Beginner': [
            ("let x_{n} = {n2};\n<span class=\"gap-blank\">____</span>.log(x_{n});", ['console', 'print', 'System', 'log'], 'console'),
            ("const arr_{n} = [{n2}, {n3}];\narr_{n}.<span class=\"gap-blank\">____</span>({n});", ['push', 'append', 'add', 'insert'], 'push'),
            ("function add_{n}(a, b) {{\n    <span class=\"gap-blank\">____</span> a + b;\n}}", ['return', 'yield', 'print', 'output'], 'return'),
            ("let name_{n} = \"Bob\";\nconsole.log(name_{n}.<span class=\"gap-blank\">____</span>);", ['length', 'size', 'len', 'count'], 'length'),
            ("if (x_{n} <span class=\"gap-blank\">____</span> {n2}) {{\n    // strict equality\n}}", ['===', '==', '=', 'equals'], '==='),
        ],
        'Intermediate': [
            ("const arr_{n} = [{n2}, {n3}];\narr_{n}.<span class=\"gap-blank\">____</span>(x => x * 2);", ['map', 'forEach', 'filter', 'reduce'], 'map'),
            ("setTimeout(() => {{\n    console.log({n});\n}}, <span class=\"gap-blank\">____</span>);", ['1000', '1s', 'one', '1000ms'], '1000'),
            ("const obj_{n} = {{ a: {n2} }};\nconst {{ <span class=\"gap-blank\">____</span> }} = obj_{n};", ['a', 'b', 'obj', 'val'], 'a'),
            ("document.<span class=\"gap-blank\">____</span>('myId_{n}');", ['getElementById', 'querySelector', 'getId', 'findId'], 'getElementById'),
            ("let x_{n} = {n2};\nx_{n} <span class=\"gap-blank\">____</span> 2; // add 2", ['+=', '=+', '++', '+'], '+='),
        ],
        'Advanced': [
            ("const promise_{n} = new <span class=\"gap-blank\">____</span>((resolve, reject) => {{ resolve({n2}); }});", ['Promise', 'Async', 'Task', 'Future'], 'Promise'),
            ("async function fetch_{n}() {{\n    <span class=\"gap-blank\">____</span> Promise.resolve({n2});\n}}", ['return', 'await', 'yield', 'async'], 'return'),
            ("class MyClass_{n} {{\n    constructor() {{\n        <span class=\"gap-blank\">____</span>.val = {n2};\n    }}\n}}", ['this', 'self', 'super', 'cls'], 'this'),
            ("const arr_{n} = [{n2}, {n3}];\narr_{n}.<span class=\"gap-blank\">____</span>((acc, val) => acc + val, 0);", ['reduce', 'map', 'filter', 'forEach'], 'reduce'),
            ("export <span class=\"gap-blank\">____</span> function foo_{n}() {{ return {n2}; }}", ['default', 'const', 'let', 'main'], 'default'),
        ]
    },
    'C++': {
        'Beginner': [
            ("int x_{n} = {n2};\n<span class=\"gap-blank\">____</span> << x_{n} << std::endl;", ['std::cout', 'printf', 'print', 'cout'], 'std::cout'),
            ("int arr_{n}[{n2}];\n<span class=\"gap-blank\">____</span>(int i=0; i<{n2}; i++) {{}}", ['for', 'while', 'do', 'if'], 'for'),
            ("int main_{n}() {{\n    <span class=\"gap-blank\">____</span> 0;\n}}", ['return', 'exit', 'yield', 'break'], 'return'),
            ("#include <span class=\"gap-blank\">____</span>\nint main_{n}() {{}}", ['<iostream>', 'iostream.h', '"iostream"', 'iostream'], '<iostream>'),
            ("int x_{n} = {n2};\nx_{n}<span class=\"gap-blank\">____</span>; // increment", ['++', '+=', '+', '--'], '++'),
        ],
        'Intermediate': [
            ("std::vector<int> v_{n};\nv_{n}.<span class=\"gap-blank\">____</span>({n2});", ['push_back', 'push', 'append', 'add'], 'push_back'),
            ("int* ptr_{n} = new int;\n<span class=\"gap-blank\">____</span> ptr_{n};", ['delete', 'free', 'remove', 'clear'], 'delete'),
            ("std::string s_{n} = \"Hello\";\ns_{n}.<span class=\"gap-blank\">____</span>();", ['length', 'size', 'len', 'count'], 'length'),
            ("class MyClass_{n} {{\n<span class=\"gap-blank\">____</span>:\n    int x;\n}};", ['public', 'private', 'protected', 'virtual'], 'public'),
            ("void func_{n}(int <span class=\"gap-blank\">____</span>x) {{ x = {n2}; }} // pass by reference", ['&', '*', 'ref', 'const'], '&'),
        ],
        'Advanced': [
            ("template <typename <span class=\"gap-blank\">____</span>>\nT add_{n}(T a, T b) {{ return a+b; }}", ['T', 'Class', 'Type', 'Arg'], 'T'),
            ("std::unique_ptr<int> p_{n} = std::<span class=\"gap-blank\">____</span><int>({n2});", ['make_unique', 'new_unique', 'create_unique', 'unique'], 'make_unique'),
            ("auto f_{n} = []() <span class=\"gap-blank\">____</span> {{ return {n2}; }}; // lambda return type", ['-> int', 'int', ': int', '=> int'], '-> int'),
            ("class Derived_{n} : public <span class=\"gap-blank\">____</span> {{}};", ['Base', 'super', 'parent', 'Object'], 'Base'),
            ("std::vector<int> v_{n} = {{{n2}, {n3}}};\nstd::sort(v_{n}.<span class=\"gap-blank\">____</span>(), v_{n}.end());", ['begin', 'start', 'first', 'front'], 'begin'),
        ]
    },
    'Java': {
        'Beginner': [
            ("int x_{n} = {n2};\nSystem.out.<span class=\"gap-blank\">____</span>(x_{n});", ['println', 'print', 'log', 'out'], 'println'),
            ("public static void <span class=\"gap-blank\">____</span>(String[] args) {{\n    // method {n}\n}}", ['main', 'Main', 'start', 'run'], 'main'),
            ("int[] arr_{n} = new int[{n2}];\narr_{n}[0] = {n3};", ['int', 'Integer', 'array', 'List'], 'int'),
            ("String s_{n} = \"Hello\";\ns_{n}.<span class=\"gap-blank\">____</span>();", ['length', 'size', 'len', 'count'], 'length'),
            ("boolean flag_{n} = <span class=\"gap-blank\">____</span>;", ['true', 'True', '1', 'yes'], 'true'),
        ],
        'Intermediate': [
            ("ArrayList<Integer> list_{n} = new <span class=\"gap-blank\">____</span><>();", ['ArrayList', 'List', 'Array', 'Vector'], 'ArrayList'),
            ("class MyClass_{n} <span class=\"gap-blank\">____</span> BaseClass {{}}", ['extends', 'implements', 'inherits', 'super'], 'extends'),
            ("public void run_{n}() throws <span class=\"gap-blank\">____</span> {{}}", ['Exception', 'Error', 'Throwable', 'Fault'], 'Exception'),
            ("String s_{n} = \"Java\";\ns_{n}.<span class=\"gap-blank\">____</span>(1); // gets 'a'", ['charAt', 'get', 'indexOf', 'char'], 'charAt'),
            ("interface Printable_{n} {{\n    void <span class=\"gap-blank\">____</span>();\n}}", ['print', 'Print', 'show', 'display'], 'print'),
        ],
        'Advanced': [
            ("List<Integer> list_{n} = Arrays.asList({n2}, {n3});\nlist_{n}.stream().<span class=\"gap-blank\">____</span>(x -> x*{n2});", ['map', 'filter', 'reduce', 'forEach'], 'map'),
            ("class MyThread_{n} implements <span class=\"gap-blank\">____</span> {{}}", ['Runnable', 'Thread', 'Callable', 'Task'], 'Runnable'),
            ("@<span class=\"gap-blank\">____</span>\npublic void toString_{n}() {{}}", ['Override', 'Overload', 'Super', 'Method'], 'Override'),
            ("Optional<String> opt_{n} = Optional.<span class=\"gap-blank\">____</span>(\"Hi\");", ['of', 'from', 'create', 'make'], 'of'),
            ("public <span class=\"gap-blank\">____</span> Singleton getInstance_{n}() {{ return instance; }}", ['static', 'final', 'const', 'public'], 'static'),
        ]
    }
}

for lang in languages:
    for lvl in levels:
        tmps = templates[lang][lvl]
        for i in range(50):
            tmp = random.choice(tmps)
            code = tmp[0].format(n=i, n2=random.randint(100,200), n3=random.randint(201,300))
            opts = list(tmp[1])
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
