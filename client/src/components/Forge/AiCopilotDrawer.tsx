/**
 * SkillSprint - Gemini AI Copilot Drawer Component
 * Purpose: Context-aware AI tutor drawer for code explanation, error debugging, and Big-O optimization.
 * Author: SkillSprint Engineering
 */

import React from 'react';
import { useForgeStore } from '../../store/useForgeStore';
import { X, Sparkles, Lightbulb, Bug, Cpu, Check, ArrowRight } from 'lucide-react';

export const AiCopilotDrawer: React.FC = () => {
  const { isAiDrawerOpen, toggleAiDrawer, isAiLoading, aiType, aiData, setCode } = useForgeStore();

  if (!isAiDrawerOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-[#161b22] border-l border-gray-800 shadow-2xl z-50 flex flex-col font-sans transition-all duration-300">
      {/* Drawer Header */}
      <div className="flex items-center justify-between px-5 py-4 bg-[#0d1117] border-b border-gray-800">
        <div className="flex items-center space-x-2 text-violet-400 font-bold text-sm">
          <Sparkles className="w-5 h-5" />
          <span>SkillSprint AI Copilot</span>
        </div>
        <button
          onClick={() => toggleAiDrawer(false)}
          className="p-1 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Drawer Content */}
      <div className="flex-1 p-5 overflow-y-auto space-y-6 text-xs text-gray-300">
        {isAiLoading ? (
          <div className="py-20 text-center space-y-3">
            <Sparkles className="w-8 h-8 mx-auto text-violet-500 animate-spin" />
            <p className="text-violet-300 font-medium">Gemini 1.5 is analyzing your code...</p>
          </div>
        ) : aiData ? (
          <>
            {aiType === 'EXPLAIN' && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-violet-400 font-bold text-sm">
                  <Lightbulb className="w-4 h-4" />
                  <span>Code Explanation</span>
                </div>
                <div className="p-3 bg-[#0d1117] rounded-xl border border-gray-800 whitespace-pre-wrap leading-relaxed">
                  {aiData.explanation}
                </div>
                <div>
                  <h4 className="font-semibold text-gray-200 mb-2">Key Concepts:</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {aiData.keyConcepts?.map((concept: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 bg-violet-600/20 text-violet-300 rounded-md border border-violet-500/30 text-[11px]"
                      >
                        {concept}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {aiType === 'DEBUG' && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-rose-400 font-bold text-sm">
                  <Bug className="w-4 h-4" />
                  <span>Error Diagnostics & Fix</span>
                </div>
                <div className="p-3 bg-rose-950/20 border border-rose-900/40 rounded-xl space-y-2">
                  <h4 className="font-semibold text-rose-300">Root Cause:</h4>
                  <p className="text-gray-300">{aiData.errorAnalysis}</p>
                </div>
                <div className="p-3 bg-[#0d1117] rounded-xl border border-gray-800 space-y-2">
                  <h4 className="font-semibold text-emerald-400">Suggested Fix:</h4>
                  <p className="text-gray-300">{aiData.suggestedFix}</p>
                </div>
                {aiData.fixedCodeSnippet && (
                  <button
                    onClick={() => setCode(aiData.fixedCodeSnippet)}
                    className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-emerald-600/20 transition-all"
                  >
                    <Check className="w-4 h-4" />
                    <span>Apply Fixed Code to Editor</span>
                  </button>
                )}
              </div>
            )}

            {aiType === 'OPTIMIZE' && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-emerald-400 font-bold text-sm">
                  <Cpu className="w-4 h-4" />
                  <span>Big-O Complexity Optimization</span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-[#0d1117] rounded-xl border border-gray-800 text-center">
                    <span className="text-[10px] text-gray-500 uppercase block">Time Complexity</span>
                    <span className="text-sm font-bold font-code text-rose-400">
                      {aiData.currentComplexity?.time}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 mx-auto my-1 text-gray-500" />
                    <span className="text-sm font-bold font-code text-emerald-400">
                      {aiData.optimizedComplexity?.time}
                    </span>
                  </div>

                  <div className="p-3 bg-[#0d1117] rounded-xl border border-gray-800 text-center">
                    <span className="text-[10px] text-gray-500 uppercase block">Space Complexity</span>
                    <span className="text-sm font-bold font-code text-amber-400">
                      {aiData.currentComplexity?.space}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 mx-auto my-1 text-gray-500" />
                    <span className="text-sm font-bold font-code text-emerald-400">
                      {aiData.optimizedComplexity?.space}
                    </span>
                  </div>
                </div>

                {aiData.optimizedCode && (
                  <button
                    onClick={() => setCode(aiData.optimizedCode)}
                    className="w-full py-2.5 bg-violet-600 hover:bg-violet-500 text-white font-bold rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-violet-600/20 transition-all"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>Apply Optimized Solution</span>
                  </button>
                )}
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
};
