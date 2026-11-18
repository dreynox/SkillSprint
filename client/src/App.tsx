/**
 * SkillSprint - Main Application Entry Component
 * Purpose: Mounts Forge Workspace within QueryClientProvider context.
 * Author: SkillSprint Engineering
 */

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ForgeWorkspace } from './components/Forge/ForgeWorkspace';

const queryClient = new QueryClient();

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ForgeWorkspace />
    </QueryClientProvider>
  );
};

export default App;
