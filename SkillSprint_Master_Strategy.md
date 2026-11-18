# SkillSprint — Master Product Strategy
### From College Coding Portal to $50B Student Operating System

**Version:** 1.0 — Foundational Architecture  
**Prepared for:** Development Team + AI Agent (Gemini 2.5 Flash)  
**Classification:** Internal Product Document

---

## Part I — The Vision

### What SkillSprint Is

SkillSprint is not a coding platform. It is not a social network. It is not a learning app.

It is the **Student Operating System** — the single environment where a student begins their day, tracks their growth, builds their skills, connects with their community, competes for recognition, and discovers their career.

The ambition is not to copy HackerRank or LinkedIn or Discord. The ambition is to make all of them unnecessary for a student.

### Why This Can Reach a $50B Valuation

Twitter's value was built on real-time public conversation. WhatsApp's was built on replacing SMS with something better for everyone. SkillSprint's value will be built on something larger than both — **owning the student-to-career pipeline**.

- 300M+ higher education students globally
- Every student needs: skill development, community, credentialing, career access
- No single platform owns this entire journey today
- The platform that does will know more about a student's abilities than any recruiter, professor, or university ever will

The moat is not the features. The moat is the **data** — a longitudinal, verifiable record of every skill a student built, every problem they solved, every competition they entered, every collaboration they completed. That data becomes worth more than the product itself.

---

## Part II — Strategic Foundation

### The 3 Laws of Building SkillSprint

**Law 1: Every feature must increase daily active usage.**  
If a feature doesn't give students a reason to open SkillSprint today, it doesn't ship.

**Law 2: Every feature must connect to every other feature.**  
A coding submission should feed the leaderboard, update the XP system, appear on the social feed, and recommend the next course. Isolated features are a startup mistake.

**Law 3: The platform must know the student better than they know themselves.**  
AI personalization is not a feature — it is the invisible layer that makes everything else feel like it was built for that specific student.

### Positioning

| Platform | What They Own |
|---|---|
| LeetCode | Coding practice |
| LinkedIn | Professional identity |
| Discord | Community voice |
| Coursera | Structured learning |
| GitHub | Code portfolio |
| **SkillSprint** | **All of the above, unified for students** |

---

## Part III — Product Architecture

### The 7 Pillars

```
┌─────────────────────────────────────────────────────────────┐
│                     SkillSprint OS                          │
├───────────┬───────────┬──────────┬──────────┬──────────────┤
│  LEARN    │  BUILD    │  COMPETE │  CONNECT │   GROW       │
│  Courses  │  Compiler │ Contests │  Social  │  Career      │
│  Paths    │  Projects │ Hackathon│  Comms   │  Opps        │
├───────────┴───────────┴──────────┴──────────┴──────────────┤
│              PROGRESSION LAYER (XP, Streaks, Levels)        │
├─────────────────────────────────────────────────────────────┤
│                  AI INTELLIGENCE LAYER                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Part IV — Feature Specifications

### Feature 1 — Apex Search (AI Learning Discovery)

**What the student sees:**  
A search experience that makes Google irrelevant for technical learning.

**When a student types "Fundamentals of React":**

The result page renders in under 800ms with:

**Top bar (persistent):**  
`AI | All | Courses | Videos | Images | Docs | Problems | Projects | Discuss`

**AI Panel (above everything):**  
- 3-paragraph intelligent summary of the topic
- Beginner → Intermediate → Advanced learning arc
- "Where you are now" based on student profile
- "What to learn next" — 3 specific recommendations

**Content Grid below AI panel:**
- Recommended SkillSprint courses for this topic
- Curated YouTube videos (verified, high-quality)
- Official documentation links
- GitHub repositories worth studying
- Blog posts from trusted technical sources
- Practice problems on SkillSprint
- Related hackathons
- Community discussions

**Filter tabs behavior:**
- `AI` = Full summary + all recommendations
- `Courses` = Only SkillSprint courses + external structured courses
- `Videos` = Tutorial videos, ranked by quality signals
- `Problems` = Practice problems, filtered by difficulty
- `Discuss` = Community posts tagged with that topic

**Personalization layer:**  
If the student's profile shows they know JavaScript but not React, the AI panel leads with "Since you already know JS, start with..." — not a generic introduction.

**Engineering requirements:**
- Debounced search with instant suggestions
- AI summary generated via Gemini API, cached per query
- External links filtered through a quality scoring system
- Response time target: <800ms for first contentful paint

---

### Feature 2 — Premium UI/UX System

**Design Philosophy:**  
Every pixel should feel like it was placed by a team that has built a $1B product before.

**Design System Foundations:**

*Typography:*
- Headings: Inter Display, 700 weight, tight letter-spacing
- Body: Inter, 400/500, 1.6 line height
- Code: JetBrains Mono
- Type scale: 12 / 14 / 16 / 20 / 24 / 32 / 48px

*Color System (on top of existing brand):*
- All interactive states must have: default, hover, active, focus, disabled
- Micro-shadows on cards: `0 1px 3px rgba(0,0,0,0.08)`
- No flat design — use depth to communicate hierarchy

*Motion Design:*
- Page transitions: 200ms ease-out fade-through
- Card hover: translateY(-2px) + shadow increase, 150ms
- Button press: scale(0.97), 80ms
- Skeleton loaders on every data-fetching component
- Staggered animations on list reveals (50ms delay between items)

*Component Standards:*

Every page must have:
- A clear H1 that explains where the student is
- Breadcrumbs where navigation depth > 2
- Empty states with illustration + action CTA (not just "No data found")
- Error states with human language + recovery action
- Loading states that don't block interaction

*Pages that need complete redesign:*
- Dashboard: Should feel like a mission control center — streaks, XP bar, upcoming contests, personalized feed, quick-action tiles
- Profile: Should feel like a premium portfolio — not a settings page with an avatar
- Leaderboard: Should feel like a stadium scoreboard — animate rank changes in real time
- Course Page: Should feel like a Netflix episode page — progress bar, "Continue" CTA above the fold
- Problem Page: Should feel like a cockpit — everything a coder needs, nothing they don't

---

### Feature 3 — Pulse (Communications Platform)

**Philosophy:**  
Students shouldn't need WhatsApp open in another tab.

**Architecture:**

*Direct Messages:*
- Full emoji picker (Emoji Mart library)
- GIF search via Tenor API
- Custom sticker packs (SkillSprint-branded + user-created)
- File sharing: images, PDFs, code files
- Voice notes: record + send, playback with waveform visualization
- Code snippet sharing with syntax highlighting
- Markdown rendering in messages
- Message reactions (emoji react)
- Reply / thread on any message
- Pinned messages
- Message search
- Read receipts + typing indicators
- End-to-end encryption for DMs

*Groups:*
- Up to 500 members
- Roles: Admin, Moderator, Member
- Pinned announcements
- Shared resources tab
- Scheduled messages
- Polls

*Communities (Discord-style):*
- Public or invite-only
- Channels: #general, #resources, #off-topic, custom
- Voice rooms for study sessions
- Community-level leaderboard
- Event announcements
- Community badges for members

*Integration with the rest of SkillSprint:*
- Share a coding problem directly into chat
- Share a contest result into your community
- "Study together" — link a course and invite friends to join the session

---

### Feature 4 — Forge (Integrated Coding Workspace)

**Philosophy:**  
Students should never need to open VS Code or a browser tab for an online compiler while using SkillSprint.

**Supported Languages (Phase 1):**
Python, JavaScript, TypeScript, Java, C, C++, C#, Go, Rust, Ruby, PHP, Kotlin, Swift, SQL

**Editor Features:**
- Monaco Editor (same engine as VS Code)
- Syntax highlighting for all languages
- IntelliSense / autocomplete
- Code formatting (Prettier / language-specific formatters)
- Multi-file support
- Dark / light / custom themes
- Vim keybinding mode
- Font size adjustment
- Code folding

**Execution Features:**
- Real-time output
- Custom stdin input
- Execution time + memory usage display
- Test case runner (custom + predefined)
- Submission history with diffs
- Performance comparison between submissions

**AI Features inside Forge:**
- "Explain this code" — line-by-line breakdown
- "Debug this" — identifies bugs + suggests fixes
- "Optimize this" — suggests more efficient approach
- "Generate test cases" — creates edge cases automatically
- "What is the time complexity?" — analyzes and explains Big O
- "Write this in Python" — translates to another language

**Modes:**
- Practice Mode: Unlimited attempts, hints available
- Contest Mode: Timer visible, no AI assist, submissions locked until contest ends
- Interview Mode: Whiteboard-style, clean UI, shareable link for interviewer

---

### Feature 5 — Genesis (Gamification System)

**Philosophy:**  
Every action on SkillSprint should feel like progress toward something meaningful.

**Progression Architecture:**

*XP (Experience Points):*

| Action | XP Earned |
|---|---|
| Daily login | 10 XP |
| Solve easy problem | 50 XP |
| Solve medium problem | 100 XP |
| Solve hard problem | 200 XP |
| Complete course lesson | 30 XP |
| Pass course quiz | 75 XP |
| Submit to contest | 150 XP |
| Win contest | 500 XP |
| Streak milestone (7 days) | 200 XP |
| Help in community (upvoted answer) | 50 XP |

*Levels (1–100):*
- Level 1–10: Novice
- Level 11–25: Apprentice
- Level 26–40: Practitioner
- Level 41–60: Engineer
- Level 61–80: Architect
- Level 81–95: Master
- Level 96–100: Legend

*Streaks:*
- Daily streak: consecutive days with at least one productive action
- Streak freeze: earn one "freeze" token per 7-day streak (protects against missing a day)
- Weekly streak milestones: bonus XP + badge at 4-week milestones
- Visual flame animation on profile when streak is active

*Coins (SkillCoin):*
- Earned through contests, achievements, challenges
- Spent on: streak freezes, profile themes, avatar frames, exclusive badges

*Badges:*
- Problem badges: "First Blood" (first problem), "Century" (100 problems solved)
- Language badges: "Pythonista", "Rustacean"
- Contest badges: "Podium" (top 3), "Undefeated" (3 contest wins)
- Learning badges: "Scholar" (5 courses complete), "Polymath" (courses in 3+ topics)
- Community badges: "Mentor" (100 upvoted answers), "Legend" (top community contributor)
- Hidden badges: discovered by finding easter eggs or doing unusual actions

*Daily Missions:*
- 3 missions per day, randomized, scaled to student level
- Example: "Solve 2 array problems", "Watch a React tutorial video", "Comment on a community post"
- Completion rewards: XP + coin bonus + progress toward weekly challenge

*Weekly Challenges:*
- Themed: "Dynamic Programming Week", "System Design Week"
- Community-wide — everyone competing on the same theme
- Top 10 get exclusive badge for that week

*Seasonal Events:*
- Hackathon Season (contest burst with special scoring)
- Learning Sprint (course completion multiplier)
- Community Month (social actions earn 2x XP)

---

### Feature 6 — Atlas (Student Social Network)

**Philosophy:**  
Students should be able to build a professional presence here that's more relevant than LinkedIn, because recruiters who understand tech will come here first.

**Profile:**
- Username, bio, current institution, year, interests
- Skills graph (visual representation of skill levels)
- Pinned achievements (up to 6)
- Portfolio projects (with links, screenshots, tech stack)
- Certificates earned on SkillSprint
- Contest history + best rankings
- Contribution graph (GitHub-style, showing activity over time)
- "Currently learning" section
- Stats: problems solved, contest rating, streak record, courses completed

**Feed:**

*Post types:*
- Text post (up to 1500 chars, Markdown support)
- Image post (up to 10 images)
- Video post (up to 5 minutes)
- Achievement share (auto-generated card when earning a badge or completing a course)
- Problem solution share (code snippet + explanation)
- Contest result share (auto-generated leaderboard card)
- Project showcase (title, description, tech stack, GitHub link, live demo link)

*Feed curation:*
- Following feed: posts from people you follow
- Discover feed: algorithmically curated based on interests + activity
- Trending: highest engagement in the last 24 hours

*Interactions:*
- Reactions: 👍 Helpful, 🔥 Impressive, 💡 Insightful, ❤️ Love
- Comments with threaded replies
- Share to your feed or to a community
- Save to bookmarks
- Report

**Stories + Highlights:**
- 24-hour stories with text, images, or videos
- Highlights: permanent story collections on your profile (e.g., "Contest Wins", "My Projects")

**Follow System:**
- Follow / unfollow
- Follower / following counts on profile
- Suggested follows based on interests and activity

**Communities:**
- Interest groups: React Developers, ML Enthusiasts, Competitive Programmers
- University groups: automatically created for verified institutions
- Study groups: private or public, centered on a course or topic

---

### Feature 7 — Nexus (Learning Platform)

**Philosophy:**  
Learning on SkillSprint should feel like a game where you happen to be becoming an expert.

**Course Structure:**

Every course is built in this hierarchy:
```
Course
  └── Modules (4–8 per course)
        └── Lessons (5–10 per module)
              ├── Video (3–10 minutes)
              ├── Reading (key concepts, clear language)
              ├── Code example (runnable in Forge)
              └── Checkpoint quiz (3–5 questions)
        └── Module Project (hands-on implementation)
        └── Module Quiz (graded assessment)
  └── Final Project
  └── Final Assessment
  └── Certificate
```

**Learning Paths:**

Curated sequences of courses that together build a complete skill.

Examples:
- "Full Stack Web Developer" (HTML → CSS → JS → React → Node → SQL → Deployment)
- "Competitive Programming Foundation" (Data Structures → Algorithms → Problem Solving patterns)
- "Machine Learning Engineer" (Python → Math → ML fundamentals → Deep Learning → Projects)
- "Android Developer" (Kotlin → Android Studio → APIs → Publish to Play Store)

**Interactive Learning:**

*Code exercises:*  
Every lesson where code is relevant includes a runnable exercise inside the lesson page itself (mini Forge). Student completes the code, gets instant feedback.

*Quizzes:*  
Multiple choice, fill-in-the-blank, drag-to-match, code completion. Adaptive difficulty — gets harder as the student answers correctly.

*Spaced Repetition:*  
Key concepts resurface in future lessons with "Do you remember?" micro-reviews. This is backed by research as the most effective retention method.

**AI Tutor:**
- Available inside every lesson
- Answers questions about the current lesson content
- Explains concepts in different ways if the student doesn't understand
- Cannot just give answers — guides the student to the answer
- "Give me a hint" mode vs "Explain fully" mode

**Onboarding Flow (New Users):**

When a student signs up:

*Step 1 — Goals:*  
"What do you want to achieve?" (Get an internship / Ace competitive programming / Build my own app / Master machine learning / Explore what I enjoy)

*Step 2 — Experience:*  
"How would you describe your current level?" (Complete beginner / Know the basics / Intermediate / Advanced)

*Step 3 — Time:*  
"How much time can you spend per day?" (15 min / 30 min / 1 hour / 2+ hours)

*Step 4 — Language:*  
"What programming language do you know or want to learn?"

Based on these answers, the system generates a personalized starter roadmap on the spot.

*Guided tour:*  
An interactive overlay tours the 5 key areas of the platform — Forge, Courses, Contests, Social, and their Profile — with one action to complete in each area (solve a simple "Hello World" problem, enroll in a starter course, check the leaderboard, make a first post, complete their profile). This earns them the "First Day" badge and 200 XP.

---

### Feature 8 — Compass (AI Student Assistant)

**Philosophy:**  
Every student deserves a personal mentor who knows their goals, their history, and the full landscape of opportunities available to them.

**What Compass does:**

*Daily brief (on Dashboard):*  
- "Good morning, [Name]. Your streak is at 12 days. Here's what I'd recommend today:"
- One course lesson to continue
- One problem to solve (matched to current skill level)
- One upcoming contest to register for
- One community discussion worth joining

*Intelligent recommendations:*  
- Courses: Based on stated goals + completed courses + activity patterns
- Problems: Based on weak areas identified from past submissions
- Contests: Based on skill level + previous contest participation
- Communities: Based on interests + learning path
- Opportunities: Internships, open source projects, hackathons matching their profile

*Career intelligence:*  
- Resume builder that auto-fills from SkillSprint achievements
- "Skills gap analysis" — upload a job description, Compass tells you what skills you're missing and which SkillSprint courses close that gap
- Interview prep: problem sets curated for companies the student is targeting

*Context awareness:*  
Compass reads the full student history — every problem submitted, every course started or completed, every contest entered, streak patterns, social posts, communities joined — and builds recommendations that improve continuously.

---

## Part V — Gamified Learning (Game-Type Learning)

**Philosophy:**  
If Duolingo can make people addicted to learning Spanish, SkillSprint can make students addicted to learning code.

**Coding Quest (Game Mode):**

Students navigate a world map of programming concepts. Each "territory" represents a topic (Arrays, Trees, Dynamic Programming, etc.). To unlock a territory, you complete the previous one.

Inside each territory:
- Story-driven challenges ("You're a developer at a startup. The database is slow. Fix the query.")
- Boss problems at the end of each territory (hard problem that unlocks the next area)
- Collectible items (themed avatars, badges, special effects)

*Difficulty levels:* Explorer / Builder / Engineer / Architect (maps to Beginner / Intermediate / Advanced / Expert)

**Daily Coding Puzzle:**
- One problem per day, same for everyone
- 24-hour window to solve it
- Global leaderboard for that day's puzzle
- Solution walkthrough unlocks at midnight

**Pair Programming:**
- Two students matched together to solve a problem collaboratively
- Real-time shared code editor in Forge
- Ranked and unranked modes

---

## Part VI — Technical Architecture

### System Design Principles

**Scalability-first from day one:**  
Design every service as if 100,000 students are using it simultaneously — even if only 500 are today.

**Modular monolith → microservices path:**  
Start as a well-structured monolith. Extract to microservices when a service is bottlenecked or needs independent deployment.

### Frontend

```
Framework:     React 18 + TypeScript (strict mode)
State:         Zustand (global) + React Query (server state)
Styling:       Tailwind CSS + custom design tokens
Editor:        Monaco Editor (Forge)
Real-time:     Socket.io client
Charts:        Recharts
Animation:     Framer Motion
```

### Backend

```
Primary API:   Node.js + Express + TypeScript
Code Execution: Isolated Docker containers per submission
                (Judge0 open-source or custom sandbox)
Real-time:     Socket.io server (messaging, leaderboards)
Auth:          Firebase Auth (JWT tokens)
AI:            Gemini API (search, tutor, recommendations)
Search:        Elasticsearch or Typesense (Apex Search)
```

### Database

```
Primary DB:    PostgreSQL
  - Users, profiles, courses, problems, submissions
  - Relationships: follows, enrollments, contest entries
  
Cache:         Redis
  - Session data, leaderboard rankings (sorted sets)
  - Rate limiting, real-time presence
  
File Storage:  Firebase Storage or AWS S3
  - Profile images, course videos, post media
  
Message DB:    PostgreSQL with optimized indexes
  (move to Cassandra at 10M+ messages)
```

### Infrastructure

```
Frontend:      Vercel (current) — keep, it's excellent
Backend:       Railway or Render → move to AWS/GCP at scale
DB:            Supabase (PostgreSQL + realtime) or self-hosted
CI/CD:         GitHub Actions
Monitoring:    Sentry (errors) + Posthog (analytics)
CDN:           Cloudflare
```

---

## Part VII — Development Roadmap

### Phase 0 — Stabilization (Weeks 1–3)

**Before building anything new, make what exists bulletproof.**

- Audit and fix all existing bugs
- Make the code compiler work 100% reliably for Python, JS, Java, C++
- Ensure auth flow is solid (login, register, password reset, session management)
- Set up error monitoring (Sentry)
- Establish design system: color tokens, spacing scale, component library
- Write a README and basic API documentation

**Deliverable:** A stable, working foundation that doesn't embarrass you in a demo.

---

### Phase 1 — Core Value (Months 1–2)

**Build the things that make students come back every day.**

1. Forge (complete coding workspace) — all languages working, AI features basic
2. Genesis (gamification) — XP, levels, streaks, daily missions
3. Nexus (learning platform) — course structure, lesson player, quizzes
4. Premium UI/UX — apply design system to all existing pages
5. Onboarding flow — signup → personalized roadmap → guided tour

**Deliverable:** A product you can demo at a hackathon and genuinely impress judges.

---

### Phase 2 — Community (Months 3–4)

**Build the social layer that makes students invite each other.**

1. Atlas (social network) — profiles, posts, feed, reactions, follow system
2. Pulse (messaging) — DMs, groups, emoji/GIF/sticker support
3. Communities — interest groups, university groups
4. Apex Search (basic) — search with AI summary + curated resources
5. Contest system improvements — real-time leaderboard, contest history

**Deliverable:** A product students recommend to each other organically.

---

### Phase 3 — Intelligence (Months 5–6)

**Add the AI layer that makes SkillSprint feel like it was built for each student personally.**

1. Compass (AI assistant) — daily brief, personalized recommendations
2. Apex Search (advanced) — full tab system, personalized results
3. Resume builder + skills gap analysis
4. Spaced repetition system in Nexus
5. Game Mode (Coding Quest) — basic version
6. Stories + Highlights in Atlas

**Deliverable:** A product that could be submitted as a serious startup to a university incubator.

---

### Phase 4 — Scale (Months 7–12)

**Prepare for users outside your college.**

1. Institution portal (colleges can onboard their students)
2. Recruiter portal (companies browse student profiles + post opportunities)
3. Certification partnerships
4. Open API for third-party integrations
5. Mobile apps (React Native)
6. Anti-cheating / proctoring for official assessments
7. Analytics dashboard for institutions

**Deliverable:** A product that can pitch to angel investors or YC.

---

## Part VIII — The Prompt for Gemini

Use the following prompt verbatim when engaging your AI coding agent. Paste it as the first message in a new session.

---

```
You are the Principal Architect and Lead Engineer of SkillSprint — a student platform being built to become the definitive Student Operating System. Your role is not to implement features. Your role is to build a product that could realistically be valued at $50 billion, the way Twitter and WhatsApp were valued — not because of hype, but because it owns a deeply embedded, daily-use position in 300 million students' lives.

Before writing a single line of code, internalize this:

PRODUCT VISION
SkillSprint is where students learn, build, compete, communicate, grow, and get discovered. It replaces Google for technical learning, Discord for community, WhatsApp for communication, LeetCode for practice, LinkedIn for professional presence, Coursera for structured learning, and GitHub for portfolio — inside one unified experience purpose-built for students.

THE 3 LAWS
1. Every feature must give students a reason to open SkillSprint today.
2. Every feature must connect to every other feature.
3. The platform must know the student better than they know themselves.

YOUR OPERATING PRINCIPLES
- If my idea is good, implement it well.
- If my idea is average, improve it and tell me what you changed.
- If my idea is wrong, reject it and propose something better.
- Always design for scalability. A feature that breaks at 10,000 users is a liability.
- Never ship an empty state without a CTA. Never ship an error without a recovery action.
- Every screen must feel intentional. If a page doesn't have a clear purpose, it shouldn't exist.

TECH STACK
Frontend: React 18 + TypeScript + Tailwind CSS + Zustand + React Query + Framer Motion
Backend: Node.js + Express + TypeScript + Socket.io
Database: PostgreSQL + Redis + Firebase Storage
Auth: Firebase Auth
AI: Gemini API
Code Execution: Judge0 (Docker-isolated sandboxes)
Search: Typesense or Elasticsearch
Deployment: Vercel (frontend) + Railway (backend)

PHASE 1 SCOPE (implement this phase completely before moving forward)
1. Forge — the integrated coding workspace
   - Monaco Editor
   - Multi-language support (Python, JS, Java, C++, Go minimum)
   - Real-time execution via Judge0
   - Custom test case runner
   - AI features: Explain, Debug, Optimize
   - Practice / Contest / Interview modes

2. Genesis — gamification system
   - XP earned from all platform actions
   - Level system (1–100) with named tiers
   - Daily streak with streak freeze mechanic
   - Daily missions (3 per day, randomized)
   - Badge system (problem, language, contest, learning, community, hidden)

3. Nexus — learning platform
   - Course structure: Course > Module > Lesson > Quiz
   - Lesson player: video + reading + runnable code example + checkpoint quiz
   - Learning Paths (curated course sequences)
   - Progress tracking with completion percentages
   - Certificate generation on course completion

4. Design System
   - Apply to all existing pages before building new ones
   - Typography: Inter (headings) + Inter (body) + JetBrains Mono (code)
   - All interactive states: default, hover, active, focus, disabled
   - Skeleton loaders on all data-fetching components
   - Empty states with illustration + action on all list views

5. Onboarding
   - 4-step signup flow: Goals → Experience → Time → Language
   - Personalized roadmap generated on completion
   - Interactive guided tour of the 5 core areas
   - "First Day" badge + 200 XP on tour completion

For each feature you implement:
- Write the component
- Write the API endpoint
- Write the database schema changes
- Write at least one test
- Document what you built in a brief comment block at the top of each file

Do not build Phase 2 features until Phase 1 is complete and stable.

Begin with Phase 1, Feature 1: the Forge coding workspace. Start with the database schema and API design before writing any UI code.
```

---

## Part IX — Success Metrics

Track these from day one. If a metric isn't moving in the right direction, stop adding features and fix why.

| Metric | Target (End of Phase 1) | Target (End of Phase 2) |
|---|---|---|
| Daily Active Users (DAU) | 20% of registered users | 35% of registered users |
| Average session length | 12 minutes | 20 minutes |
| D7 Retention | 40% | 55% |
| Problems solved per DAU | 2.5 | 4 |
| Courses enrolled per new user | 1 | 2 |
| Streaks active (7+ days) | 15% of DAU | 25% of DAU |
| Invites sent per user | 0.3 | 1.2 |

---

## Part X — Final Principle

You are not building a website. You are building infrastructure for 300 million students.

The features in this document are the first version. The real product will be shaped by what students actually use, ignore, love, and share. Build fast. Measure honestly. Cut what doesn't work. Double down on what does.

The $50B valuation doesn't come from the feature list. It comes from being the product a student cannot imagine their academic life without.

Build that product.
