/**
 * SkillSprint - Client DOM Renderer
 * Purpose: Entry mount point for React 18 application root.
 * Author: SkillSprint Engineering
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
