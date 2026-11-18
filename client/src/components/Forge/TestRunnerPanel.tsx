/**
 * SkillSprint - Test Case Runner & Execution Terminal Output Panel
 * Purpose: Allows custom test case editing, sample input execution via Judge0, and submission verdict presentation.
 * Author: SkillSprint Engineering
 */

import React from 'react';
import { useForgeStore } from '../../store/useForgeStore';
import { Play, Send, CheckCircle2, XCircle, Clock, HardDrive, Terminal } from 'lucide-react';

export const TestRunnerPanel: React.FC = () => {
  const {
    sampleTestCases,
    customInput,
    setCustomInput,
    activeRightTab,
    setActiveRightTab,
    isExecuting,
    isSubmitting,
    executeCode,
    submitCode,
    executionResult,
    submissionResult,
  } = useForgeStore();

  return (
    <div className="flex flex-col h-full bg-[#161b22] border border-gray-800 rounded-xl overflow-hidden shadow-xl">
      {/* Header Controls & Action Buttons */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#0d1117] border-b border-gray-800">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveRightTab('testcases')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeRightTab === 'testcases'
                ? 'bg-violet-600/20 text-violet-400 border border-violet-500/30'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Testcases & Custom Input
          </button>
          <button
            onClick={() => setActiveRightTab('result')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeRightTab === 'result'
                ? 'bg-violet-600/20 text-violet-400 border border-violet-500/30'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Execution Console
          </button>
        </div>

        {/* Primary Action Buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={executeCode}
            disabled={isExecuting || isSubmitting}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg text-xs font-semibold border border-gray-700 transition-all disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current text-emerald-400" />
            <span>{isExecuting ? 'Running...' : 'Run Code'}</span>
          </button>

          <button
            onClick={submitCode}
            disabled={isExecuting || isSubmitting}
            className="flex items-center space-x-1.5 px-4 py-1.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white rounded-lg text-xs font-bold shadow-lg shadow-violet-600/25 transition-all disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{isSubmitting ? 'Submitting...' : 'Submit'}</span>
          </button>
        </div>
      </div>

      {/* Main Container Content */}
      <div className="flex-1 p-4 overflow-y-auto font-code text-xs text-gray-300">
        {activeRightTab === 'testcases' ? (
          <div className="space-y-4">
            <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider font-sans">
              Sample Inputs & Custom Runner
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {sampleTestCases.map((tc, idx) => (
                <div key={tc.id} className="p-3 bg-[#0d1117] rounded-lg border border-gray-800 space-y-2">
                  <span className="text-[11px] font-bold text-violet-400">Case {idx + 1}</span>
                  <div>
                    <label className="text-[10px] text-gray-500 block">Input:</label>
                    <pre className="p-2 bg-[#161b22] rounded text-gray-200 text-xs overflow-x-auto">{tc.input}</pre>
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-500 block">Expected Output:</label>
                    <pre className="p-2 bg-[#161b22] rounded text-emerald-400 text-xs overflow-x-auto">
                      {tc.expectedOutput}
                    </pre>
                  </div>
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider font-sans">
                Custom Test Input
              </label>
              <textarea
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                placeholder="Enter custom input standard stream..."
                rows={3}
                className="w-full p-3 bg-[#0d1117] text-gray-200 border border-gray-800 rounded-lg focus:outline-none focus:border-violet-500 resize-none font-code text-xs"
              />
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Submission Verdict Banner */}
            {submissionResult && (
              <div
                className={`p-4 rounded-xl border flex items-center justify-between font-sans ${
                  submissionResult.status === 'ACCEPTED'
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                }`}
              >
                <div className="flex items-center space-x-3">
                  {submissionResult.status === 'ACCEPTED' ? (
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                  ) : (
                    <XCircle className="w-6 h-6 text-rose-400" />
                  )}
                  <div>
                    <h3 className="text-sm font-bold">{submissionResult.status}</h3>
                    <p className="text-xs opacity-90">
                      Passed {submissionResult.passedTestCases} / {submissionResult.totalTestCases} Test Cases
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-4 text-xs font-code">
                  <div className="flex items-center space-x-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{submissionResult.runtimeMs} ms</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <HardDrive className="w-3.5 h-3.5" />
                    <span>{(submissionResult.memoryKb / 1024).toFixed(1)} MB</span>
                  </div>
                  <div className="px-2.5 py-1 bg-violet-600 text-white font-bold rounded-lg shadow">
                    +{submissionResult.xpEarned} XP
                  </div>
                </div>
              </div>
            )}

            {/* Execution Result Log */}
            {executionResult ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-gray-400 border-b border-gray-800 pb-2 font-sans">
                  <span className="flex items-center space-x-1.5">
                    <Terminal className="w-4 h-4 text-violet-400" />
                    <span>Verdict: {executionResult.status}</span>
                  </span>
                  <div className="flex items-center space-x-3">
                    <span>Runtime: {executionResult.runtimeMs} ms</span>
                    <span>Memory: {(executionResult.memoryKb / 1024).toFixed(1)} MB</span>
                  </div>
                </div>

                {executionResult.stdout && (
                  <div>
                    <label className="text-[11px] text-gray-400 block mb-1">Standard Output (stdout):</label>
                    <pre className="p-3 bg-[#0d1117] border border-gray-800 rounded-lg text-emerald-400 overflow-x-auto">
                      {executionResult.stdout}
                    </pre>
                  </div>
                )}

                {executionResult.stderr && (
                  <div>
                    <label className="text-[11px] text-rose-400 block mb-1">Standard Error (stderr):</label>
                    <pre className="p-3 bg-rose-950/20 border border-rose-900/40 rounded-lg text-rose-300 overflow-x-auto">
                      {executionResult.stderr}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-8 text-center text-gray-500 font-sans space-y-2">
                <Terminal className="w-8 h-8 mx-auto text-gray-600" />
                <p>Click "Run Code" or "Submit" to see execution results and test case comparisons.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
