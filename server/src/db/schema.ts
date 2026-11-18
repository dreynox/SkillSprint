/**
 * SkillSprint - TypeScript Schema & Interface Definitions for Forge Workspace
 * Purpose: Strongly typed DB entities, inputs, and state schemas for Forge coding workspace.
 * Author: SkillSprint Engineering
 */

export type ProblemDifficulty = 'EASY' | 'MEDIUM' | 'HARD';

export type SubmissionStatus =
  | 'PENDING'
  | 'ACCEPTED'
  | 'WRONG_ANSWER'
  | 'TIME_LIMIT_EXCEEDED'
  | 'MEMORY_LIMIT_EXCEEDED'
  | 'COMPILATION_ERROR'
  | 'RUNTIME_ERROR';

export type WorkspaceMode = 'PRACTICE' | 'CONTEST' | 'INTERVIEW';

export interface ProblemConstraints {
  timeLimitMs: number;
  memoryLimitKb: number;
}

export interface StarterCodeMap {
  python?: string;
  javascript?: string;
  java?: string;
  cpp?: string;
  go?: string;
  [key: string]: string | undefined;
}

export interface Problem {
  id: string;
  slug: string;
  title: string;
  description: string;
  difficulty: ProblemDifficulty;
  category: string;
  constraints: ProblemConstraints;
  starterCode: StarterCodeMap;
  createdAt: Date;
  updatedAt: Date;
}

export interface TestCase {
  id: string;
  problemId: string;
  input: string;
  expectedOutput: string;
  isSample: boolean;
  explanation?: string;
  createdAt: Date;
}

export interface CodeSubmission {
  id: string;
  userId: string;
  problemId: string;
  language: string;
  code: string;
  status: SubmissionStatus;
  runtimeMs: number;
  memoryKb: number;
  passedTestCases: number;
  totalTestCases: number;
  judge0Token?: string;
  mode: WorkspaceMode;
  createdAt: Date;
}

export interface UserWorkspaceState {
  id: string;
  userId: string;
  problemId: string;
  language: string;
  codeDraft: string;
  customTestInput?: string;
  activeTab?: string;
  updatedAt: Date;
}
