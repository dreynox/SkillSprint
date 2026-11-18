/**
 * SkillSprint - Forge Integrated Coding Workspace Component (Phase 1, Feature 1)
 * Purpose: Unified main workspace screen combining Monaco Editor, resizable problem & test runner panels, and AI tutor drawer across Practice, Contest, and Interview modes.
 * Author: SkillSprint Engineering
 */

import React from 'react';
import { useForgeStore, WorkspaceMode } from '../../store/useForgeStore';
import { ProblemPanel } from './ProblemPanel';
import { MonacoCodeEditor } from './MonacoCodeEditor';
import { TestRunnerPanel } from './TestRunnerPanel';
import { AiCopilotDrawer } from './AiCopilotDrawer';
import { Code2, Flame, Award, Clock, Users, Sparkles } from 'lucide-react';

export const ForgeWorkspace: React.FC = () => {
  const { mode, setMode, toggleAiDrawer } = useForgeStore();

  const modeDescriptions: Record<WorkspaceMode, string> = {
    PRACTICE: 'Open Sandbox Mode • Full AI Copilot Assistance Enabled',
    CONTEST: 'Ranked Contest Mode • AI Hints Restricted • 60 Min Timer',
    INTERVIEW: 'Real-time Mock Interview • Socket.io Live Sync Active',
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#090d16] text-gray-100 overflow-hidden font-sans select-none">
      {/* Workspace Navigation Bar */}
      <header className="flex items-center justify-between px-6 py-3 bg-[#0d1117] border-b border-gray-800 shrink-0">
        <div className="flex items-center space-x-6">
          {/* SkillSprint Brand */}
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-gradient-to-tr from-violet-600 to-indigo-600 rounded-xl shadow-lg shadow-violet-600/30">
              <Code2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight text-white">
                SkillSprint <span className="text-violet-400 font-light">Forge</span>
              </span>
              <span className="block text-[10px] text-gray-400 font-code">{modeDescriptions[mode]}</span>
            </div>
          </div>

          {/* Mode Switcher Pill */}
          <div className="p-1 bg-[#161b22] border border-gray-800 rounded-xl flex items-center space-x-1">
            <button
              onClick={() => setMode('PRACTICE')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                mode === 'PRACTICE'
                  ? 'bg-violet-600 text-white shadow-md'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              Practice
            </button>
            <button
              onClick={() => setMode('CONTEST')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                mode === 'CONTEST'
                  ? 'bg-amber-600 text-white shadow-md'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              <span>Contest</span>
            </button>
            <button
              onClick={() => setMode('INTERVIEW')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                mode === 'INTERVIEW'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>Interview</span>
            </button>
          </div>
        </div>

        {/* Header Right Status Bar & AI Trigger */}
        <div className="flex items-center space-x-5">
          {mode === 'CONTEST' && (
            <div className="flex items-center space-x-1.5 px-3 py-1 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-lg text-xs font-code">
              <Clock className="w-3.5 h-3.5" />
              <span>58:24 remaining</span>
            </div>
          )}

          {/* Streak Indicator (Genesis Integration) */}
          <div className="flex items-center space-x-1 text-xs font-bold text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-lg border border-amber-500/20">
            <Flame className="w-4 h-4 fill-current" />
            <span>7 Day Streak</span>
          </div>

          {/* AI Copilot Toggle Button */}
          <button
            onClick={() => toggleAiDrawer()}
            className="flex items-center space-x-2 px-3.5 py-1.5 bg-gradient-to-r from-violet-600/30 to-indigo-600/30 hover:from-violet-600/40 hover:to-indigo-600/40 text-violet-300 rounded-xl border border-violet-500/30 text-xs font-semibold transition-all shadow-md"
          >
            <Sparkles className="w-4 h-4" />
            <span>AI Copilot</span>
          </button>
        </div>
      </header>

      {/* Main Resizable Workspace Grid */}
      <main className="flex-1 grid grid-cols-12 gap-3 p-3 overflow-hidden relative">
        {/* Left Column: Problem Specs & Submissions (5 cols) */}
        <div className="col-span-12 lg:col-span-5 h-full overflow-hidden">
          <ProblemPanel />
        </div>

        {/* Right Column: Monaco Code Editor & Test Cases Terminal (7 cols) */}
        <div className="col-span-12 lg:col-span-7 h-full flex flex-col space-y-3 overflow-hidden">
          {/* Top Half: Monaco Editor */}
          <div className="h-[60%] w-full">
            <MonacoCodeEditor />
          </div>

          {/* Bottom Half: Test Runner Terminal */}
          <div className="h-[40%] w-full">
            <TestRunnerPanel />
          </div>
        </div>

        {/* AI Copilot Drawer */}
        <AiCopilotDrawer />
      </main>
    </div>
  );
};
