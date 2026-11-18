/**
 * SkillSprint - Server Listener & Socket.io Initialization
 * Purpose: Starts HTTP server and Socket.io real-time pair programming listener.
 * Author: SkillSprint Engineering
 */

import http from 'http';
import { Server as SocketIOServer } from 'socket.io';
import app from './app';

const PORT = process.env.PORT || 5000;
const server = http.createServer(app);

const io = new SocketIOServer(server, {
  cors: { origin: '*' },
});

io.on('connection', (socket) => {
  console.log(`⚡ Socket connected: ${socket.id}`);

  // Pair programming / live code sync session handling for Interview & Pair mode
  socket.on('join_session', (sessionId: string) => {
    socket.join(sessionId);
    console.log(`User ${socket.id} joined Forge session: ${sessionId}`);
  });

  socket.on('code_change', (data: { sessionId: string; code: string; language: string }) => {
    socket.to(data.sessionId).emit('code_update', data);
  });

  socket.on('disconnect', () => {
    console.log(`🔥 Socket disconnected: ${socket.id}`);
  });
});

server.listen(PORT, () => {
  console.log(`🚀 SkillSprint Server listening on port ${PORT}`);
});
