/**
 * SkillSprint - Forge Workspace API Automated Test Suite
 * Purpose: Integration and unit testing for Forge execution, submission, drafts, and AI Copilot endpoints.
 * Author: SkillSprint Engineering
 */

import request from 'supertest';
import app from '../app';

describe('Forge Workspace API Suite', () => {
  describe('GET /api/v1/forge/problems/:slug', () => {
    it('should fetch problem details and sample test cases for valid slug', async () => {
      const res = await request(app).get('/api/v1/forge/problems/two-sum');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(res.body.data.problem).toBeDefined();
      expect(res.body.data.problem.title).toBe('Two Sum');
      expect(res.body.data.sampleTestCases.length).toBeGreaterThan(0);
    });

    it('should return 404 for unknown problem slug', async () => {
      const res = await request(app).get('/api/v1/forge/problems/non-existent-problem');
      expect(res.status).toBe(404);
      expect(res.body.success).toBe(false);
    });
  });

  describe('POST /api/v1/forge/execute', () => {
    it('should execute python code and return simulated Judge0 stdout', async () => {
      const payload = {
        language: 'python',
        code: 'def two_sum(nums, target):\n    return [0, 1]',
        customInput: '[2, 7, 11, 15]\n9',
      };

      const res = await request(app).post('/api/v1/forge/execute').send(payload);
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(res.body.data.status).toBe('Accepted');
      expect(res.body.data.runtimeMs).toBeDefined();
    });

    it('should reject requests missing code or language parameters', async () => {
      const res = await request(app).post('/api/v1/forge/execute').send({ language: 'python' });
      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
    });
  });

  describe('POST /api/v1/forge/submit', () => {
    it('should submit code solution and evaluate test cases with XP award', async () => {
      const payload = {
        problemId: 'b1e8460e-862d-4bf8-b8bc-2d1829e79ab0',
        language: 'javascript',
        code: 'function twoSum(nums, target) { return [0, 1]; }',
        mode: 'PRACTICE',
      };

      const res = await request(app).post('/api/v1/forge/submit').send(payload);
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(res.body.data.submissionId).toBeDefined();
      expect(res.body.data.status).toBe('ACCEPTED');
      expect(res.body.data.xpEarned).toBe(50);
    });
  });

  describe('POST /api/v1/forge/ai/explain', () => {
    it('should return AI code explanation and key concepts', async () => {
      const payload = {
        problemTitle: 'Two Sum',
        language: 'python',
        code: 'def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        if target - num in seen:\n            return [seen[target - num], i]\n        seen[num] = i',
      };

      const res = await request(app).post('/api/v1/forge/ai/explain').send(payload);
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(res.body.data.explanation).toBeDefined();
      expect(res.body.data.keyConcepts.length).toBeGreaterThan(0);
    });
  });
});
