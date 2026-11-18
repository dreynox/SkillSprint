/**
 * SkillSprint - Forge Workspace Express Routes
 * Purpose: REST API routing for Forge workspace, execution, submissions, drafts, and AI Copilot helpers.
 * Author: SkillSprint Engineering
 */

import { Router } from 'express';
import { ForgeController } from '../controllers/forge.controller';

const router = Router();
const controller = new ForgeController();

// Problem & Workspace state
router.get('/problems/:slug', (req, res) => controller.getProblem(req, res));
router.post('/draft', (req, res) => controller.saveDraft(req, res));

// Code execution & submission
router.post('/execute', (req, res) => controller.executeCode(req, res));
router.post('/submit', (req, res) => controller.submitCode(req, res));

// AI Copilot features (Gemini)
router.post('/ai/explain', (req, res) => controller.aiExplain(req, res));
router.post('/ai/debug', (req, res) => controller.aiDebug(req, res));
router.post('/ai/optimize', (req, res) => controller.aiOptimize(req, res));

export default router;
