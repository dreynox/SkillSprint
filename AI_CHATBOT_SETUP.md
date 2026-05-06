# SkillSprint AI Chatbot Setup Guide

## Overview
Your SkillSprint website now has an integrated AI chatbot powered by OpenAI's GPT models. The chatbot appears as:
- **Floating widget** (💬 button) on all student pages
- **Dedicated chat page** at `/frontend/html/chat.html`

## Features
✅ Ask any question about coding, programming, learning, or SkillSprint  
✅ Floating widget on Dashboard, Contests, Quiz, Leaderboard, Profile, Messages  
✅ Full-page chat interface with history persistence  
✅ Typing indicators and real-time responses  
✅ Message history saved for 1 hour  
✅ Mobile-responsive design  

---

## Setup: Getting an OpenAI API Key

### Step 1: Create OpenAI Account
1. Visit [platform.openai.com](https://platform.openai.com)
2. Click **Sign up** (or sign in if you have an account)
3. Complete email verification

### Step 2: Generate API Key
1. Go to **API keys** section: https://platform.openai.com/api-keys
2. Click **+ Create new secret key**
3. Copy the key (you won't see it again!)
4. Keep it safe — never share it publicly

### Step 3: Set API Key in Your Website

#### Option A: Local Development (Easy)
Open browser DevTools (F12 → Console) on any SkillSprint page and run:
```javascript
localStorage.setItem("skillsprint_openai_key", "sk-your-api-key-here");
```
Replace `sk-your-api-key-here` with your actual API key.

#### Option B: Chat Page Setup
1. Navigate to `/frontend/html/chat.html`
2. You'll see an "API Key Required" banner
3. Paste your API key in the input field
4. Click **Save Key**
5. The key is stored locally in your browser

#### Option C: Code-Based Setup (Production)
In your `backend/config.py` or environment:
```python
# Store as environment variable
OPENAI_API_KEY = "sk-your-api-key"
```

Then inject it into pages:
```html
<script>
  window.OPENAI_API_KEY = "sk-your-api-key";
</script>
```

---

## Using the Chatbot

### Floating Widget
1. Click the **💬** button on any page (bottom-right corner)
2. Type your question in the input field
3. Press **Enter** or click **Send**
4. Wait for the AI response (you'll see a typing indicator)

### Full Chat Page
1. Go to **Dashboard** → Click **AI Chat** card
   OR
2. Navigate directly to `/frontend/html/chat.html`
3. Enter your API key if prompted
4. Type questions and chat away!

### Example Questions
- "Explain recursion in JavaScript"
- "How do I solve a LeetCode medium problem?"
- "What's the difference between var, let, and const?"
- "Help me debug this code"
- "What contests are available on SkillSprint?"

---

## Features & Tips

### Message History
- Your last 20 messages are saved for **1 hour**
- Close and reopen the chat to see previous messages
- Click **Clear** button to delete all history

### Unread Badge
- When the widget is closed and you get a new AI response, a red badge appears
- Shows number of unread messages

### Mobile Friendly
- Widget adapts to phone screens
- Full chat page is fully responsive

### Cost Estimation
OpenAI charges per token:
- GPT-3.5-turbo: ~$0.0005 per 1K tokens (~0.05¢ per chat)
- GPT-4: ~$0.03 per 1K tokens (more expensive but smarter)

**Budget tip:** Set usage limits in your OpenAI account:
1. Go to [Billing Settings](https://platform.openai.com/account/billing/overview)
2. Click **Usage limits**
3. Set a monthly cap

---

## Implementation Details

### Files Added
```
frontend/
  css/
    chat-widget.css         # Widget & chat page styles
  js/
    chat-widget.js          # Chat widget initialization
  html/
    chat.html               # Full-page chat interface
```

### Pages Updated
Chat widget CSS & JS added to:
- `student-dashboard.html`
- `contests.html`
- `quiz.html`
- `leaderboard.html`
- `profile.html`
- `message.html`

### API Integration
- **Endpoint:** `https://api.openai.com/v1/chat/completions`
- **Model:** `gpt-3.5-turbo` (configurable in `chat-widget.js`)
- **Max tokens:** 300 (widget), 500 (full page)
- **Temperature:** 0.7 (balanced creativity & consistency)

---

## Customization

### Change AI Model
Edit `frontend/js/chat-widget.js` line 12:
```javascript
this.model = options.model || "gpt-4";  // Change to "gpt-4" or "gpt-4-turbo"
```

### Change System Prompt
Edit the `systemPrompt` in `chat-widget.js` (~line 14):
```javascript
this.systemPrompt = "Your custom instructions here...";
```

### Change Widget Position
Edit `frontend/css/chat-widget.css`:
```css
.chat-widget-button {
  bottom: 24px;  /* Distance from bottom */
  right: 24px;   /* Distance from right */
}
```

### Adjust Response Length
Edit `chat-widget.js` and `chat.html`:
```javascript
max_tokens: 200,  // Shorter responses
```

---

## Troubleshooting

### "API key not configured" Message
→ Set your API key using Option A, B, or C above

### No response / Typing indicator stuck
→ Check your OpenAI API key is valid at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
→ Check your account has credits/billing setup

### CORS Error (blocked by browser)
→ This is normal for client-side API calls. If severe, proxy through your backend:
```python
# backend/routes/chat_routes.py
@router.post("/api/chat")
async def chat_proxy(request: ChatRequest):
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={...}
    )
    return response.json()
```

### Widget not appearing
→ Check browser console (F12) for JavaScript errors
→ Verify `chat-widget.css` is loaded (Network tab)
→ Ensure `chat-widget.js` is loaded before DOM content

---

## Security Best Practices

⚠️ **NEVER** commit your API key to Git!

1. Add to `.gitignore`:
```
*.env
*.local
```

2. Use environment variables in production (never hardcode)

3. Set API usage limits on your OpenAI account

4. Rotate your key periodically: https://platform.openai.com/api-keys

5. Consider backend proxy for production:
   - Store API key on backend only
   - Frontend calls your backend endpoint
   - Backend forwards to OpenAI

---

## Next Steps

### Optional Enhancements
- [ ] Add follow-up question suggestions
- [ ] Implement RAG (Retrieval Augmented Generation) with SkillSprint docs
- [ ] Add code syntax highlighting for code snippets
- [ ] Integrate with contest/quiz data for context-aware responses
- [ ] Add user feedback (thumbs up/down) for response quality
- [ ] Create admin dashboard to monitor chat usage
- [ ] Add chat export/download for study notes

### Integration Ideas
- Auto-generate contest descriptions using AI
- Create quiz questions with AI assistance
- Personalized learning path recommendations
- Code review bot for submitted solutions

---

## Support

For issues:
1. Check OpenAI status: https://status.openai.com/
2. Review API documentation: https://platform.openai.com/docs/
3. Check console errors (F12 → Console tab)
4. Verify API key permissions in account settings

---

**Happy chatting! 🚀**
