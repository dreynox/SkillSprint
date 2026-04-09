const API_BASE = window.API_BASE_URL || "http://127.0.0.1:8000";

function getToken() {
    const raw = localStorage.getItem("access_token") || localStorage.getItem("token") || "";
    const cleaned = String(raw).trim().replace(/^"|"$/g, "");
    if (!cleaned || cleaned === "undefined" || cleaned === "null") {
        return "";
    }
    return cleaned;
}

function authHeaders() {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

let currentChatUserId = null;
let currentChatUserName = null;
let voiceStream = null;
let mediaRecorder = null;
let callActive = false;
let callStartTime = null;
let isMuted = false;

document.addEventListener('DOMContentLoaded', async () => {
    const chatForm = document.getElementById('chat-form');
    const msgInput = document.getElementById('msg-input');
    const fileBtn = document.getElementById('file-btn');
    const fileInput = document.getElementById('file-input');
    const newChatBtn = document.getElementById('new-chat-btn');
    const voiceCallBtn = document.getElementById('voice-call-btn');
    const endCallBtn = document.getElementById('end-call-btn');
    const closeVoiceModal = document.getElementById('close-voice-modal');
    const emojiBtn = document.getElementById('emoji-btn');
    const muteBtn = document.getElementById('mute-btn');

    // Load conversations on page load
    const conversations = await loadConversations();
    await maybeAutoOpenSelectedRecipient(conversations || []);

    // Send message
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = msgInput.value.trim();

        if (!message && !currentChatUserId) {
            alert('Please select a user to chat with');
            return;
        }

        if (message && currentChatUserId) {
            try {
                const response = await fetch(`${API_BASE}/messages/send`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...authHeaders(),
                    },
                    body: JSON.stringify({
                        recipient_id: currentChatUserId,
                        content: message,
                        media_type: 'text',
                    }),
                });

                if (response.ok) {
                    msgInput.value = '';
                    await loadMessages(currentChatUserId);
                    await loadConversations();
                }
            } catch (error) {
                console.error('Error sending message:', error);
            }
        }
    });

    // File upload
    fileBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', async (e) => {
        if (!currentChatUserId) {
            alert('Please select a user first');
            return;
        }

        const file = e.target.files[0];
        if (file) {
            await uploadMedia(file, currentChatUserId, detectMediaType(file));
        }
        fileInput.value = '';
    });

    // New chat
    newChatBtn.addEventListener('click', openUserSelectionModal);

    // Quick emoji insert
    emojiBtn.addEventListener('click', () => {
        msgInput.value += '😊';
        msgInput.focus();
    });

    // Voice call
    voiceCallBtn.addEventListener('click', () => {
        if (currentChatUserId) {
            startVoiceCall();
        } else {
            alert('Please select a user first');
        }
    });

    // End call
    endCallBtn.addEventListener('click', endVoiceCall);

    // Mute/unmute local mic during recording
    muteBtn.addEventListener('click', toggleMute);

    // Close modals
    closeVoiceModal.addEventListener('click', () => {
        document.getElementById('voice-modal').style.display = 'none';
    });

    document.getElementById('close-user-modal').addEventListener('click', () => {
        document.getElementById('user-modal').style.display = 'none';
    });

    // Auto-refresh messages every 2 seconds
    setInterval(() => {
        if (currentChatUserId) {
            loadMessages(currentChatUserId, true);
            loadConversations();
        }
    }, 2000);
});

async function loadConversations() {
    try {
        const response = await fetch(`${API_BASE}/messages/conversations`, {
            headers: authHeaders(),
        });

        if (!response.ok) throw new Error('Failed to load conversations');

        const conversations = await response.json();
        renderConversations(conversations);
        return conversations;
    } catch (error) {
        console.error('Error loading conversations:', error);
        return [];
    }
}

async function maybeAutoOpenSelectedRecipient(conversations) {
    const selectedRecipientIdRaw = sessionStorage.getItem('selectedRecipientId');
    if (!selectedRecipientIdRaw) {
        return;
    }

    sessionStorage.removeItem('selectedRecipientId');
    const selectedRecipientId = Number(selectedRecipientIdRaw);
    if (!Number.isFinite(selectedRecipientId)) {
        return;
    }

    const existingConversation = conversations.find((conv) => conv.user_id === selectedRecipientId);
    if (existingConversation) {
        await selectConversation(existingConversation.user_id, existingConversation.name);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/users/${selectedRecipientId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            throw new Error('Recipient not found');
        }

        const user = await response.json();
        await selectConversation(user.id, user.name || `User ${user.id}`);
    } catch (error) {
        console.error('Could not auto-open selected recipient:', error);
    }
}

function renderConversations(conversations) {
    const conversationsList = document.getElementById('conversations-list');
    if (conversations.length === 0) {
        conversationsList.innerHTML = '<div class="placeholder">No conversations yet</div>';
        return;
    }

    conversationsList.innerHTML = '';
    conversations.forEach((conv) => {
        const convDiv = document.createElement('div');
        convDiv.className = 'conversation-item';
        if (conv.user_id === currentChatUserId) convDiv.classList.add('active');

        const unreadBadge = conv.unread_count > 0 ? `<span class="unread-badge">${conv.unread_count}</span>` : '';

        convDiv.innerHTML = `
            <div class="conversation-avatar">
                ${conv.avatar_url ? `<img src="${conv.avatar_url}" alt="${conv.name}">` : '<div class="avatar-placeholder">' + conv.name[0].toUpperCase() + '</div>'}
            </div>
            <div class="conversation-info">
                <h4>${conv.name}</h4>
                <p>${conv.last_message}</p>
            </div>
            <div class="conversation-meta">
                <small>${formatTime(conv.last_message_time)}</small>
                ${unreadBadge}
            </div>
        `;

        convDiv.addEventListener('dblclick', () => {
            window.location.href = `profile.html?user_id=${conv.user_id}`;
        });

        convDiv.addEventListener('click', (event) => selectConversation(conv.user_id, conv.name, event));
        conversationsList.appendChild(convDiv);
    });
}

async function selectConversation(userId, userName, clickEvent = null) {
    currentChatUserId = userId;
    currentChatUserName = userName;

    // Update active conversation
    document.querySelectorAll('.conversation-item').forEach((el) => el.classList.remove('active'));
    const activeConversation = clickEvent?.target?.closest('.conversation-item');
    if (activeConversation) {
        activeConversation.classList.add('active');
    }

    // Show chat area
    document.getElementById('chat-empty').style.display = 'none';
    document.getElementById('chat-area').style.display = 'flex';

    // Update header
    document.getElementById('chat-user-name').textContent = userName;

    // Load messages
    await loadMessages(userId);
}

async function loadMessages(userId, silent = false) {
    try {
        const response = await fetch(`${API_BASE}/messages/with/${userId}`, {
            headers: authHeaders(),
        });

        if (!response.ok) throw new Error('Failed to load messages');

        const messages = await response.json();
        if (!silent) {
            renderMessages(messages);
        } else {
            // Only update if there are new messages
            const currentMessages = document.querySelectorAll('.message').length;
            if (messages.length > currentMessages) {
                renderMessages(messages);
            }
        }
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

function renderMessages(messages) {
    const messageArena = document.getElementById('message-display');
    
    // Get current user ID
    const currentUserData = JSON.parse(localStorage.getItem('user') || '{}');
    const currentUserId = currentUserData.id;

    messageArena.innerHTML = '';

    if (messages.length === 0) {
        messageArena.innerHTML = '<div class="placeholder">No messages yet. Start the conversation!</div>';
        return;
    }

    messages.forEach((msg) => {
        const isOutgoing = msg.sender_id === currentUserId;
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${isOutgoing ? 'outgoing' : 'incoming'}`;

        const time = new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        let bubbleContent = '';

        if (msg.media_type === 'text') {
            bubbleContent = `<p>${escapeHtml(msg.content || '')}</p>`;
        } else if (msg.media_type === 'image') {
            bubbleContent = `<img src="${normalizeMediaUrl(msg.file_path)}" alt="image" class="media-preview">`;
        } else if (msg.media_type === 'video') {
            bubbleContent = `<video controls class="media-preview"><source src="${normalizeMediaUrl(msg.file_path)}"></video>`;
        } else if (msg.media_type === 'voice') {
            bubbleContent = `<audio controls><source src="${normalizeMediaUrl(msg.file_path)}"></audio>`;
        } else if (msg.media_type === 'file') {
            bubbleContent = `<a href="${normalizeMediaUrl(msg.file_path)}" download class="file-link">📄 ${msg.content}</a>`;
        } else {
            bubbleContent = `<p>${msg.content || 'Unknown media'}</p>`;
        }

        msgDiv.innerHTML = `
            <div class="bubble">
                ${!isOutgoing ? `<span class="ref-tag">REF: ${msg.sender.name}</span>` : ''}
                ${bubbleContent}
                <span class="timestamp">${time}</span>
            </div>
        `;

        messageArena.appendChild(msgDiv);
    });

    messageArena.scrollTop = messageArena.scrollHeight;
}

async function uploadMedia(file, recipientId, mediaType) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('media_type', mediaType);

    try {
        document.getElementById('upload-progress').style.display = 'block';

        const response = await fetch(
            `${API_BASE}/messages/upload/${recipientId}`,
            {
                method: 'POST',
                headers: authHeaders(),
                body: formData,
            }
        );

        if (response.ok) {
            document.getElementById('upload-progress').style.display = 'none';
            await loadMessages(recipientId);
            await loadConversations();
        } else {
            throw new Error('Upload failed');
        }
    } catch (error) {
        console.error('Error uploading media:', error);
        alert('Failed to upload file');
        document.getElementById('upload-progress').style.display = 'none';
    }
}

function detectMediaType(file) {
    const type = file.type;
    if (type.startsWith('image/')) return 'image';
    if (type.startsWith('video/')) return 'video';
    if (type.startsWith('audio/')) return 'voice';
    return 'file';
}

async function startVoiceCall() {
    try {
        voiceStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        callActive = true;
        callStartTime = Date.now();
        isMuted = false;

        document.getElementById('voice-modal').style.display = 'flex';
        document.getElementById('voice-call-user').textContent = currentChatUserName;
        document.getElementById('mute-btn').textContent = 'Mute';

        // Start recording
        mediaRecorder = new MediaRecorder(voiceStream);
        const audioChunks = [];

        mediaRecorder.ondataavailable = (e) => {
            audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const formData = new FormData();
            formData.append('file', new File([audioBlob], 'voice_message.wav'));
            formData.append('media_type', 'voice');

            try {
                const response = await fetch(
                    `${API_BASE}/messages/upload/${currentChatUserId}`,
                    {
                        method: 'POST',
                        headers: authHeaders(),
                        body: formData,
                    }
                );

                if (response.ok) {
                    await loadMessages(currentChatUserId);
                    await loadConversations();
                }
            } catch (error) {
                console.error('Error sending voice message:', error);
            }
        };

        mediaRecorder.start();

        // Update call duration
        const durationInterval = setInterval(() => {
            if (!callActive) {
                clearInterval(durationInterval);
                return;
            }
            const elapsed = Math.floor((Date.now() - callStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            document.getElementById('call-duration').textContent = 
                `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    } catch (error) {
        console.error('Error starting voice call:', error);
        alert('Could not access microphone');
    }
}

function endVoiceCall() {
    if (mediaRecorder) {
        mediaRecorder.stop();
    }

    if (voiceStream) {
        voiceStream.getTracks().forEach((track) => track.stop());
    }

    callActive = false;
    isMuted = false;
    document.getElementById('voice-modal').style.display = 'none';
    document.getElementById('mute-btn').textContent = 'Mute';
}

function toggleMute() {
    if (!voiceStream) {
        return;
    }

    isMuted = !isMuted;
    voiceStream.getAudioTracks().forEach((track) => {
        track.enabled = !isMuted;
    });

    document.getElementById('mute-btn').textContent = isMuted ? 'Unmute' : 'Mute';
}

async function openUserSelectionModal() {
    try {
        const response = await fetch(`${API_BASE}/users`, {
            headers: authHeaders(),
        });

        if (!response.ok) throw new Error('Failed to load users');

        const users = await response.json();
        renderUsersList(users);
        document.getElementById('user-modal').style.display = 'flex';
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

function renderUsersList(users) {
    const usersList = document.getElementById('users-list');
    usersList.innerHTML = '';

    const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

    users.forEach((user) => {
        if (user.id === currentUser.id) return; // Skip self

        const userDiv = document.createElement('div');
        userDiv.className = 'user-item';

        userDiv.innerHTML = `
            <div class="user-avatar">
                ${user.avatar_url ? `<img src="${user.avatar_url}" alt="${user.name}">` : '<div class="avatar-placeholder">' + user.name[0].toUpperCase() + '</div>'}
            </div>
            <div class="user-info">
                <h4>${user.name}</h4>
                <p>${user.email}</p>
            </div>
        `;

        userDiv.addEventListener('click', (event) => {
            selectConversation(user.id, user.name, event);
            document.getElementById('user-modal').style.display = 'none';
            loadConversations();
        });

        userDiv.addEventListener('dblclick', () => {
            window.location.href = `profile.html?user_id=${user.id}`;
        });

        usersList.appendChild(userDiv);
    });
}

function formatTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    if (diffMins < 10080) return `${Math.floor(diffMins / 1440)}d ago`;

    return date.toLocaleDateString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function normalizeMediaUrl(path) {
    if (!path) {
        return '';
    }

    if (/^https?:\/\//i.test(path)) {
        return path;
    }

    if (path.startsWith('/')) {
        return `${API_BASE}${path}`;
    }

    return `${API_BASE}/${path}`;
}