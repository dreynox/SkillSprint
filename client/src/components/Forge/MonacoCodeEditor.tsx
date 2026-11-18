/**
 * SkillSprint - Monaco Editor Integration Component
 * Purpose: Professional multi-language code editor supporting Python, JS, Java, C++, and Go with dark mode theme and status bar.
 * Author: SkillSprint Engineering
 */

import React from 'react';
import Editor, { OnMount } from '@monaco-editor/react';
import { useForgeStore, SupportedLanguage } from '../../store/useForgeStore';
import { Code, Terminal, Sparkles, CheckCircle2 } from 'lucide-react';

const LANGUAGE_MONACO_MAP: Record<SupportedLanguage, string> = {
  python: 'python',
  javascript: 'javascript',
  java: 'java',
  cpp: 'cpp',
  go: 'go',
};

export const MonacoCodeEditor: React.FC = () => {
  const { language, code, setCode, setLanguage, isExecuting, isSubmitting } = useForgeStore();

  const handleEditorMount: OnMount = (editor, monaco) => {
    monaco.editor.defineTheme('skillsprint-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '6a9955', fontStyle: 'italic' },
        { token: 'keyword', foreground: 'c586c0', fontStyle: 'bold' },
        { token: 'string', foreground: 'ce9178' },
        { token: 'number', foreground: 'b5cea8' },
        { token: 'type', foreground: '4ec9b0' },
      ],
      colors: {
        'editor.background': '#0d1117',
        'editor.foreground': '#d4d4d4',
        'editorCursor.foreground': '#8b5cf6',
        'editor.lineHighlightBackground': '#161b22',
        'editorLineNumber.foreground': '#484f58',
        'editorLineNumber.activeForeground': '#e6edf3',
      },
    });
    monaco.editor.setTheme('skillsprint-dark');
  };

  return (
    <div className="flex flex-col h-full bg-[#0d1117] border border-gray-800 rounded-xl overflow-hidden shadow-2xl">
      {/* Editor Header Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#161b22] border-b border-gray-800">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-violet-400 font-medium text-xs">
            <Code className="w-4 h-4" />
            <span>Monaco Editor</span>
          </div>

          {/* Language Selector */}
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as SupportedLanguage)}
            className="bg-[#0d1117] text-gray-200 text-xs rounded-md border border-gray-700 px-2.5 py-1 focus:outline-none focus:border-violet-500 font-code transition-colors"
          >
            <option value="python">Python 3 (3.8.1)</option>
            <option value="javascript">JavaScript (Node.js ES6)</option>
            <option value="java">Java 17 (OpenJDK)</option>
            <option value="cpp">C++ 20 (GCC 9.2)</option>
            <option value="go">Go 1.21</option>
          </select>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center space-x-4 text-xs text-gray-400 font-code">
          <div className="flex items-center space-x-1.5 text-emerald-400">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Judge0 Connected</span>
          </div>
          {(isExecuting || isSubmitting) && (
            <div className="flex items-center space-x-1.5 text-violet-400 animate-pulse">
              <Terminal className="w-3.5 h-3.5" />
              <span>{isSubmitting ? 'Evaluating Test Cases...' : 'Executing Code...'}</span>
            </div>
          )}
        </div>
      </div>

      {/* Monaco Code Editor Instance */}
      <div className="flex-1 w-full relative">
        <Editor
          height="100%"
          language={LANGUAGE_MONACO_MAP[language]}
          value={code}
          onChange={(val) => setCode(val || '')}
          onMount={handleEditorMount}
          options={{
            fontSize: 14,
            fontFamily: "'JetBrains Mono', monospace",
            minimap: { enabled: true, scale: 0.75 },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            cursorBlinking: 'smooth',
            cursorSmoothCaretAnimation: 'on',
            lineNumbersMinChars: 3,
            padding: { top: 12, bottom: 12 },
          }}
        />
      </div>

      {/* Footer Status Line */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-[#161b22] border-t border-gray-800 text-[11px] text-gray-400 font-code">
        <div className="flex items-center space-x-4">
          <span>UTF-8</span>
          <span>Tab Size: 4</span>
          <span>Auto-Save Enabled</span>
        </div>
        <div className="flex items-center space-x-1 text-violet-400">
          <Sparkles className="w-3 h-3" />
          <span>SkillSprint AI Copilot Active</span>
        </div>
      </div>
    </div>
  );
};
