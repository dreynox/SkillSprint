/**
 * SkillSprint - Database Migration Schema for Forge Workspace (Phase 1, Feature 1)
 * Purpose: Defines PostgreSQL tables for Problems, TestCases, CodeSubmissions, and UserWorkspaceState.
 * Author: SkillSprint Engineering
 */

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enum types for Forge Workspace
DO $$ BEGIN
    CREATE TYPE problem_difficulty AS ENUM ('EASY', 'MEDIUM', 'HARD');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE submission_status AS ENUM (
        'PENDING',
        'ACCEPTED',
        'WRONG_ANSWER',
        'TIME_LIMIT_EXCEEDED',
        'MEMORY_LIMIT_EXCEEDED',
        'COMPILATION_ERROR',
        'RUNTIME_ERROR'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE workspace_mode AS ENUM ('PRACTICE', 'CONTEST', 'INTERVIEW');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 1. Problems Table
CREATE TABLE IF NOT EXISTS forge_problems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(128) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    difficulty problem_difficulty NOT NULL DEFAULT 'EASY',
    category VARCHAR(64) NOT NULL DEFAULT 'Algorithms',
    constraints JSONB NOT NULL DEFAULT '{"time_limit_ms": 2000, "memory_limit_kb": 262144}',
    starter_code JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_forge_problems_slug ON forge_problems(slug);
CREATE INDEX IF NOT EXISTS idx_forge_problems_difficulty ON forge_problems(difficulty);

-- 2. Test Cases Table
CREATE TABLE IF NOT EXISTS forge_test_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    problem_id UUID NOT NULL REFERENCES forge_problems(id) ON DELETE CASCADE,
    input TEXT NOT NULL,
    expected_output TEXT NOT NULL,
    is_sample BOOLEAN NOT NULL DEFAULT FALSE,
    explanation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_forge_test_cases_problem ON forge_test_cases(problem_id);

-- 3. Code Submissions Table
CREATE TABLE IF NOT EXISTS forge_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    problem_id UUID NOT NULL REFERENCES forge_problems(id) ON DELETE CASCADE,
    language VARCHAR(32) NOT NULL,
    code TEXT NOT NULL,
    status submission_status NOT NULL DEFAULT 'PENDING',
    runtime_ms INTEGER DEFAULT 0,
    memory_kb INTEGER DEFAULT 0,
    passed_test_cases INTEGER DEFAULT 0,
    total_test_cases INTEGER DEFAULT 0,
    judge0_token VARCHAR(128),
    mode workspace_mode NOT NULL DEFAULT 'PRACTICE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_forge_submissions_user ON forge_submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_forge_submissions_problem ON forge_submissions(problem_id);

-- 4. User Workspace State (Drafts & Layout Session) Table
CREATE TABLE IF NOT EXISTS forge_workspace_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    problem_id UUID NOT NULL REFERENCES forge_problems(id) ON DELETE CASCADE,
    language VARCHAR(32) NOT NULL DEFAULT 'python',
    code_draft TEXT NOT NULL DEFAULT '',
    custom_test_input TEXT DEFAULT '',
    active_tab VARCHAR(32) DEFAULT 'description',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_problem_draft UNIQUE (user_id, problem_id)
);
