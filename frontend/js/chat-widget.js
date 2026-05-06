/**
 * SkillSprint AI Chat Widget
 * Floating chat widget with Google Gemini API integration (FREE)
 */

class SkillSprintChatWidget {
  constructor(options = {}) {
    this.apiKey = options.apiKey || window.GEMINI_API_KEY || localStorage.getItem("skillsprint_gemini_key") || null;
    this.model = options.model || "gemini-1.5-flash";
    this.messages = [];
    this.isOpen = false;
    this.isLoading = false;
    this.unreadCount = 0;

    // System context for the AI
    this.systemPrompt =
      options.systemPrompt ||
      `You are SkillSprint Assistant, a helpful AI tutor supporting students with coding, programming, and learning questions. 
Be concise, clear, and encouraging. Provide code examples when relevant with language hints (e.g., # Python, // JavaScript).
Keep responses under 150 words for the widget. Always be friendly and supportive.`;

    this.init();
  }

  init() {
    this.createWidgetHTML();
    this.attachEventListeners();
    this.loadMessageHistory();
  }

  createWidgetHTML() {
    // Button
    const button = document.createElement("button");
    button.className = "chat-widget-button";
    button.id = "chat-widget-button";
    button.innerHTML = "💬";
    button.setAttribute("aria-label", "Open chat");
    document.body.appendChild(button);

    // Container
    const container = document.createElement("div");
    container.className = "chat-widget-container";
    container.id = "chat-widget-container";
    container.innerHTML = `
      <div class="chat-widget-header">
        <h3>SkillSprint AI</h3>
        <button class="close-btn" aria-label="Close chat">✕</button>
      </div>
      <div class="chat-widget-messages" id="chat-messages">
        <div class="chat-message system">
          <div class="chat-bubble">👋 Hi! I'm here to help. Ask me anything!</div>
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
        <button class="chat-widget-send" id="chat-send" aria-label="Send message">📤</button>
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

    // Close widget when clicking outside
    document.addEventListener("click", (e) => {
      if (
        !this.container.contains(e.target) &&
        !this.button.contains(e.target) &&
        this.isOpen
      ) {
        this.toggleWidget();
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
    }
  }

  async sendMessage() {
    const text = this.input.value.trim();
    if (!text || this.isLoading) return;

    // Check API key
    if (!this.apiKey) {
      this.addMessage("system", "⚠️ API key not configured. Please set your Google Gemini API key");
      return;
    }

    // Add user message
    this.addMessage("user", text);
    this.input.value = "";
    this.input.style.height = "auto";
    this.isLoading = true;
    this.sendBtn.disabled = true;

    // Show typing indicator
    this.addTypingIndicator();

    try {
      const candidateModels = [
        this.model,
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-2.0-flash",
      ];
      let data = null;
      let lastError = null;

      for (const modelName of candidateModels) {
        const response = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${this.apiKey}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              contents: [
                {
                  role: "user",
                  parts: [{ text: this.systemPrompt + "\n\nUser: " + text }],
                },
              ],
              generationConfig: {
                temperature: 0.7,
                maxOutputTokens: 300,
              },
            }),
          }
        );

        if (response.ok) {
          this.model = modelName;
          data = await response.json();
          break;
        }

        const error = await response.json();
        const errorMsg = error.error?.message || JSON.stringify(error);
        lastError = new Error(`API Error (${response.status}): ${errorMsg}`);

        // If issue is not model availability, stop retrying.
        const modelIssue = response.status === 404 || /not found|unsupported/i.test(errorMsg);
        if (!modelIssue) {
          break;
        }
      }

      if (!data) {
        throw lastError || new Error("No supported Gemini model available for this key.");
      }
      
      // Extract response text
      const aiResponse =
        data.candidates?.[0]?.content?.parts?.[0]?.text ||
        "No response received";

      // Remove typing indicator and add response
      this.removeTypingIndicator();
      this.addMessage("assistant", aiResponse);

      // Save to localStorage
      this.saveMessageHistory();
    } catch (error) {
      this.removeTypingIndicator();
      this.addMessage("system", `❌ Error: ${error.message}`);
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
    messageEl.innerHTML = `<div class="chat-bubble">${this.escapeHtml(content)}</div>`;

    this.messagesContainer.appendChild(messageEl);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

    // Update unread count if widget is closed and assistant message
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
      badge.textContent = Math.min(this.unreadCount, 9) + (this.unreadCount > 9 ? "+" : "");
    } else if (badge) {
      badge.remove();
    }
  }

  saveMessageHistory() {
    try {
      // Keep last 20 messages to save space
      const toSave = this.messages.slice(-20);
      localStorage.setItem("skillsprint_chat_history", JSON.stringify(toSave));
    } catch (e) {
      console.warn("Could not save chat history:", e);
    }
  }

  loadMessageHistory() {
    try {
      const saved = localStorage.getItem("skillsprint_chat_history");
      if (saved) {
        const history = JSON.parse(saved);
        // Load messages but only if less than 1 hour old
        const oneHourAgo = Date.now() - 3600000;
        const recentMessages = history.filter((m) => m.timestamp > oneHourAgo);

        if (recentMessages.length > 0) {
          this.messages = recentMessages;
          // Render loaded messages
          recentMessages.forEach((msg) => {
            const messageEl = document.createElement("div");
            messageEl.className = `chat-message ${msg.role}`;
            messageEl.innerHTML = `<div class="chat-bubble">${this.escapeHtml(msg.content)}</div>`;
            this.messagesContainer.appendChild(messageEl);
          });
          this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
      }
    } catch (e) {
      console.warn("Could not load chat history:", e);
    }
  }

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  setApiKey(key) {
    this.apiKey = key;
    localStorage.setItem("skillsprint_gemini_key", key);
  }

  getApiKey() {
    return this.apiKey || localStorage.getItem("skillsprint_gemini_key");
  }

  clearHistory() {
    this.messages = [];
    localStorage.removeItem("skillsprint_chat_history");
    this.messagesContainer.innerHTML = `
      <div class="chat-message system">
        <div class="chat-bubble">👋 Hi! I'm here to help. Ask me anything!</div>
      </div>
    `;
  }
}

// Initialize widget on page load
document.addEventListener("DOMContentLoaded", () => {
  window.chatWidget = new SkillSprintChatWidget({
    apiKey: window.GEMINI_API_KEY || localStorage.getItem("skillsprint_gemini_key"),
  });
});
