document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const msgInput = document.getElementById('msg-input');
    const messageArena = document.getElementById('message-display');

    const addMessage = (text, type = 'outgoing') => {
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}`;

        msgDiv.innerHTML = `
            <div class="bubble">
                ${type === 'incoming' ? '<span class="ref-tag">REF: USER_02</span>' : ''}
                <p>${text}</p>
                <span class="timestamp">${time}</span>
            </div>
        `;

        messageArena.appendChild(msgDiv);
        messageArena.scrollTop = messageArena.scrollHeight;
    };

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const val = msgInput.value.trim();
        if (val) {
            addMessage(val, 'outgoing');
            msgInput.value = '';
            
            // Simulating an automated response from the "Arena"
            setTimeout(() => {
                addMessage("CONNECTION_STABLE. PACKET_RECEIVED.", "incoming");
            }, 1200);
        }
    });
});