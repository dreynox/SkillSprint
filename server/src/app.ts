/**
 * SkillSprint - Main Express Application Server Setup
 * Purpose: Express app declaration, CORS configuration, JSON parsing, API routing, and error handling.
 * Author: SkillSprint Engineering
 */

import express from 'express';
import cors from 'cors';
import forgeRoutes from './routes/forge.routes';

const app = express();

app.use(cors({ origin: '*' }));
app.use(express.json());

// API Routes
app.use('/api/v1/forge', forgeRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'SkillSprint Operating System API', timestamp: new Date() });
});

export default app;
