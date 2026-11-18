/**
 * SkillSprint - Forge Workspace API Controller
 * Purpose: Express route handlers for problem fetching, code execution, submissions, draft saving, and AI copilot actions.
 * Author: SkillSprint Engineering
 */

import { Request, Response } from 'express';
import { Judge0Service } from '../services/judge0.service';
import { GeminiForgeService } from '../services/gemini.service';
import { Problem, TestCase, CodeSubmission, UserWorkspaceState } from '../db/schema';

const judge0Service = new Judge0Service();
const geminiService = new GeminiForgeService();

// Seed mock database store for standalone verification & rapid dev
const MOCK_PROBLEMS: Record<string, Problem> = {
  'two-sum': {
    id: 'b1e8460e-862d-4bf8-b8bc-2d1829e79ab0',
    slug: 'two-sum',
    title: 'Two Sum',
    description: `Given an array of integers \`nums\` and an integer \`target\`, return *indices of the two numbers such that they add up to \`target\`*.

You may assume that each input would have ***exactly one solution***, and you may not use the same element twice.

You can return the answer in any order.

### Example 1:
\`\`\`text
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
\`\`\`

### Example 2:
\`\`\`text
Input: nums = [3,2,4], target = 6
Output: [1,2]
\`\`\``,
    difficulty: 'EASY',
    category: 'Arrays & Hashing',
    constraints: { timeLimitMs: 2000, memoryLimitKb: 262144 },
    starterCode: {
      python: `def two_sum(nums, target):\n    # Write your solution here\n    pass`,
      javascript: `function twoSum(nums, target) {\n    // Write your solution here\n};`,
      java: `class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        return new int[]{};\n    }\n}`,
      cpp: `#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) {\n        return {};\n    }\n};`,
      go: `package main\n\nfunc twoSum(nums []int, target int) []int {\n    return []int{}\n}`,
    },
    createdAt: new Date(),
    updatedAt: new Date(),
  },
};

const MOCK_TEST_CASES: Record<string, TestCase[]> = {
  'b1e8460e-862d-4bf8-b8bc-2d1829e79ab0': [
    {
      id: 'tc-1',
      problemId: 'b1e8460e-862d-4bf8-b8bc-2d1829e79ab0',
      input: '[2, 7, 11, 15]\n9',
      expectedOutput: '[0, 1]',
      isSample: true,
      explanation: 'nums[0] + nums[1] = 2 + 7 = 9',
      createdAt: new Date(),
    },
    {
      id: 'tc-2',
      problemId: 'b1e8460e-862d-4bf8-b8bc-2d1829e79ab0',
      input: '[3, 2, 4]\n6',
      expectedOutput: '[1, 2]',
      isSample: true,
      explanation: 'nums[1] + nums[2] = 2 + 4 = 6',
      createdAt: new Date(),
    },
    {
      id: 'tc-hidden-1',
      problemId: 'b1e8460e-862d-4bf8-b8bc-2d1829e79ab0',
      input: '[3, 3]\n6',
      expectedOutput: '[0, 1]',
      isSample: false,
      createdAt: new Date(),
    },
  ],
};

const MOCK_SUBMISSIONS: CodeSubmission[] = [];
const MOCK_DRAFTS: Map<string, UserWorkspaceState> = new Map();

export class ForgeController {
  /**
   * GET /api/v1/forge/problems/:slug
   */
  public async getProblem(req: Request, res: Response): Promise<void> {
    const { slug } = req.params;
    const problem = MOCK_PROBLEMS[slug];

    if (!problem) {
      res.status(404).json({ success: false, error: `Problem with slug '${slug}' not found` });
      return;
    }

    const testCases = MOCK_TEST_CASES[problem.id] || [];
    const sampleTestCases = testCases.filter((tc) => tc.isSample);
    const userId = (req.query.userId as string) || 'guest-user';
    const draftKey = `${userId}:${problem.id}`;
    const userDraft = MOCK_DRAFTS.get(draftKey);

    res.json({
      success: true,
      data: {
        problem,
        sampleTestCases,
        userDraft: userDraft || null,
      },
    });
  }

  /**
   * POST /api/v1/forge/execute
   */
  public async executeCode(req: Request, res: Response): Promise<void> {
    try {
      const { language, code, customInput, problemId } = req.body;

      if (!language || !code) {
        res.status(400).json({ success: false, error: 'Language and code parameters are required.' });
        return;
      }

      let stdin = customInput || '';
      if (!stdin && problemId && MOCK_TEST_CASES[problemId]) {
        const sample = MOCK_TEST_CASES[problemId].find((tc) => tc.isSample);
        if (sample) stdin = sample.input;
      }

      const result = await judge0Service.executeCode(language, code, stdin);

      res.json({
        success: true,
        data: {
          status: result.status.description,
          statusId: result.status.id,
          stdout: result.stdout,
          stderr: result.stderr,
          compileOutput: result.compile_output,
          runtimeMs: Math.round(parseFloat(result.time || '0.05') * 1000),
          memoryKb: result.memory || 14000,
        },
      });
    } catch (error: any) {
      res.status(500).json({ success: false, error: error.message });
    }
  }

  /**
   * POST /api/v1/forge/submit
   */
  public async submitCode(req: Request, res: Response): Promise<void> {
    try {
      const { problemId, language, code, mode = 'PRACTICE', userId = 'guest-user' } = req.body;

      if (!problemId || !language || !code) {
        res.status(400).json({ success: false, error: 'problemId, language, and code are required.' });
        return;
      }

      const testCases = MOCK_TEST_CASES[problemId] || [];
      let passedCount = 0;
      let totalRuntime = 0;
      let maxMemory = 0;
      let finalStatus: CodeSubmission['status'] = 'ACCEPTED';

      for (const tc of testCases) {
        const result = await judge0Service.executeCode(language, code, tc.input, tc.expectedOutput);
        const runtime = Math.round(parseFloat(result.time || '0.04') * 1000);
        totalRuntime += runtime;
        maxMemory = Math.max(maxMemory, result.memory || 12000);

        if (result.status.id === 3) {
          passedCount++;
        } else {
          if (result.status.id === 6) finalStatus = 'COMPILATION_ERROR';
          else if (result.status.id === 5) finalStatus = 'TIME_LIMIT_EXCEEDED';
          else if (result.status.id === 11) finalStatus = 'RUNTIME_ERROR';
          else finalStatus = 'WRONG_ANSWER';
          break;
        }
      }

      if (testCases.length === 0) passedCount = 1;

      const submission: CodeSubmission = {
        id: `sub-${Date.now()}`,
        userId,
        problemId,
        language,
        code,
        status: finalStatus,
        runtimeMs: totalRuntime,
        memoryKb: maxMemory,
        passedTestCases: passedCount,
        totalTestCases: testCases.length || 1,
        mode,
        createdAt: new Date(),
      };

      MOCK_SUBMISSIONS.push(submission);

      // Genesis Gamification XP Reward logic
      const xpEarned = finalStatus === 'ACCEPTED' ? (mode === 'CONTEST' ? 150 : 50) : 10;

      res.json({
        success: true,
        data: {
          submissionId: submission.id,
          status: submission.status,
          passedTestCases: submission.passedTestCases,
          totalTestCases: submission.totalTestCases,
          runtimeMs: submission.runtimeMs,
          memoryKb: submission.memoryKb,
          xpEarned,
        },
      });
    } catch (error: any) {
      res.status(500).json({ success: false, error: error.message });
    }
  }

  /**
   * POST /api/v1/forge/draft
   */
  public async saveDraft(req: Request, res: Response): Promise<void> {
    const { problemId, language, code, userId = 'guest-user', customTestInput, activeTab } = req.body;
    const draftKey = `${userId}:${problemId}`;

    const draftState: UserWorkspaceState = {
      id: `draft-${Date.now()}`,
      userId,
      problemId,
      language,
      codeDraft: code,
      customTestInput,
      activeTab,
      updatedAt: new Date(),
    };

    MOCK_DRAFTS.set(draftKey, draftState);
    res.json({ success: true, message: 'Draft autosaved successfully' });
  }

  /**
   * AI Controllers
   */
  public async aiExplain(req: Request, res: Response): Promise<void> {
    const { problemTitle = 'Two Sum', code, language } = req.body;
    const result = await geminiService.explainCode(problemTitle, code, language);
    res.json({ success: true, data: result });
  }

  public async aiDebug(req: Request, res: Response): Promise<void> {
    const { problemTitle = 'Two Sum', code, language, errorLog } = req.body;
    const result = await geminiService.debugCode(problemTitle, code, language, errorLog);
    res.json({ success: true, data: result });
  }

  public async aiOptimize(req: Request, res: Response): Promise<void> {
    const { problemTitle = 'Two Sum', code, language } = req.body;
    const result = await geminiService.optimizeCode(problemTitle, code, language);
    res.json({ success: true, data: result });
  }
}
