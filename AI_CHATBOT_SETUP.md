# SkillSprint AI Chatbot Setup Guide

## Overview
Your SkillSprint website now has an integrated AI chatbot powered by **Google Gemini (FREE!)** 🎉

The chatbot appears as:
- **Floating widget** (💬 button) on all student pages
- **Dedicated chat page** at `/frontend/html/chat.html`

## Features
✅ Ask any question about coding, programming, learning, or SkillSprint  
✅ **100% FREE** - Google Gemini free tier included  
✅ 60 requests/minute limit (more than enough!)  
✅ Floating widget on Dashboard, Contests, Quiz, Leaderboard, Profile, Messages  
✅ Full-page chat interface with history persistence  
✅ Typing indicators and real-time responses  
✅ Message history saved for 1 hour  
✅ Mobile-responsive design  

---

## Setup: Getting a FREE Google Gemini API Key

### Step 1: Go to Google AI Studio
1. Visit [ai.google.dev](https://ai.google.dev)
2. Click **Get API Key** (top-right)
3. Click **Create API key in new Google Cloud project**

### Step 2: Copy Your API Key
1. Your key will be displayed (starts with `AIza...`)
2. Click **Copy** to copy it
3. Save it somewhere safe

---

## Using Your API Key

### Option A: Chat Page Setup (Easiest)
1. Navigate to `/frontend/html/chat.html`
2. You'll see an "API Key Required" banner
3. Paste your Google Gemini API key in the input field
4. Click **Save Key**
5. Done! Start chatting! 🚀

### Option B: Local Storage (for development)
Open browser DevTools (F12 → Console) and run:
```javascript
localStorage.setItem("skillsprint_gemini_key", "AIza_your_key_here");
```

### Option C: Environment Variable (Production)
Add to your environment or config:
```bash
GEMINI_API_KEY=AIza_your_key_here
```

Then inject into pages:
```html
<script>
  window.GEMINI_API_KEY = process.env.GEMINI_API_KEY;
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
3. Enter your Google Gemini API key if prompted
4. Type questions and chat away!

### Example Questions
- "Explain recursion in JavaScript"
- "How do I solve a LeetCode medium problem?"
- "What's the difference between var, let, and const?"
- "Help me debug this code"
- "What contests are available on SkillSprint?"

---

## Pricing & Limits

**Google Gemini Free Tier (NO CREDIT CARD REQUIRED):**
- ✅ **60 requests/minute** (plenty!)
- ✅ **100 requests/day** (for free tier)
- ✅ **No billing needed**
- ✅ Completely free to use

**Comparison:**
| Feature | Gemini | OpenAI GPT-3.5 |
|---------|--------|---|
| Cost | FREE | $0.0005 per 1K tokens |
| Setup | 2 minutes | Needs credit card |
| Quality | Excellent | Excellent |
| Speed | Fast | Fast |

---

## Implementation Details

### Files Added
```
frontend/
  css/
    chat-widget.css         # Widget & chat page styles
  js/
    chat-widget.js          # Chat widget initialization (Gemini-powered)
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
- **Provider:** Google Generative AI (Gemini)
- **Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent`
- **Model:** `gemini-pro` (free tier)
- **Max tokens:** 300 (widget), 500 (full page)
- **Temperature:** 0.7 (balanced creativity & consistency)
- **Cost:** FREE (within limits)

---

## Customization

### Change AI Model
Edit `frontend/js/chat-widget.js` line 9:
```javascript
this.model = options.model || "gemini-1.5-pro";  // Other options: "gemini-pro", "gemini-1.5-flash"
```

Available models:
- `gemini-pro` — Fastest, free tier
- `gemini-1.5-pro` — Better reasoning (may need upgrade)
- `gemini-1.5-flash` — Balanced speed and quality

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
maxOutputTokens: 200,  // Shorter responses
```

---

## Troubleshooting

### "API key not configured" Message
→ Set your Google Gemini API key using Option A, B, or C above

### No response / Typing indicator stuck
→ Check your Google Gemini API key is valid at [ai.google.dev](https://ai.google.dev)
→ Check you haven't exceeded free tier limits (60 requests/minute, 100/day)
→ Verify key format starts with `AIza...`

### CORS Error (blocked by browser)
→ Google Gemini API handles CORS properly, shouldn't be an issue
→ If it persists, check browser console for specific error

### "Quota exceeded" Error
→ You've hit the free tier limit (60 req/min or 100/day)
→ Wait a bit and try again
→ Upgrade to paid tier at [Google Cloud Console](https://console.cloud.google.com/) for higher limits

### Widget not appearing
→ Check browser console (F12) for JavaScript errors
→ Verify `chat-widget.css` is loaded (Network tab)
→ Ensure `chat-widget.js` is loaded before DOM content

### API key not saving
→ Check browser allows localStorage (not in private/incognito mode)
→ Clear browser cache and try again
→ Check console for storage permission errors

---

## Security Best Practices

⚠️ **NEVER** commit your API key to Git!

1. Add to `.gitignore`:
```
*.env
*.local
*.keys
```

2. Use environment variables in production (never hardcode)

3. Google Gemini free tier has no billing concerns, but:
   - Monitor your usage at [console.cloud.google.com](https://console.cloud.google.com/)
   - Set quotas to prevent accidental overages if you upgrade to paid tier

4. Rotate your key periodically if exposed at [ai.google.dev](https://ai.google.dev)

5. For production with sensitive data:
   - Use backend proxy (your server calls Google, frontend calls your server)
   - Store API key on backend only
   - This prevents key exposure in client code

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
1. Check Google Generative AI status: https://status.cloud.google.com/
2. Review Gemini API docs: https://ai.google.dev/docs
3. Check console errors (F12 → Console tab)
4. Verify API key format (starts with `AIza...`)
5. Try the API key in [Google AI Studio](https://aistudio.google.com/) first

**Helpful links:**
- Google Generative AI: https://ai.google.dev
- API Documentation: https://ai.google.dev/docs
- Gemini Models: https://ai.google.dev/models
- Free Tier Info: https://ai.google.dev/pricing

---

**Happy chatting! 🚀**
