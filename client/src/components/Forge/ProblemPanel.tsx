/**
 * SkillSprint - Problem Description & Submissions Panel Component
 * Purpose: Displays problem spec, difficulty tiers, sample constraints, and historical submissions.
 * Author: SkillSprint Engineering
 */

import React from 'react';
import { useForgeStore } from '../../store/useForgeStore';
import { BookOpen, History, FileText, Sparkles, Cpu, Lightbulb, Bug } from 'lucide-react';

export const ProblemPanel: React.FC = () => {
  const { problem, activeLeftTab, setActiveLeftTab, triggerAiAction } = useForgeStore();

  if (!problem) return null;

  const difficultyColors = {
    EASY: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    MEDIUM: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    HARD: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  };

  return (
    <div className="flex flex-col h-full bg-[#161b22] border border-gray-800 rounded-xl overflow-hidden shadow-xl">
      {/* Top Header & Tab Navigation */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#0d1117] border-b border-gray-800">
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setActiveLeftTab('description')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeLeftTab === 'description'
                ? 'bg-violet-600/20 text-violet-400 border border-violet-500/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Description</span>
          </button>
          <button
            onClick={() => setActiveLeftTab('submissions')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeLeftTab === 'submissions'
                ? 'bg-violet-600/20 text-violet-400 border border-violet-500/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Submissions</span>
          </button>
          <button
            onClick={() => setActiveLeftTab('editorial')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeLeftTab === 'editorial'
                ? 'bg-violet-600/20 text-violet-400 border border-violet-500/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Editorial</span>
          </button>
        </div>
      </div>

      {/* Main Tab Body */}
      <div className="flex-1 p-5 overflow-y-auto space-y-6 text-sm text-gray-300">
        {activeLeftTab === 'description' && (
          <>
            {/* Title & Metadata Badges */}
            <div className="space-y-3">
              <h1 className="text-xl font-bold text-white tracking-tight">{problem.title}</h1>
              <div className="flex items-center space-x-3 text-xs">
                <span
                  className={`px-2.5 py-0.5 rounded-full font-semibold border ${
                    difficultyColors[problem.difficulty]
                  }`}
                >
                  {problem.difficulty}
                </span>
                <span className="px-2.5 py-0.5 rounded-full bg-gray-800 text-gray-300 border border-gray-700">
                  {problem.category}
                </span>
              </div>
            </div>

            {/* AI Action Bar Quick Tools */}
            <div className="p-3 bg-[#0d1117] rounded-xl border border-violet-900/30 flex items-center justify-between">
              <div className="flex items-center space-x-2 text-violet-400 text-xs font-semibold">
                <Sparkles className="w-4 h-4" />
                <span>AI Tutor Tools</span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => triggerAiAction('EXPLAIN')}
                  className="flex items-center space-x-1.5 px-2.5 py-1 bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 rounded-md text-xs border border-violet-500/30 transition-all"
                >
                  <Lightbulb className="w-3.5 h-3.5" />
                  <span>Explain</span>
                </button>
                <button
                  onClick={() => triggerAiAction('DEBUG')}
                  className="flex items-center space-x-1.5 px-2.5 py-1 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 rounded-md text-xs border border-rose-500/30 transition-all"
                >
                  <Bug className="w-3.5 h-3.5" />
                  <span>Debug</span>
                </button>
                <button
                  onClick={() => triggerAiAction('OPTIMIZE')}
                  className="flex items-center space-x-1.5 px-2.5 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 rounded-md text-xs border border-emerald-500/30 transition-all"
                >
                  <Cpu className="w-3.5 h-3.5" />
                  <span>Optimize</span>
                </button>
              </div>
            </div>

            {/* Problem Description Body */}
            <div className="prose prose-invert max-w-none text-gray-300 space-y-4 text-xs leading-relaxed">
              <p>{problem.description}</p>
            </div>

            {/* Constraints Card */}
            <div className="p-4 bg-[#0d1117] rounded-xl border border-gray-800 space-y-2">
              <h3 className="text-xs font-semibold text-gray-200">Constraints & Execution Limits</h3>
              <ul className="text-xs text-gray-400 space-y-1 font-code">
                <li>• CPU Time Limit: {problem.constraints.timeLimitMs} ms</li>
                <li>• Memory Limit: {problem.constraints.memoryLimitKb / 1024} MB</li>
                <li>• Strict memory safety enforced via Judge0 docker isolation</li>
              </ul>
            </div>
          </>
        )}

        {activeLeftTab === 'submissions' && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white">Your Past Submissions</h3>
            <div className="p-4 bg-[#0d1117] rounded-xl border border-gray-800 flex items-center justify-between text-xs font-code">
              <div className="space-y-1">
                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                  ACCEPTED
                </span>
                <p className="text-gray-400">Language: Python 3</p>
              </div>
              <div className="text-right text-gray-400">
                <p>Runtime: 42 ms</p>
                <p>Memory: 14.2 MB</p>
              </div>
            </div>
          </div>
        )}

        {activeLeftTab === 'editorial' && (
          <div className="space-y-4 text-xs text-gray-300">
            <h3 className="text-sm font-semibold text-white">Official Solution & Complexity Guide</h3>
            <p>
              The optimal strategy uses a Hash Map to store target complements in a single O(N) linear traversal pass.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
