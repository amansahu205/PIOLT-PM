# APP_FLOW.md — Application Flow & Navigation

> **Version**: 1.0 | **Last Updated**: March 28, 2026
> **Project**: PilotPM
> **Reference**: PRD.md v1.0

---

## 0. How to Use This Document

This document maps every screen, decision point, and state in PilotPM. When building any UI or backend logic that involves navigation, routing, or state transitions — reference this doc first.

**AI Usage:** Provide this doc when implementing any flow. Say: *"Implement [Flow Name] as specified in APP_FLOW.md, Section 3."*

**Auth note:** No Auth0. No OAuth. Hackathon uses hardcoded demo credentials stored in `.env`. One role: PM (the only user type). Keep it simple, keep it working.

---

## 1. Entry Points

### Primary Entry Points

| Entry Point | URL / Trigger | First Screen | Auth Required? |
|---|---|---|---|
| Direct URL | `pilotpm.vercel.app/` | Landing page (immersive scroll) | No |
| App link | `pilotpm.vercel.app/app` | Dashboard (if authed) or Login | Yes → redirect to /login |
| Deep link | `pilotpm.vercel.app/app/[route]` | Requested screen | Yes → redirect to /login?redirect_to=[route] |
| Phone call | Twilio number +1 (203) 555-PILOT | Voice agent (no UI) | No — phone handles identity |

### Secondary Entry Points

| Entry Point | Source | Notes |
|---|---|---|
| Devpost link | YHack judging page | Lands on landing page `/` |
| QR code on slides | Demo presentation | Lands on landing page `/` |
| GitHub README link | GitHub repo | Lands on landing page `/` |

---

## 2. Authentication Gate

> PilotPM uses hardcoded demo credentials. No Auth0, no OAuth, no email verification. One PM user. Session stored in localStorage as a JWT signed with `APP_SECRET` from `.env`.

```
USER ARRIVES AT ANY /app/* ROUTE
│
├── IF: localStorage has valid JWT (not expired)
│   └── PROCEED to requested route
│
├── IF: localStorage has expired JWT
│   ├── Clear localStorage
│   └── REDIRECT to /login?redirect_to=[requested_url]
│       └── After successful login → REDIRECT to saved destination
│
├── IF: No JWT in localStorage
│   ├── Save redirect_to param
│   └── REDIRECT to /login
│       └── After successful login → REDIRECT to /app/dashboard
│
└── IF: User arrives at /login while already authenticated
    └── REDIRECT to /app/dashboard
```

### Demo Credentials

```
Email:    pm@pilotpm.demo
Password: pilotpm2026
```

These are hardcoded in `.env` as `DEMO_EMAIL` and `DEMO_PASSWORD`. No database. No hashing needed for demo.

---

## 3. Core User Flows

---

### Flow 1: Login (F-001 prerequisite)

**Goal**: PM authenticates to access the dashboard
**Trigger**: Arriving at `/login` unauthenticated
**Frequency**: Once per session
**Entry Point**: `/login`
**Exit Points**: `/app/dashboard` (success), stays on `/login` (failure)

#### Happy Path

| Step | Screen | User Action | System Response | Next State |
|---|---|---|---|---|
| 1 | `/login` | Page loads | Show login form, focus email field | Login form visible |
| 2 | `/login` | Types email + password | Real-time: no validation until submit | Fields filled |
| 3 | `/login` | Clicks "Sign in" | Disable button, show spinner | Loading state |
| 4 | `/login` | — | Compare against `.env` credentials | Match found |
| 5 | `/login` | — | Generate JWT, store in localStorage | JWT stored |
| 6 | Redirect | — | Navigate to `/app/dashboard` or `redirect_to` | Dashboard loads |

#### Error States

| Error | Trigger | Display | Recovery |
|---|---|---|---|
| Wrong credentials | Email or password doesn't match `.env` | Inline error below password: "Incorrect email or password" | User re-types |
| Empty fields | Submit with blank email or password | Inline: "Email is required" / "Password is required" | User fills fields |
| Network error | Fetch fails | Toast: "Connection error. Check your internet and try again." | Retry button re-enables |

#### Edge Cases

- User hits Enter in password field: triggers form submit
- User arrives from `/app/blockers`: after login, redirects back to `/app/blockers`

---

### Flow 2: Async Standup Digest (F-001)

**Goal**: PM gets full team status without holding a meeting
**Trigger**: Dashboard load (auto-runs at 9am) OR manual "Refresh digest" button
**Frequency**: Daily
**Entry Point**: `/app/standup`
**Exit Points**: Digest displayed (success), partial digest with warning (degraded), error state (failure)

#### Happy Path

| Step | Screen | User Action | System Response | Next State |
|---|---|---|---|---|
| 1 | `/app/standup` | Page loads | Show loading skeletons | Skeleton state |
| 2 | `/app/standup` | — | Agent fetches GitHub commits (last 24hrs) | Fetching GitHub |
| 3 | `/app/standup` | — | Agent fetches Slack messages (#engineering) | Fetching Slack |
| 4 | `/app/standup` | — | Agent fetches Monday.com ticket updates | Fetching Monday |
| 5 | `/app/standup` | — | Gemini synthesizes per-engineer digest | Synthesizing |
| 6 | `/app/standup` | — | Digest rendered — 3 engineer cards with status | Populated state |
| 7 | `/app/standup` | Reads digest | Sources listed under each card | Digest complete |
| 8 | `/app/standup` | Clicks "Post to Slack" | Opens review queue with draft Slack message | Review queue opens |
| 9 | `/app/review` | Clicks "Approve" | Slack message posted to #standup-digest | Success toast |

#### Data Sources Shown Per Engineer Card

Each card shows:
- **Did**: commits merged, tickets closed (from GitHub + Monday.com)
- **Working on**: open PRs, in-progress tickets (from GitHub + Monday.com)
- **Status badge**: On track / Blocked / Check in (from Slack signal + inactivity detection)
- **Sources**: "4 commits · 2 Monday updates · 1 Slack message"

#### Error States

| Error | Trigger | Display | Recovery |
|---|---|---|---|
| GitHub API down | 503 / timeout | Yellow warning banner: "GitHub unavailable — digest from Slack + Monday.com only" | Partial digest shown |
| Slack API down | 503 / timeout | Yellow warning banner: "Slack unavailable — digest from GitHub + Monday.com only" | Partial digest shown |
| All APIs down | All 3 fail | Full error state: "Unable to fetch team data. Check your API connections in Settings." | Retry button |
| Lava / LLM down | Lava forward unreachable | Toast / error; optional Gemini direct if `GEMINI_API_KEY` set | Partial or cached digest per guardrails |
| No engineer activity in 24hrs | Zero commits / messages | Info banner: "No activity detected in the last 24 hours. Team may be off or in deep focus." | No action needed |

#### Edge Cases

- **New engineer added mid-sprint**: appears in digest if they have any GitHub/Slack activity
- **Engineer on holiday with no activity**: card shows "No activity — possibly OOO" with check-in flag
- **Digest already generated today**: shows cached version with timestamp, "Refresh" button to regenerate
- **PM clicks "Post to Slack" twice**: second click disabled after first approval; toast: "Already posted today"

---

### Flow 3: Blocker Radar (F-002)

**Goal**: PM detects and resolves blockers before they cost engineer time
**Trigger**: Continuous background monitoring — new blockers surface in dashboard badge and `/app/blockers`
**Frequency**: Continuous (polled every 15 minutes)
**Entry Point**: `/app/blockers` or blocker badge in sidebar
**Exit Points**: Blocker resolved (ping sent + ticket created), blocker dismissed, blocker deferred

#### Happy Path

| Step | Screen | User Action | System Response | Next State |
|---|---|---|---|---|
| 1 | Any page | — | Background poll detects: PR #143 open 48hrs, 0 reviews | Badge in sidebar shows "3" |
| 2 | `/app/blockers` | Clicks sidebar item | Page loads with 3 blocker cards sorted by severity | Populated state |
| 3 | `/app/blockers` | Reads blocker card | Card shows: who blocked, how long, what's blocking, draft ping | Card visible |
| 4 | `/app/blockers` | Clicks "Ping @mike" | Review queue opens with pre-drafted Slack message | Review queue |
| 5 | `/app/review` | Edits message (optional) | Inline text edit enabled | Edited message |
| 6 | `/app/review` | Clicks "Approve" | Slack DM sent to @mike, blocker ticket created in Monday.com | Success state |
| 7 | `/app/blockers` | — | Blocker card moves to "In progress" section | Card state updated |

#### Blocker Detection Rules (rendered in UI)

| Signal | Threshold | Severity | Draft Action |
|---|---|---|---|
| PR open with 0 reviews | > 48 hours | Critical | Ping code owner to review |
| Slack message with blocking language | Any time | Critical | Ping the person who can unblock |
| Engineer with 0 commits | > 24 hours | Watch | Soft check-in message |
| Ticket in "In Progress" with 0 activity | > 3 days | Medium | Check-in with ticket assignee |

#### Error States

| Error | Trigger | Display | Recovery |
|---|---|---|---|
| Slack send fails | API error | Toast: "Ping failed — Slack may be down. Try again in a few minutes." | Retry button on blocker card |
| Monday.com ticket creation fails | API error | Toast: "Blocker ticket not created — Monday.com unreachable. Ping was still sent." | Manual retry for ticket only |
| False positive dismissed | PM clicks "Not a blocker" | Card removed, reason modal (optional) | Confirmation toast: "Dismissed" |
| All APIs unavailable | Network down | Full error state with retry | Retry button |

#### Edge Cases

- **PM dismisses all 3 blockers**: empty state shows "No active blockers. Team is unblocked." with green indicator
- **Same blocker detected twice**: deduplication by PR number / engineer + signal type — only one card shown
- **Blocker resolved externally** (engineer commits): card auto-removed on next poll with toast "Blocker resolved ✓"
- **PM approves ping to themselves**: allowed — no validation; PM manages their own team

---

### Flow 4: Sprint Autopilot (F-003)

**Goal**: PM approves a complete sprint plan in < 5 minutes
**Trigger**: PM navigates to `/app/sprint` OR 2 days before sprint end (banner appears)
**Frequency**: Every 2 weeks
**Entry Point**: `/app/sprint`
**Exit Points**: Sprint approved + pushed to Monday.com (success), sprint saved as draft (abandoned), error state

#### Happy Path

| Step | Screen | User Action | System Response | Next State |
|---|---|---|---|---|
| 1 | `/app/sprint` | Page loads | Agent pulls backlog from Monday.com (18 tickets) | Loading skeleton |
| 2 | `/app/sprint` | — | K2 Think V2 scores each ticket (impact × effort) | Scored list appears |
| 3 | `/app/sprint` | — | Agent calculates velocity per engineer from GitHub | Velocity shown per engineer |
| 4 | `/app/sprint` | — | Draft sprint assembled: 12 tickets, 94% capacity | Draft sprint tab visible |
| 5 | `/app/sprint` | Reviews draft | Sees ticket scores, assignments, capacity bar | All visible |
| 6 | `/app/sprint` | Unchecks "Dashboard v2" | Ticket removed, capacity bar updates to 81% | Updated capacity |
| 7 | `/app/sprint` | Reassigns ticket to Sarah | Dropdown assignment change | Assignment updated |
| 8 | `/app/sprint` | Clicks "Approve sprint" | Confirm modal: "Push Sprint 25 to Monday.com?" | Confirm modal |
| 9 | Confirm modal | Clicks "Confirm" | Sprint pushed to Monday.com, ceremonies booked in Calendar | Success state |
| 10 | `/app/sprint` | — | Success banner: "Sprint 25 live in Monday.com. 4 ceremonies booked in Calendar." | Complete |

#### Scoring Display

Each ticket shows:
- **Score**: 1–100 with color (red 0–30 / amber 31–60 / green 61–100)
- **Reasoning**: 1-sentence from K2 Think V2 (e.g., "Blocks 3 tickets, 2-day fix, critical path")
- **Assigned to**: Engineer name with avatar initials
- **Story points**: Estimated by K2 Think V2
- **Status**: Selected / Deferred

#### Error States

| Error | Trigger | Display | Recovery |
|---|---|---|---|
| Backlog empty | Monday.com has 0 tickets | Empty state: "No backlog tickets found. Add tickets to Monday.com first." | Link to Monday.com |
| < 5 tickets | Monday.com has 1–4 tickets | Warning banner: "Low backlog — sprint may be under-capacity" | Proceed with what exists |
| K2 Think V2 unavailable | API timeout | Yellow banner: "Using Gemini for scoring — K2 unavailable" | Scores generated, slightly less detailed |
| Monday.com push fails | API error | Toast: "Push failed — Monday.com may be down. Sprint saved as draft." | Retry push button |
| Calendar booking fails | Google Calendar API error | Toast: "Sprint approved. Calendar booking failed — please add ceremonies manually." | Sprint still approved |

#### Edge Cases

- **PM approves sprint mid-sprint**: warning modal "A sprint is already active (Sprint 24). Start Sprint 25 anyway?" with explicit confirm
- **Velocity data unavailable** (new project): defaults to 8 pts/engineer with orange warning: "No velocity history — using default estimate of 8 pts per engineer"
- **Engineer on leave**: if engineer has a "OOO" event in Calendar → agent automatically reduces their capacity to 0 and notes it
- **Browser closes during approval**: sprint saved as draft in MongoDB, restored on next visit with banner "You have an unsaved sprint draft"

---

### Flow 5: Auto Status Reports (F-004)

**Goal**: Weekly stakeholder email drafted and sent with zero PM writing
**Trigger**: Every Friday 5pm (scheduled) OR manual "Generate now" button
**Frequency**: Weekly
**Entry Point**: `/app/reports`
**Exit Points**: Email sent (success), email saved as draft (abandoned), error with partial report

#### Happy Path

| Step | Screen | User Action | System Response | Next State |
|---|---|---|---|---|
| 1 | `/app/reports` | Page loads (or Friday 5pm trigger) | Agent pulls closed tickets (GitHub + Monday.com) | Loading state |
| 2 | `/app/reports` | — | Agent pulls merged PRs, resolved blockers | Still loading |
| 3 | `/app/reports` | — | Hex API generates sprint velocity + burn-down dashboard | Hex chart rendered |
| 4 | `/app/reports` | — | Gemini writes stakeholder update draft | Draft appears |
| 5 | `/app/reports` | Reads draft | Sees: shipped items, metrics, blockers resolved, next week | Draft visible |
| 6 | `/app/reports` | Edits one line inline | Text field becomes editable on click | Edited |
| 7 | `/app/reports` | Clicks "Send to stakeholders" | Review queue opens with email preview | Review queue |
| 8 | `/app/review` | Clicks "Approve" | Gmail MCP sends email, Hex dashboard link embedded | Email sent |
| 9 | `/app/reports` | — | Success: "Report sent to 3 stakeholders · [View sent email]" | Complete |

#### Report Structure (auto-generated)

```
Subject: PilotPM Engineering Update — Week of [Date]

Shipped this week:
• [ticket names from Monday.com + GitHub]

Key metrics:
• Sprint velocity: X pts (vs Y pts last sprint)
• PRs merged: N
• Blockers resolved: N

Next week focus:
• [Top 3 tickets from current sprint]
```

#### Error States

| Error | Trigger | Display | Recovery |
|---|---|---|---|
| Hex API unavailable | Timeout | Yellow banner: "Analytics unavailable — plain report generated" | Report sent without chart link |
| Gmail MCP fails | API error | Toast: "Email send failed. Report saved as draft." | Retry send button |
| No shipped tickets this week | 0 closed tickets | Report includes: "No tickets closed this week — sprint in progress" | Sent as-is |
| Gemini unavailable | Lava down | Toast: "AI unavailable — generating template report" | Fill-in template shown instead |

#### Edge Cases

- **PM edits draft heavily**: all edits tracked in MongoDB for future improvement
- **Friday 5pm trigger fires but PM hasn't reviewed**: report saved as draft, banner appears on next login: "Your Friday report is ready to review"
- **Multiple stakeholder emails**: comma-separated in `.env` as `STAKEHOLDER_EMAILS`
- **PM sends twice**: second send blocked with toast: "This week's report was already sent on [time]. Send again?"

---

### Flow 6: Voice Calling Agent (F-005)

**Goal**: PM calls a phone number and gets live project answers
**Trigger**: PM dials +1 (203) 555-PILOT from any phone
**Frequency**: On-demand (multiple times per day)
**Entry Point**: Physical phone call — no UI required
**Exit Points**: Call ends naturally, PM hangs up, network failure

#### Happy Path

| Step | What Happens | System Response |
|---|---|---|
| 1 | PM dials number | Twilio receives inbound call |
| 2 | Twilio streams audio | ElevenLabs Conversational AI answers within 2 rings |
| 3 | ElevenLabs greets | "Hey, this is PilotPM. What do you need to know about the project?" |
| 4 | PM asks: "What's blocking my team?" | ElevenLabs STT transcribes question |
| 5 | — | Backend fetches live context from GitHub + Monday.com + standup cache |
| 6 | — | Gemini generates answer < 20 seconds when spoken |
| 7 | ElevenLabs TTS speaks answer | "You have 3 blockers. Sarah is waiting on AWS keys from Mike..." |
| 8 | PM asks follow-up | Natural multi-turn conversation continues |
| 9 | PM says "Thanks, bye" or hangs up | Call ends, transcript logged to MongoDB |

#### Questions Agent Can Answer

| Question | Data Source | Expected Answer Shape |
|---|---|---|
| "What's blocking my team?" | Blocker radar cache | Lists blockers by engineer, severity, duration |
| "Give me the sprint summary" | Monday.com current sprint | Velocity, open tickets, days remaining |
| "How is [name] doing?" | Standup digest cache | What they did, what they're on, any blockers |
| "What shipped this week?" | GitHub PRs + Monday closed tickets | List of shipped items |
| "When is sprint ending?" | Monday.com sprint dates | X days remaining |

#### Error States

| Error | Trigger | What Caller Hears |
|---|---|---|
| Gemini / Lava down | Lava gateway unreachable | "I'm having trouble reaching the AI. Using cached data from [time]. [Answer from cache]." |
| GitHub / Monday down | API error | "I couldn't refresh the latest data. Based on my last update at [time]: [cached answer]" |
| Question not understood | Low confidence | "I didn't quite catch that. Could you rephrase? You can ask about blockers, sprint status, or how a specific engineer is doing." |
| Network drops mid-call | Twilio disconnect | Call ends — no answer given. PM calls back normally. |
| Agent has no data at all | Cold start, APIs all down | "I don't have current project data right now. Please check the dashboard at pilotpm.vercel.app." |

#### Edge Cases

- **Call from unrecognized number**: no auth — anyone who has the number can call (demo feature, not production concern)
- **Call during active call**: Twilio queues; second caller hears hold music (default Twilio behavior)
- **PM asks about something outside scope** (e.g., "what's the weather?"): "I'm specialized in your project status. I can help with blockers, sprint updates, and engineer status."

---

### Flow 7: Review Queue (F-011)

**Goal**: PM reviews all pending agent actions before execution
**Trigger**: Any agent workflow generates an action
**Frequency**: Multiple times per day
**Entry Point**: `/app/review` or badge click in sidebar
**Exit Points**: All actions approved/rejected (queue empty), PM navigates away (actions persist)

#### Happy Path

| Step | Screen | User Action | System Response | Next State |
|---|---|---|---|---|
| 1 | Any page | — | Agent generates action (e.g., Slack ping) | Sidebar badge increments |
| 2 | `/app/review` | Clicks badge / sidebar | Page shows pending actions grouped by workflow | Queue populated |
| 3 | `/app/review` | Reads action card | Sees: action type, description, agent reasoning trail | Card expanded |
| 4 | `/app/review` | Edits Slack message | Inline text edit, character count shown | Edited version |
| 5 | `/app/review` | Checks/unchecks individual actions | Checkboxes update selection | Selection updated |
| 6 | `/app/review` | Clicks "Approve selected (3)" | Actions execute in parallel | Loading on each card |
| 7 | `/app/review` | — | Each card shows ✓ or ✗ result | Result state |
| 8 | `/app/review` | — | Successfully executed items fade out | Queue shrinks |

#### Error States

| Error | Trigger | Display | Recovery |
|---|---|---|---|
| Action execution fails | API error mid-approval | Card turns red: "Failed to execute — Slack may be down. Retry?" | Per-card retry button |
| PM approves empty queue | No actions checked | Button disabled with tooltip: "Select at least one action" | Select actions |
| Action becomes stale | Data changed since draft | Yellow badge on card: "Data may be outdated — agent drafted this 2hrs ago" | PM decides to approve or re-run |

---

## 4. Navigation Map

```
ROOT (/)
├── /                               [Public] — Immersive scroll landing page
│   ├── #hero                       Veo video + headline
│   ├── #standup                    Workflow 1 section
│   ├── #blockers                   Workflow 2 section
│   ├── #sprint                     Workflow 3 section
│   ├── #reports                    Workflow 4 section
│   ├── #voice                      Workflow 5 + Stitch images
│   └── #sponsors                   Sponsor logos
│
├── /login                          [Public — redirect to /app/dashboard if authed]
│
└── /app                            [Auth Required — redirect to /login if no JWT]
    ├── /app/dashboard              [Default post-login view]
    ├── /app/standup                [F-001] Standup digest
    ├── /app/blockers               [F-002] Blocker radar
    ├── /app/sprint                 [F-003] Sprint autopilot
    ├── /app/reports                [F-004] Status reports
    ├── /app/backlog                [F-010] Backlog AI (P1)
    ├── /app/voice                  [F-005] Voice agent info + transcript log
    └── /app/review                 [F-011] Human review queue
```

### Navigation Rules

| Rule | Specification |
|---|---|
| Default unauthenticated redirect | `/login?redirect_to=[requested_url]` |
| Default post-login redirect | `/app/dashboard` or `redirect_to` param |
| Back button | Browser default; form data preserved on `/app/sprint` and `/app/review` |
| Hash navigation on landing | Smooth scroll to section anchor |
| Active nav item | Highlighted in sidebar based on current route |

---

## 5. Screen Inventory

---

### Screen: Landing Page

| Property | Value |
|---|---|
| **Route** | `/` |
| **Access** | Public |
| **Purpose** | Impress judges and Devpost reviewers; explain PilotPM in < 2 minutes of scrolling |

**Key Sections:**
- Hero: Headline + Veo demo video (autoplay muted) + "Try PilotPM" CTA
- 5 workflow sections (immersive scroll, one per P0 feature)
- Stitch-generated product visuals in each section
- Voice agent section with phone number prominently displayed
- Sponsor logos footer

**User Actions:**

| Action | Leads To | Condition |
|---|---|---|
| Click "Try PilotPM" CTA | `/app/dashboard` or `/login` | Authenticated → dashboard; else → login |
| Click sponsor logo | External sponsor URL | Always |
| Scroll through sections | Smooth scroll animation | Always |

**State Variants:**

| State | Trigger | Display |
|---|---|---|
| Default | Page load | Full immersive scroll, Veo video autoplays muted |
| Video unavailable | Veo video fails to load | Static hero image (Stitch-generated) shown instead |

---

### Screen: Login

| Property | Value |
|---|---|
| **Route** | `/login` |
| **Access** | Public (redirects to dashboard if already authed) |
| **Purpose** | Single authentication screen for PM demo account |

**Key UI Elements:**
- PilotPM logo + wordmark
- Email field (pre-filled with `pm@pilotpm.demo` for demo)
- Password field with show/hide toggle
- "Sign in" button
- Subtle: "Demo credentials: pm@pilotpm.demo / pilotpm2026" shown below form

**State Variants:**

| State | Trigger | Display |
|---|---|---|
| Default | Page load | Empty form, focus on email |
| Loading | Submit clicked | Button shows spinner, fields disabled |
| Error | Wrong credentials | Inline error below password field |
| Success | Correct credentials | Brief success state → redirect |

---

### Screen: Dashboard

| Property | Value |
|---|---|
| **Route** | `/app/dashboard` |
| **Access** | Authenticated |
| **Purpose** | Morning briefing — full team status at a glance without any meetings |

**Key UI Elements:**
- "Good morning, [name]" + sprint info header
- 3 stat cards: active blockers / PRs awaiting review / sprint velocity
- Today's AI digest (per-engineer cards)
- Quick action buttons: "Call voice agent" / "View blockers"

**State Variants:**

| State | Trigger | Display |
|---|---|---|
| Loading | Initial page load | Skeleton cards (3 stat cards + 3 engineer skeletons) |
| Populated | Data loaded | Full digest with engineer cards |
| Empty | No engineer activity in 24hrs | "No team activity detected yet today" with refresh button |
| Degraded | Partial API failure | Yellow banner + partial data with warning labels |
| Error | All APIs failed | Full error state + retry button |

---

### Screen: Standup Feed

| Property | Value |
|---|---|
| **Route** | `/app/standup` |
| **Access** | Authenticated |
| **Purpose** | Detailed standup digest with per-engineer cards, source citations, and Slack post action |

**State Variants:**

| State | Trigger | Display |
|---|---|---|
| Loading | Page load / refresh | 3 skeleton engineer cards |
| Generating | Agent synthesizing | Progress steps visible: "Reading GitHub... Reading Slack... Synthesizing..." |
| Populated | Digest ready | 3 engineer cards with status badges and source citations |
| Cached | Digest already run today | Cached digest shown with "Generated at [time]" + "Refresh" button |
| Degraded | 1–2 sources unavailable | Digest shown with yellow source warnings |
| Error | All sources failed | "Unable to generate digest" + retry |

---

### Screen: Blocker Radar

| Property | Value |
|---|---|
| **Route** | `/app/blockers` |
| **Access** | Authenticated |
| **Purpose** | Real-time blocker visibility + one-click resolution pings |

**State Variants:**

| State | Trigger | Display |
|---|---|---|
| Loading | Page load | 3 skeleton blocker cards |
| Populated | Blockers exist | Cards sorted: Critical → Medium → Watch |
| Empty | No blockers | Green state: "No active blockers. Team is unblocked." + green dot |
| All resolved | PM resolves all | Same empty/green state with "Last resolved: [time ago]" |
| Error | API failure | "Blocker detection unavailable. Check API connections." |

---

### Screen: Sprint Planner

| Property | Value |
|---|---|
| **Route** | `/app/sprint` |
| **Access** | Authenticated |
| **Purpose** | AI-drafted sprint for PM review and approval |

**Tabs:**
- "AI draft" — scored tickets with assignments
- "Velocity data" — per-engineer capacity stats

**State Variants:**

| State | Trigger | Display |
|---|---|---|
| Loading | Page load | Progress steps: "Fetching backlog... Scoring tickets... Calculating velocity..." |
| Draft ready | AI done | Full sprint board with scores, assignments, capacity bar |
| Edited | PM unchecks/reassigns | Capacity bar updates live |
| Confirm modal | PM clicks "Approve" | Modal: "Push Sprint [N] to Monday.com and book ceremonies?" |
| Success | Approved + pushed | Banner: "Sprint [N] live. Ceremonies booked in Calendar." |
| Error — push failed | Monday.com down | Toast: "Push failed. Sprint saved as draft." + retry |

---

### Screen: Status Reports

| Property | Value |
|---|---|
| **Route** | `/app/reports` |
| **Access** | Authenticated |
| **Purpose** | Auto-generated weekly stakeholder email — review and send |

**Tabs:**
- "This week" — compiled metrics and shipped items
- "Stakeholder email" — editable draft email

**State Variants:**

| State | Trigger | Display |
|---|---|---|
| Loading | Page load / generation trigger | Progress: "Compiling shipped work... Generating report... Building Hex dashboard..." |
| Generated | Report ready | Metrics cards + Hex chart + email draft |
| Edited | PM edits email inline | Edited text highlighted in draft |
| Sent | PM approves | Success banner: "Report sent to [N] stakeholders · [View sent email]" |
| Already sent | Report exists for this week | Banner: "This week's report was sent on [date/time]" + "Send again" option |
| No data | 0 shipped this week | Report generated with "Sprint in progress" language |

---

### Screen: Backlog AI (P1)

| Property | Value |
|---|---|
| **Route** | `/app/backlog` |
| **Access** | Authenticated |
| **Purpose** | Priority-scored backlog with K2 Think V2 reasoning and Hex matrix |

**State Variants:**

| State | Trigger | Display |
|---|---|---|
| Loading | Page load | Skeleton ticket list |
| Scored | K2 done | Ranked list with scores + Hex 2×2 matrix |
| Empty | No backlog | "No tickets in backlog. Add items to Monday.com." |
| Error | K2 or Monday.com down | Fallback: unscored list with retry button |

---

### Screen: Voice Agent

| Property | Value |
|---|---|
| **Route** | `/app/voice` |
| **Access** | Authenticated |
| **Purpose** | Show phone number, sample questions, and live call transcript log |

**Key UI Elements:**
- Phone number prominently displayed: "+1 (203) 555-PILOT"
- Sample questions list (3 examples)
- Live call transcript feed (last 5 calls from MongoDB)
- "Data agent has access to" section showing connected sources

**State Variants:**

| State | Trigger | Display |
|---|---|---|
| Idle | No active call | Phone number + sample questions + past transcripts |
| Active call | Twilio webhook fires | "Call in progress" live indicator + real-time transcript streaming |
| No transcripts | First use | "No calls yet — dial the number to try it" |

---

### Screen: Review Queue

| Property | Value |
|---|---|
| **Route** | `/app/review` |
| **Access** | Authenticated |
| **Purpose** | Centralized approval gate for all agent actions |

**State Variants:**

| State | Trigger | Display |
|---|---|---|
| Loading | Page load | Skeleton action cards |
| Populated | Pending actions exist | Action cards grouped by workflow type |
| Executing | PM clicks approve | Per-card loading spinners |
| Partial success | Some actions fail | Green ✓ and red ✗ per card |
| Empty | All approved / rejected | "Queue empty. All actions reviewed." + green indicator |

---

## 6. Decision Points (Conditional Logic)

```
# Auth check on every /app/* route
IF localStorage.jwt is null OR jwt.exp < Date.now()
  THEN REDIRECT /login?redirect_to=[current_route]
  AND clear localStorage
ELSE
  PROCEED to requested route

# Standup digest freshness
IF today's digest exists in MongoDB (created_at > 6am today)
  THEN show: cached digest with "Generated at [time]" label
  AND show: "Refresh" button to regenerate
ELSE
  THEN run: full digest generation pipeline

# Blocker card action routing
IF blocker.type === "pr_stale"
  THEN draft_ping targets: PR reviewers (from GitHub CODEOWNERS)
ELSE IF blocker.type === "slack_signal"
  THEN draft_ping targets: person mentioned in Slack message
ELSE IF blocker.type === "inactivity"
  THEN draft_ping targets: engineer's direct manager (PM in this case)

# Sprint planning velocity fallback
IF engineer.github_merges_last_3_sprints.count < 3
  THEN use: default 8 story points per sprint
  AND show: orange warning "No velocity history — using default estimate"
ELSE
  THEN use: average of last 3 sprint velocities

# K2 Think V2 availability
IF K2_Think_V2_API responds within 10 seconds
  THEN use: K2 for scoring
  AND show: "Scored by MBZUAI K2 Think V2"
ELSE
  THEN use: Lava (general LLM chain) as fallback
  AND show: yellow badge "Scored by backup model (K2 unavailable)"

# Lava / Lava gateway availability
IF Lava forward responds within 3s
  THEN route: general AI inference via Lava (primary then fallback model)
ELSE IF GEMINI_API_KEY configured
  THEN route: optional Gemini direct last resort
ELSE
  THEN show: error / cached data path per product rules
  AND show: toast "AI gateway unavailable"

# Review queue action execution
IF action.type === "slack_message"
  THEN call: Slack API post_message
ELSE IF action.type === "monday_board"
  THEN call: Monday.com MCP create_board
ELSE IF action.type === "calendar_event"
  THEN call: Google Calendar MCP create_event
ELSE IF action.type === "gmail_send"
  THEN call: Gmail MCP send_email

# Status report send guard
IF report.sent_this_week === true AND user.clicks_send_again === false
  THEN show: "Already sent on [date]" toast
  AND show: "Send again" secondary button
ELSE IF user.confirms_send_again === true
  THEN proceed: with send

# Sprint approval guard
IF sprint.current_is_active === true AND user.approves_new_sprint
  THEN show: warning modal "Sprint [N] is still active. Start [N+1] anyway?"
  IF user.confirms
    THEN proceed: with push
  ELSE
    THEN cancel: return to sprint page

# Voice agent fallback context
IF mongodb.standup_cache.age < 2 hours
  THEN use: cached standup digest as context
ELSE IF github.api.available
  THEN refresh: context before answering
ELSE
  THEN use: stale cache with spoken disclaimer "My last update was [time] ago"

# Sidebar badge count
badge_count = 
  review_queue.pending_actions.count
IF badge_count > 0
  THEN show: red badge with count
ELSE
  THEN hide: badge
```

---

## 7. Global Error Handling

### HTTP Error Responses from PilotPM Backend

| Error | Route | Display | User Actions |
|---|---|---|---|
| 401 Unauthorized | Redirect to `/login` | Clears JWT, saves redirect_to | Log in again |
| 404 Not Found | Inline in app | "This page doesn't exist — [Go to dashboard]" | Navigate home |
| 429 Too Many Requests | Inline toast | "You're moving fast. Wait a few seconds and try again." | Auto-retry after 5s |
| 500 Server Error | Inline in page | "Something went wrong on our end. [Retry] or [Go to dashboard]" | Retry / navigate |
| 503 Service Unavailable | Inline in page | "PilotPM is temporarily unavailable. [Retry]" | Retry |

### Toast System

| Type | Duration | Position | Trigger Examples |
|---|---|---|---|
| Success (green) | 3s auto-dismiss | Top-right | "Sprint approved", "Email sent", "Ping delivered" |
| Error (red) | 6s or manual dismiss | Top-right | "Push failed — Monday.com may be down", "Email send failed" |
| Warning (amber) | 5s auto-dismiss | Top-right | "Using cached data — GitHub unavailable", "K2 unavailable — using Gemini |
| Info (blue) | 4s auto-dismiss | Top-right | "Using cloud AI — Lava offline", "Digest already generated today" |

### Specific Error Copy (exact strings)

```
GitHub unavailable:
  "GitHub unavailable — digest based on Slack + Monday.com only"

All sources unavailable:
  "Unable to fetch team data. Check your API connections in Settings."

Gemini / Lava down:
  "Local AI unavailable — trying cloud fallback"

Monday.com push failed:
  "Push failed — Monday.com may be down. Sprint saved as draft."

Gmail send failed:
  "Email send failed. Report saved as draft."

Hex unavailable:
  "Analytics dashboard unavailable — plain report sent"

Wrong credentials (login):
  "Incorrect email or password"

Empty field (login):
  "Email is required" / "Password is required"

Already sent (status report):
  "This week's report was already sent on [weekday] at [time]. Send again?"

Voice agent — unknown question:
  "I didn't quite catch that. You can ask about blockers, sprint status, or how a specific engineer is doing."
```

### Offline Handling

```
ON: navigator.onLine === false
  SHOW: sticky top banner "You're offline — changes won't sync until reconnected"
  DISABLE: all submit / approve buttons (tooltip: "You're offline")
  READ-ONLY: dashboard and standup feed show cached data

ON: connection restored
  HIDE: offline banner
  SHOW: toast "Back online" (3s)
  RE-ENABLE: all action buttons
```

---

## 8. Interaction Patterns

### Form Submission (Login + Sprint Edit)

```
1. User fills form
2. Validation: runs on submit only (not on keystroke — reduces noise)
3. User submits:
   a. Validate client-side
   b. IF errors → show inline messages below each field, focus first error
   c. IF valid → disable submit, show spinner on button
4. API call:
   a. SUCCESS → redirect or update UI
   b. ERROR (validation) → inline server errors on relevant fields
   c. ERROR (network) → toast + re-enable submit button
5. Never clear form data on error (preserve user input)
```

### Optimistic Updates (Blocker dismiss, Review queue approve)

```
1. User clicks "Approve" or "Dismiss"
2. Immediately: card animates out (opacity → 0, height → 0, 200ms)
3. Send API request in background
4. IF success: no UI change needed (already removed)
5. IF failure: card animates back in + toast error + retry button
   "Action failed — [card name] restored"
```

### Review Queue Batch Approval

```
1. All checkboxes default to checked
2. User unchecks items they don't want
3. "Approve selected (N)" button shows count reactively
4. On click:
   a. Each checked item executes in parallel (Promise.all)
   b. Each card shows individual loading spinner
   c. On resolve: green ✓ or red ✗ per card
   d. Green cards fade out after 1.5s
   e. Red cards stay with retry button
5. IF all succeed: toast "All [N] actions executed ✓"
6. IF some fail: toast "3 of 4 actions executed. 1 failed — see queue."
```

### Inline Edit (Status Report Email)

```
1. Email body renders as styled read-only text
2. On hover: subtle edit cursor appears
3. On click: field becomes contenteditable, cursor placed at click position
4. On blur or Escape: save edit to local state (not API — only saved on "Approve")
5. Visual indicator: edited sections highlighted with subtle underline
6. "Reset to original" button appears after any edit
```

### Sprint Capacity Bar

```
REACTIVE: Updates on every checkbox change without API call
capacity_used = sum(story_points of checked tickets)
capacity_total = sum(engineer velocities)
percentage = (capacity_used / capacity_total) * 100

COLOR:
  < 80%  → green   "Under capacity — consider adding tickets"
  80–95% → normal  no warning
  > 95%  → amber   "Near capacity"
  > 100% → red     "Over capacity — deselect some tickets"
```

### Modal Pattern (Sprint Approval Confirm)

```
OPEN: Triggered by "Approve sprint" click
  → Background: darken (rgba 0,0,0,0.4)
  → Modal: slides up 200ms ease-out
  → Focus: trapped inside modal
  → Body scroll: locked

CLOSE triggers:
  → "Cancel" button
  → ESC key
  → DO NOT close on outside click (destructive action — require explicit confirm)

BUTTONS:
  Primary: "Confirm — Push Sprint [N]" (purple)
  Secondary: "Cancel" (outline)
```

---

## 9. Responsive Behavior

### Layout Breakpoints

| Breakpoint | Width | Navigation | Layout |
|---|---|---|---|
| Mobile | < 640px | Hidden sidebar → hamburger menu | Single column |
| Tablet | 640–1024px | Collapsed sidebar (icons only) | 2-column where space allows |
| Desktop | > 1024px | Full sidebar with labels | Full layout |

### Per-Screen Responsive Behavior

| Screen | Desktop | Mobile |
|---|---|---|
| Landing page | Side-by-side sections | Stacked sections, video full-width |
| Dashboard | 3-column stat cards + digest | Single column, cards stack |
| Standup feed | 3 engineer cards side-by-side | Cards stack vertically |
| Blocker radar | Full-width cards with side-by-side action | Stacked, buttons below content |
| Sprint planner | Table-style ticket list | Card-per-ticket, swipe to deselect |
| Status reports | Split: metrics left + email right | Stacked tabs |
| Review queue | Action cards with side reasoning panel | Reasoning collapsible below action |

### Mobile-Specific Notes

- Voice agent screen: phone number displayed in `tel:` link (tap to call directly)
- Sprint approval confirm modal: full-screen bottom sheet on mobile
- Review queue: "Approve all" sticky button at bottom of screen

---

## 10. Animation & Transition Spec

| Transition | Duration | Easing | Notes |
|---|---|---|---|
| Page navigation (route change) | 150ms | ease-in-out | Fade only — no slide (reduces motion sickness) |
| Sidebar nav active state | 100ms | ease-out | Background color change |
| Card appear (digest loaded) | 200ms | ease-out | Fade in, no slide |
| Card dismiss (optimistic update) | 200ms | ease-in | Opacity 1→0 + height collapse |
| Card restore (failed action) | 250ms | ease-out | Reverse of dismiss |
| Skeleton → content | 200ms | ease-in | Cross-fade |
| Modal open | 200ms | ease-out | Slide up from y+20 → y+0 + fade in |
| Modal close | 150ms | ease-in | Fade out |
| Toast appear | 200ms | ease-out | Slide in from right |
| Toast dismiss | 150ms | ease-in | Slide out to right |
| Button press feedback | 80ms | ease-in | Scale 0.97 |
| Sprint capacity bar update | 300ms | ease-in-out | Width transition (reactive) |
| Landing page scroll sections | Triggered by IntersectionObserver | ease-out | Elements fade + translate Y +20→0 |
| Review queue badge count | 150ms | ease-out | Number transition |

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
    animation: none !important;
  }
}
```

All Veo video autoplays respect `prefers-reduced-motion: reduce` — video paused, static poster shown instead.

---

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | March 28, 2026 | Aman | Initial — all 10 sections, all P0 flows |
