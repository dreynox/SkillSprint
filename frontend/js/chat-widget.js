/**
 * SkillSprint Premium AI Chat Widget
 * Secure backend integration with TTS and Translation support
 */

class SkillSprintChatWidget {
  constructor(options = {}) {
    const defaultBase = window.API_BASE_URL ? `${window.API_BASE_URL}/chatbot` : "http://127.0.0.1:8000/chatbot";
    this.apiBase = options.apiBase || defaultBase;
    this.messages = [];
    this.isOpen = false;
    this.isLoading = false;
    this.unreadCount = 0;
    this.isSpeaking = false;
    this.currentUtterance = null;

    this.init();
  }

  init() {
    this.createWidgetHTML();
    this.attachEventListeners();
    this.loadMessageHistory();
  }

  createWidgetHTML() {
    // Floating Button
    const button = document.createElement("button");
    button.className = "chat-widget-button";
    button.id = "chat-widget-button";
    button.innerHTML = "💬";
    button.setAttribute("aria-label", "Open chat");
    document.body.appendChild(button);

    // Chat Container
    const container = document.createElement("div");
    container.className = "chat-widget-container";
    container.id = "chat-widget-container";
    container.innerHTML = `
      <div class="chat-widget-header">
        <h3>SkillSprint AI</h3>
        <button class="close-btn" aria-label="Close chat">✕</button>
      </div>
      <div class="chat-widget-messages" id="chat-messages">
        <div class="chat-message assistant">
          <div class="chat-bubble">👋 Hi! I'm SkillSprint AI. How can I help you with your coding journey today?</div>
          <div class="message-actions">
             <button class="action-btn tts-btn" title="Speak">🔊</button>
          </div>
        </div>
      </div>
      <div class="chat-widget-input-area">
        <textarea
          id="chat-input"
          class="chat-widget-input"
          placeholder="Ask me anything..."
          rows="1"
          aria-label="Type your message"
        ></textarea>
        <button class="chat-widget-send" id="chat-send" aria-label="Send message">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
      </div>
    `;
    document.body.appendChild(container);

    this.button = button;
    this.container = container;
    this.messagesContainer = container.querySelector("#chat-messages");
    this.input = container.querySelector("#chat-input");
    this.sendBtn = container.querySelector("#chat-send");
    this.closeBtn = container.querySelector(".close-btn");
  }

  attachEventListeners() {
    this.button.addEventListener("click", () => this.toggleWidget());
    this.closeBtn.addEventListener("click", () => this.toggleWidget());
    this.sendBtn.addEventListener("click", () => this.sendMessage());
    this.input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Auto-resize textarea
    this.input.addEventListener("input", () => {
      this.input.style.height = "auto";
      this.input.style.height = Math.min(this.input.scrollHeight, 100) + "px";
    });

    // Delegate message actions (TTS, etc)
    this.messagesContainer.addEventListener("click", (e) => {
      if (e.target.classList.contains("tts-btn")) {
        const bubble = e.target.closest(".chat-message").querySelector(".chat-bubble");
        this.speakText(bubble.textContent);
      }
    });
  }

  toggleWidget() {
    this.isOpen = !this.isOpen;
    if (this.isOpen) {
      this.container.classList.add("open");
      this.button.classList.add("open");
      this.input.focus();
      this.unreadCount = 0;
      this.updateBadge();
    } else {
      this.container.classList.remove("open");
      this.button.classList.remove("open");
      this.stopSpeaking();
    }
  }

  async sendMessage() {
    const text = this.input.value.trim();
    if (!text || this.isLoading) return;

    // Add user message
    this.addMessage("user", text);
    this.input.value = "";
    this.input.style.height = "auto";
    this.isLoading = true;
    this.sendBtn.disabled = true;

    // Show typing indicator
    this.addTypingIndicator();

    try {
      const response = await fetch(`${this.apiBase}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          history: this.messages.slice(-10) // Send last 10 messages for context
        })
      });

      if (!response.ok) throw new Error("Backend server error");
      
      const data = await response.json();
      this.removeTypingIndicator();
      this.addMessage("assistant", data.response);
      this.saveMessageHistory();
    } catch (error) {
      this.removeTypingIndicator();
      this.addMessage("system", `❌ Error: ${error.message}. Is the backend running?`);
      console.error("Chat error:", error);
    } finally {
      this.isLoading = false;
      this.sendBtn.disabled = false;
    }
  }

  addMessage(role, content) {
    const messageObj = { role, content, timestamp: Date.now() };
    this.messages.push(messageObj);

    const messageEl = document.createElement("div");
    messageEl.className = `chat-message ${role}`;
    
    let actionsHtml = "";
    if (role === "assistant") {
      actionsHtml = `
        <div class="message-actions">
          <button class="action-btn tts-btn" title="Speak">🔊</button>
        </div>
      `;
    }

    messageEl.innerHTML = `
      <div class="chat-bubble">${this.escapeHtml(content)}</div>
      ${actionsHtml}
    `;

    this.messagesContainer.appendChild(messageEl);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

    if (!this.isOpen && role === "assistant") {
      this.unreadCount++;
      this.updateBadge();
    }
  }

  addTypingIndicator() {
    const typingEl = document.createElement("div");
    typingEl.className = "chat-message assistant";
    typingEl.id = "typing-indicator";
    typingEl.innerHTML = `
      <div class="chat-bubble">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    `;
    this.messagesContainer.appendChild(typingEl);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }

  removeTypingIndicator() {
    const typingEl = document.getElementById("typing-indicator");
    if (typingEl) typingEl.remove();
  }

  updateBadge() {
    let badge = this.button.querySelector(".chat-widget-badge");
    if (this.unreadCount > 0) {
      if (!badge) {
        badge = document.createElement("div");
        badge.className = "chat-widget-badge";
        this.button.appendChild(badge);
      }
      badge.textContent = this.unreadCount;
    } else if (badge) {
      badge.remove();
    }
  }

  speakText(text) {
    if (this.isSpeaking) {
      this.stopSpeaking();
      return;
    }

    if (!('speechSynthesis' in window)) {
      alert("TTS not supported in this browser");
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onstart = () => { this.isSpeaking = true; };
    utterance.onend = () => { this.isSpeaking = false; };
    utterance.onerror = () => { this.isSpeaking = false; };
    
    this.currentUtterance = utterance;
    window.speechSynthesis.speak(utterance);
  }

  stopSpeaking() {
    window.speechSynthesis.cancel();
    this.isSpeaking = false;
  }

  saveMessageHistory() {
    const toSave = this.messages.slice(-20);
    localStorage.setItem("skillsprint_chat_history", JSON.stringify(toSave));
  }

  loadMessageHistory() {
    const saved = localStorage.getItem("skillsprint_chat_history");
    if (saved) {
      const history = JSON.parse(saved);
      const oneHourAgo = Date.now() - 3600000;
      this.messages = history.filter(m => m.timestamp > oneHourAgo);
      this.messages.forEach(msg => {
        if (msg.role !== "system") this.addMessage(msg.role, msg.content);
      });
    }
  }

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
}

// Auto-init
document.addEventListener("DOMContentLoaded", () => {
  window.chatWidget = new SkillSprintChatWidget();
});
