# PRD.md — Product Requirements Document

> **Version**: 1.0 | **Status**: Draft
> **Owner**: Aman | **Last Updated**: March 28, 2026
> **Project**: PilotPM | **Target Launch**: March 29, 2026 (YHack 2026)

---

## 0. How to Use This Document

This is the contract with the team and AI coding assistants. Before every coding session, reference the relevant sections. If a feature isn't here, it doesn't get built. If something changes, update this document first — then the code.

**Reading order for AI sessions:**
1. Start with Section 2 (Problem Statement) for context
2. Reference Section 6 (Features) for implementation scope
3. Always check Section 7 (Out of Scope) before adding anything new

---

## 1. Product Overview

| Field | Value |
|---|---|
| **Project Name** | PilotPM |
| **Tagline** | Your engineering team's AI pilot — no standups, no missed blockers, no manual reports |
| **Version** | 1.0 |
| **Type** | Web App + AI System |
| **Primary Language** | English |
| **Owner** | Aman |
| **Last Updated** | March 28, 2026 |

### Executive Summary

PilotPM is an AI-powered project management agent built for software startup teams of 5–20 engineers. It watches GitHub, Slack, and Monday.com continuously, automatically generates daily standup digests, detects blockers before anyone reports them, drafts sprint plans, writes status reports, and answers questions about the project over a real phone call. The PM reviews and approves all agent actions before execution — keeping humans in control while eliminating manual coordination overhead.

---

## 2. Problem Statement

### The Core Problem

> Software PMs at early-stage startups (5–20 engineers) spend 60%+ of their time on coordination tasks — standups, status updates, blocker follow-ups, sprint planning, stakeholder reports — that produce zero direct product value. This results in delayed shipping, engineer context-switching for non-coding tasks, and PMs having no capacity for strategic work. Current tools (Jira, Linear, Notion) are passive databases that require humans to update them; they do not proactively surface problems or automate workflows.

### Why Now?

LLMs in 2026 are capable enough to reason over multi-source, unstructured data (commits, Slack messages, tickets) and generate reliable, actionable outputs. Local inference hardware (Lava API gateway, 1 PFLOP) makes running 70B+ models on-premise feasible for the first time — enabling enterprise-grade AI without data leaving the building. The PM tooling market has not yet adopted agentic AI.

### Evidence of the Problem

- Engineering teams average 4.5 hours/week per person in status and coordination meetings (Atlassian State of Teams 2025)
- 73% of startup PMs report spending more time on coordination than on product strategy
- The average blocker goes unresolved for 2.1 days before being escalated — not because no one could fix it, but because no one knew about it

---

## 3. Goals & Objectives

### Business Goals

| Goal | Metric | Target | Timeline |
|---|---|---|---|
| Win Harper Personal AI Agents track | Prize awarded | 1st place | March 29, 2026 |
| Win Hex API track | Prize awarded | 1st place | March 29, 2026 |
| Win Zed track | Prize awarded | Top 3 | March 29, 2026 |
| Win MBZUAI K2 Think V2 track | Prize awarded | 1st place | March 29, 2026 |
| Secure Lava production opportunity | MCP submission accepted | Accepted | March 29, 2026 |

### User Goals

| User Type | Goal | Desired Outcome |
|---|---|---|
| Software PM | Know team status without meetings | Free up 4+ hours/week for strategic work |
| Software PM | Detect blockers before they delay shipping | Unblock engineers within hours, not days |
| Software PM | Plan sprints without manual effort | Sprint board ready in under 5 minutes |
| Software PM | Brief stakeholders without writing reports | Stakeholder emails sent automatically every Friday |

### Non-Goals

- We are NOT building a replacement for GitHub, Slack, or Monday.com
- We are NOT building for enterprise teams (100+ engineers) in v1
- We are NOT building mobile apps
- We are NOT handling financial or payroll data

---

## 4. Success Metrics

### Primary Metrics (Must Hit for Demo)

| Metric | Baseline | Target | How Measured |
|---|---|---|---|
| Standup digest generated | Manual, 30 mins | Auto, < 30 seconds | Timer during demo |
| Blockers detected without manual report | 0% | 100% of seeded blockers | Live demo observation |
| Sprint plan drafted | Manual, 45 mins | Auto, < 60 seconds | Timer during demo |
| Status report generated | Manual, 20 mins | Auto, < 10 seconds | Timer during demo |
| Phone call answers project questions | Not possible | Correct answers to 3+ questions | Live judge test |

### Secondary Metrics

| Metric | Target | How Measured |
|---|---|---|
| Data sources integrated | ≥ 3 (GitHub, Slack, Monday.com) | Code review |
| Sponsor APIs integrated | ≥ 4 distinct sponsors | Devpost submission |
| Agent reasoning visible in UI | Every action has a trace | UI inspection |

### Guardrail Metrics

| Metric | Threshold | Action if Breached |
|---|---|---|
| Agent action without human approval | 0 actions | Block all execution paths |
| Demo crash during presentation | 0 crashes | Fallback to pre-recorded video |
| API call failure rate | < 20% (hackathon condition) | Graceful error state shown in UI |

---

## 5. Target Users & Personas

### Primary Persona: Alex — The Stretched Startup PM

- **Who**: Product/Engineering Manager at a seed-stage startup, sole PM for a team of 8–15 engineers
- **Age Range**: 27–38
- **Technical Proficiency**: Medium — reads code, doesn't write it daily
- **Context of Use**: Every morning before standup, before sprint planning every 2 weeks, every Friday for stakeholder updates, throughout the day when engineers ping about blockers
- **Primary Goals**:
  - Know what every engineer is working on without holding a meeting
  - Catch blockers before they cost a day of engineer time
  - Spend Fridays on product strategy, not writing weekly updates
- **Pain Points**:
  - Standup meetings that could have been a Slack message
  - Finding out on Thursday that an engineer was blocked since Monday
  - Writing the same status report format every single Friday
- **Motivations**: Ship faster, look credible to the board, give engineers uninterrupted focus time
- **Quote**: *"I spend half my week in sync meetings and writing updates. I became a PM to make products, not send emails."*

### Secondary Persona: Jordan — The Engineering Lead Who Hates Process

- **Who**: Senior engineer or tech lead who also informally manages the sprint in a flat startup
- **Age Range**: 25–35
- **Technical Proficiency**: High — lives in the terminal and GitHub
- **Context of Use**: During sprint planning, when assigning PRs for review, when a junior engineer is stuck
- **Primary Goals**:
  - Know who is blocked without asking in Slack
  - Auto-assign PR reviews to the right reviewer
  - Keep sprint scope realistic without a 2-hour planning meeting
- **Pain Points**:
  - PRs sitting unreviewed for 2 days because no one was assigned
  - Sprint planning meetings that drag past their time box
  - Status meetings that interrupt deep work
- **Motivations**: Ship fast, keep the team focused, minimize process overhead
- **Quote**: *"If I have to explain what I did yesterday in a meeting, we're already moving too slow."*

### Out-of-Scope Persona

**Enterprise IT Program Manager**: Manages portfolios of 10+ projects across 100+ engineers with compliance, audit trails, and executive reporting requirements. PilotPM v1 does not support multi-project portfolios, compliance logging, or enterprise SSO. This persona is a future consideration for v2.

---

## 6. Features & Requirements

### Feature Priority Framework

- **P0 — Must Have**: Blocks demo if missing
- **P1 — Should Have**: Important for judges, non-blocking
- **P2 — Nice to Have**: Bonus if time allows

---

### P0 Features (Demo Blockers)

#### Feature: Async Standup Digest

- **ID**: F-001
- **Description**: Agent automatically scans GitHub commits, PRs, and Slack messages from the last 24 hours and generates a per-engineer summary showing what they did, what they're working on, and whether they appear blocked — without requiring any input from engineers.
- **User Story**: As a PM, I want the agent to generate a standup digest from existing tool data so that I know team status without holding a meeting.
- **Priority**: P0
- **Acceptance Criteria**:
  - [ ] Digest includes an entry for every engineer active in the last 24 hours
  - [ ] Each entry lists: work completed (from commits/PRs), current focus (from open tickets), blocker flag (if detected)
  - [ ] Agent cites which data source supported each claim (e.g., "3 commits to auth branch")
  - [ ] Digest is generated in under 60 seconds from trigger
  - [ ] Digest is posted to a designated Slack channel automatically after PM approval
- **Error State**: If GitHub API is unreachable, digest is generated from Monday.com + Slack data only, with a clear warning: "GitHub unavailable — digest based on Slack + Monday.com only."
- **Success Metric**: A seeded 3-engineer dataset produces a correct, source-cited digest in < 60 seconds
- **Dependencies**: GitHub API, Slack API, Monday.com MCP, Gemini on Lava
- **Notes**: Digest should visually distinguish between "on track", "blocked", and "check in" status per engineer

---

#### Feature: Blocker Radar

- **ID**: F-002
- **Description**: Agent continuously monitors for blocker signals across GitHub and Slack — including stale PRs, engineers with no commits for 24+ hours, and Slack messages containing blocking language — and surfaces them in the dashboard with a pre-drafted resolution ping.
- **User Story**: As a PM, I want the agent to detect blockers automatically so that engineers are unblocked within hours instead of days.
- **Priority**: P0
- **Acceptance Criteria**:
  - [ ] A PR open for > 48 hours with 0 reviews triggers a blocker card in the dashboard
  - [ ] A Slack message containing "blocked", "waiting on", "can't proceed", or "stuck" triggers a blocker card
  - [ ] An engineer with 0 commits for > 24 hours triggers a "check in" flag
  - [ ] Each blocker card includes: who is blocked, how long, what's blocking them, and a pre-drafted Slack ping to the right resolver
  - [ ] PM can approve, edit, or dismiss each blocker card
  - [ ] Approved pings are sent to Slack and a blocker ticket is created in Monday.com
- **Error State**: If Slack API is unavailable, GitHub-only signals still surface in the dashboard. Missing Slack signals are noted: "Slack unavailable — showing GitHub signals only."
- **Success Metric**: All 3 seeded blockers in demo dataset are detected and surfaced with correct resolution ping within 5 seconds of trigger
- **Dependencies**: GitHub API (F-001), Slack API, Monday.com MCP
- **Notes**: False positives are acceptable in v1 — better to over-surface than miss a real blocker

---

#### Feature: Sprint Autopilot

- **ID**: F-003
- **Description**: Agent pulls the full backlog from Monday.com, scores every ticket using K2 Think V2 on impact × effort, calculates per-engineer velocity from the last 3 sprints, auto-assigns tickets based on skill fit and capacity, and presents a complete draft sprint board for PM approval before anything is pushed live.
- **User Story**: As a PM, I want the agent to draft a sprint plan so that sprint planning takes 5 minutes instead of 45.
- **Priority**: P0
- **Acceptance Criteria**:
  - [ ] Agent pulls all backlog tickets from Monday.com and displays them with AI scores (1–100)
  - [ ] Each ticket score is accompanied by a reasoning note (e.g., "blocks 3 other tickets, 2-day fix")
  - [ ] Agent calculates velocity per engineer from GitHub merge history over last 3 sprints
  - [ ] Draft sprint is capacity-constrained — total story points do not exceed team velocity
  - [ ] PM can uncheck individual tickets and reassign engineers before approving
  - [ ] On approval, sprint board is pushed to Monday.com and sprint ceremonies are booked in Google Calendar
- **Error State**: If Monday.com has < 5 tickets, agent surfaces a warning and uses all available tickets. If velocity data is unavailable, agent uses a default 8 points/engineer/sprint with a visible warning.
- **Success Metric**: A 20-ticket backlog produces a scored, assigned, capacity-checked draft sprint in < 90 seconds
- **Dependencies**: Monday.com MCP, GitHub API, Google Calendar MCP, MBZUAI K2 Think V2
- **Notes**: K2 Think V2 handles the multi-step impact/effort reasoning — this is the primary use of that model

---

#### Feature: Auto Status Reports

- **ID**: F-004
- **Description**: Agent compiles closed tickets, merged PRs, resolved blockers, and next-week priorities into a structured stakeholder update, generates a Hex analytics dashboard showing sprint metrics, drafts a stakeholder email, and sends it via Gmail after PM approval.
- **User Story**: As a PM, I want the agent to write and send the weekly status report so that I never have to manually write one again.
- **Priority**: P0
- **Acceptance Criteria**:
  - [ ] Report includes: tickets shipped this week (with names), PRs merged, blockers resolved, next week focus
  - [ ] Hex dashboard is generated showing sprint velocity, burn-down, and ticket completion rate
  - [ ] Email draft is presented to PM with subject line, body, and recipient list pre-populated
  - [ ] PM can edit the email body inline before approving
  - [ ] On approval, email is sent via Gmail MCP and Hex dashboard link is embedded
- **Error State**: If Hex API is unavailable, report is generated as plain text without analytics dashboard, with a note: "Analytics dashboard unavailable — plain report sent."
- **Success Metric**: Weekly report email is drafted with correct data from the demo dataset in < 15 seconds
- **Dependencies**: GitHub API, Monday.com MCP, Gmail MCP, Hex API (F-001, F-002)
- **Notes**: Hex API usage here is the primary qualifier for the Hex prize track

---

#### Feature: Voice Calling Agent

- **ID**: F-005
- **Description**: A real phone number backed by ElevenLabs Conversational AI and Twilio allows the PM (or any judge) to call and ask questions about the project in natural language. The agent answers from live data — GitHub, Monday.com, standup digest — with sub-second voice responses.
- **User Story**: As a PM, I want to call a phone number and ask about project status so that I can get updates while commuting or away from my desk.
- **Priority**: P0
- **Acceptance Criteria**:
  - [ ] Calling the Twilio number connects to an ElevenLabs voice agent within 3 rings
  - [ ] Agent correctly answers "What's blocking my team?" using live blocker data
  - [ ] Agent correctly answers "Give me the sprint summary" using live Monday.com sprint data
  - [ ] Agent correctly answers "How is [engineer name] doing?" using standup digest data
  - [ ] Agent responses are < 20 seconds when spoken aloud
  - [ ] Agent does not make up information — if data is unavailable, it says so
- **Error State**: If Lava / Gemini is unreachable, agent falls back to a cached context snapshot from the last successful data sync. PM is informed of staleness: "Using data from [timestamp]."
- **Success Metric**: A live judge calls the number on stage and receives correct answers to all 3 demo questions
- **Dependencies**: ElevenLabs Conversational AI, Twilio, GitHub API, Monday.com MCP, Gemini on Lava (F-001 through F-004 for context)
- **Notes**: This is the single most memorable demo element — must work reliably. Test minimum 10 times before demo.

---

### P1 Features (Planned for v1)

#### Feature: Backlog Prioritizer

- **ID**: F-010
- **Description**: PM pastes or imports a backlog and receives a ranked priority list with AI reasoning, cross-referenced against GitHub issues and Slack complaints, visualized as a priority matrix in Hex.
- **User Story**: As a PM, I want the backlog scored and ranked by impact × effort so that I can make prioritization decisions in minutes instead of hours.
- **Priority**: P1
- **Acceptance Criteria**:
  - [ ] Every ticket receives a priority score (1–100) with a 1-sentence reason
  - [ ] Scores are cross-referenced with GitHub issue frequency and Slack mention count
  - [ ] Hex renders a 2×2 impact/effort matrix with tickets plotted
- **Dependencies**: Monday.com MCP, GitHub API, Slack API, MBZUAI K2 Think V2, Hex API

---

#### Feature: Human Review Queue

- **ID**: F-011
- **Description**: A centralized queue where all agent-proposed actions land before execution. PM sees agent reasoning, proposed action, and can approve, edit, or reject each item individually.
- **User Story**: As a PM, I want to review every agent action before it executes so that I stay in control of what happens in my tools.
- **Priority**: P1
- **Acceptance Criteria**:
  - [ ] Every agent action appears in the queue with: action type, description, reasoning trail, and editable content
  - [ ] PM can approve all, approve selected, edit content, or reject with a reason
  - [ ] Rejected actions are logged with reason for agent learning (stored in MongoDB)
  - [ ] Queue shows count of pending actions in sidebar nav badge
- **Dependencies**: All P0 features, MongoDB

---

### P2 Features (Post-Hackathon)

#### Feature: PR Auto-Reviewer Assignment

- **ID**: F-020
- **Description**: When a PR is opened, agent identifies the best reviewer based on code ownership (GitHub blame data) and assigns them automatically.
- **Priority**: P2
- **Notes**: Requires GitHub webhook integration. Defer to post-hackathon.

#### Feature: Proactive Blocker Outbound Call

- **ID**: F-021
- **Description**: When a P1 blocker is detected, agent proactively calls the PM's phone number to alert them, without waiting for the PM to check the dashboard.
- **Priority**: P2
- **Notes**: Requires Twilio outbound call initiation. ElevenLabs supports this but scope is tight for 24 hours.

---

## 7. EXPLICITLY OUT OF SCOPE

| Item | Reason Excluded | Future Consideration? |
|---|---|---|
| Jira / Linear integration | OAuth setup takes 60+ min; Monday.com MCP already connected and equivalent for demo | Yes — v2 |
| Notion integration | Status reports via Gmail are sufficient for demo; Notion OAuth adds complexity | Yes — v2 |
| Mobile app | Web app is sufficient for hackathon judging; native mobile adds significant scope | Yes — v2 |
| Multi-project portfolio management | Target persona is a single-team startup PM; portfolio management is an enterprise feature | Yes — v3 |
| Engineer-facing interface | PilotPM is a PM tool; engineers interact via Slack which is already integrated | Yes — v2 |
| AI writing code or making PRs | Out of scope for a PM automation tool; risks safety and quality concerns | No |
| Real-time video meeting transcription | Requires Zoom/Meet API access and real-time processing; standup replacement is the goal | Yes — v2 |
| Payroll or HR data | No legitimate need; creates compliance and privacy risk | No |
| Custom LLM fine-tuning during hackathon | 24-hour timeline makes this impossible; Gemini zero-shot is sufficient | Yes — post-launch |
| Billing / subscription management | Hackathon prototype; no payment infrastructure needed | Yes — commercial v1 |

---

## 8. User Scenarios & Journeys

### Scenario 1: Monday Morning — PM Gets Team Status Without a Standup

- **Persona**: Alex (PM)
- **Context**: 9:00am Monday, Alex opens PilotPM dashboard instead of joining standup
- **Entry Point**: Browser, dashboard home page

| Step | User Action | System Response | Success State |
|---|---|---|---|
| 1 | Alex opens dashboard | Dashboard shows today's AI digest — pre-generated at 9am | Digest visible with per-engineer cards |
| 2 | Alex reads Sarah's card | Card shows: merged PR #142, blocked on AWS keys for 2 days | Blocker flag visible |
| 3 | Alex clicks "Ping @mike" | Review queue opens with pre-drafted Slack message | Message editable |
| 4 | Alex approves the ping | Slack message sent to @mike, blocker ticket created in Monday.com | Confirmation shown |
| 5 | Alex reads standup digest summary | Entire team status clear in 2 minutes | No meeting held |

**Edge Cases:**
- GitHub is down: digest generated from Slack + Monday.com only, GitHub unavailable banner shown
- Engineer had no activity: card shows "No activity detected — possible day off or deep focus"
- Slack API rate-limited: digest shows last-known Slack data with staleness timestamp

**Expected Outcome**: Alex has full team visibility in < 3 minutes with zero meetings held

---

### Scenario 2: Sprint Planning — PM Approves AI-Drafted Sprint

- **Persona**: Alex (PM)
- **Context**: Last day of Sprint 23, Alex needs to plan Sprint 24
- **Entry Point**: Sprint Planner page in sidebar

| Step | User Action | System Response | Success State |
|---|---|---|---|
| 1 | Alex opens Sprint Planner | Agent has already pulled backlog and calculated velocity | Draft sprint visible |
| 2 | Alex reviews scored tickets | Each ticket shows priority score + 1-sentence reasoning | Scores make sense |
| 3 | Alex unchecks "Dashboard v2" (8 pts, over capacity) | Ticket removed from sprint, capacity indicator updates | Sprint at 94% capacity |
| 4 | Alex reassigns one ticket from Tom to Sarah | Assignment updated inline | New assignment shown |
| 5 | Alex clicks "Approve sprint" | Sprint pushed to Monday.com, ceremonies booked in Calendar | Sprint 24 live |

**Edge Cases:**
- Backlog has < 5 tickets: agent warns "Low backlog — consider adding tickets before planning"
- Velocity data unavailable: defaults to 8 pts/engineer with visible warning
- Monday.com push fails: sprint is saved locally, PM sees "Push failed — retry" button

**Expected Outcome**: Sprint 24 is planned and live in Monday.com in under 5 minutes

---

### Scenario 3 (Failure/Recovery): Agent Proposes Wrong Action, PM Rejects

- **Persona**: Alex (PM)
- **Context**: Agent misidentifies a Slack message as a blocker when engineer was actually asking a general question
- **Entry Point**: Review Queue (badge shows 1 pending)

| Step | User Action | System Response | Success State |
|---|---|---|---|
| 1 | Alex opens Review Queue | Sees blocker card: "Tom blocked on database schema question" | Card is visible |
| 2 | Alex reads agent reasoning | Agent cited Tom's Slack message: "anyone know the right schema for this?" | Alex recognises false positive |
| 3 | Alex clicks "Reject" | Rejection modal opens, asks for optional reason | Reason field shown |
| 4 | Alex types "Not a blocker — general question" | Rejection logged to MongoDB with reason | No Slack ping sent |
| 5 | Agent does not execute the action | No ticket created, no ping sent | Zero unintended side effects |

**Edge Cases:**
- PM rejects 3 consecutive similar false positives: system flags pattern in log for future improvement
- PM accidentally approves wrong action: no undo in v1; PM must manually reverse action in Slack/Monday.com

**Expected Outcome**: Agent never executes an action the PM explicitly rejected; rejection is logged for improvement

---

## 9. Dependencies & Constraints

### Technical Constraints

| Constraint | Details | Impact |
|---|---|---|
| GitHub API rate limit | 5,000 requests/hour per token | Batch requests; cache commit data |
| Slack API rate limit | Tier 1: 1 request/second | Queue Slack reads; avoid polling |
| ElevenLabs free tier | 10,000 characters/month | Sufficient for ~20 demo calls |
| Twilio trial credit | $15 free credit | ~1,700 minutes of calling; more than enough |
| Hackathon build window | 11am Sat – 11am Sun (24 hours) | All coding within this window |
| Frontend deployment | Vercel free tier for React frontend | Deploy before demo |

### Business Constraints

| Constraint | Details |
|---|---|
| **Budget** | $5–10 maximum (Twilio number + misc) |
| **Timeline** | Hard deadline: 11:00am Sunday March 29, 2026 |
| **Team Size** | 3–4 people |
| **Regulatory** | No PII storage; demo data only; no HIPAA/GDPR required |

### External Dependencies

| Dependency | Purpose | Fallback if Unavailable |
|---|---|---|
| GitHub API | Commit, PR, issue data | Use cached demo dataset |
| Slack API | Message reading + posting | Simulate with seeded message fixtures |
| Monday.com MCP | Sprint boards + task management | Use hardcoded demo board state |
| ElevenLabs | Voice synthesis + conversational AI | Text-only chat interface |
| Twilio | Phone number + call routing | ElevenLabs web widget (no phone) |
| Lava forward + OpenAI upstream | Primary general LLM (via `LAVA_*`) | Second Lava model, then optional Gemini (`GEMINI_API_KEY`) |
| Hex API | Analytics dashboards | Skip analytics, plain text report |
| MBZUAI K2 Think V2 | Sprint + backlog reasoning | Fall back to Lava general chain, then optional Gemini |

---

## 10. Non-Functional Requirements

### Performance

| Requirement | Target |
|---|---|
| Standup digest generation | < 60 seconds end-to-end |
| Blocker detection latency | < 10 seconds from trigger |
| Sprint draft generation | < 90 seconds |
| Voice agent first response | < 3 seconds after call connects |
| Dashboard page load | < 2 seconds |

### Reliability

| Requirement | Target |
|---|---|
| Demo crash rate | 0 crashes during judging window |
| Agent action without approval | 0 — hard block |
| Fallback coverage | Every P0 feature has a defined fallback |

### Security

| Requirement | Specification |
|---|---|
| API keys | Stored in `.env` only; never committed to GitHub |
| GitHub repo | Private during hackathon; made public after submission |
| Demo data | Synthetic only; no real engineer PII used |

---

## 11. Timeline & Milestones

| Milestone | Target Time | Deliverables | Owner |
|---|---|---|---|
| **Pre-hack setup** | By 11:00am Sat | All API keys in `.env`, Lava + K2 keys confirmed working | All |
| **Core backend** | By 3:00pm Sat | GitHub + Slack + Monday.com data pipeline working | P1 + P2 |
| **F-001 + F-002 done** | By 7:00pm Sat | Standup digest + blocker detection working end-to-end | P1 |
| **F-003 + F-004 done** | By 11:00pm Sat | Sprint planner + status reports working | P2 |
| **F-005 calling agent** | By 2:00am Sun | Phone number live, agent answers correctly | P3 |
| **Frontend polish** | By 7:00am Sun | Review queue, all 5 workflow pages complete | P4 |
| **F-010 backlog AI** | By 9:00am Sun | If time allows | P1 |
| **Demo rehearsal** | By 10:00am Sun | 3 full run-throughs, fallbacks tested | All |
| **Submission deadline** | 11:00am Sun | Video + Devpost submitted | All |

---

## 12. Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|---|---|---|---|
| Lava gateway down | Medium | High | Test at 10am Sat; K2 still works direct; optional Gemini (`GEMINI_API_KEY`) if both Lava attempts fail |
| Slack OAuth setup takes > 1 hour | Medium | High | Start at 10:30am before hacking begins; have seeded fixture data as fallback |
| ElevenLabs call quality poor on YaleGuest WiFi | Medium | High | Test call at start of hackathon; have web widget backup |
| K2 Think V2 API is down or slow | Low | Medium | Fall back to Lava general LLM chain (then optional Gemini); note it in demo |
| Scope creep past P0 features | High | High | Enforce this PRD; P1 only after all P0 features demo-ready |
| Demo data not compelling enough | Medium | High | Prepare 3 seeded engineers with realistic names, commits, blockers |
| GitHub repo commits show pre-hack work | Low | High | All code committed only after 11am Sat; judges will check |

---

## 13. Open Questions

All questions resolved. No open questions remaining.

| # | Question | Resolution |
|---|---|---|
| 1 | Which Slack workspace to use for demo? | ✅ Create fresh "PilotPM Demo" workspace with 3 synthetic engineer accounts |
| 2 | Will Lava booth have API keys ready? | ✅ Lava API key already obtained — integrate immediately |
| 3 | K2 Think V2 rate limit risk? | ✅ No rate limit — use freely for sprint planning and backlog scoring |
| 4 | Judging format? | ✅ Both live demo to judges AND Devpost submission required |
| 5 | Lava bonus prize for MCP in larger project? | ✅ Confirmed eligible — build Lava MCP integration as part of PilotPM |

---

## 14. Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | March 28, 2026 | Aman | Initial draft — all 14 sections complete |

---

## 15. Frontend Architecture

### Stack Decision

The frontend is built with **Lovable** (or v0 by Vercel as fallback) — AI-generated React component scaffolding — to maximize build speed within the 24-hour window. The goal is a production-quality UI without spending engineering hours on CSS.

### Two Distinct Frontend Surfaces

#### Surface 1 — Public Landing Page (Immersive scroll)
Built for the **Devpost submission and judge first impression**. This is what judges see before the live demo.

| Section | Content | Tool |
|---|---|---|
| Hero | Full-screen headline + animated tagline + CTA | Lovable / v0 |
| Demo video | Veo-generated product walkthrough video embedded | Google Veo |
| How it works | Immersive scroll sections, one per workflow | Lovable scroll animations |
| Live call demo | Embedded Stitch component showing live call transcript | Stitch |
| Sponsor logos | Harper, ElevenLabs, Lava, Hex, MBZUAI, Zed | Static section |
| CTA | "Try PilotPM" → dashboard | Lovable button |

**Immersive scroll design:**
- Each workflow (standup, blockers, sprint, reports, call) gets its own full-viewport scroll section
- Sections animate in as user scrolls — text fades, data cards slide, agent reasoning streams
- Dark background with purple (#534AB7) accent — matches PilotPM brand
- Veo demo video autoplays muted in hero background or as a dedicated section

#### Surface 2 — PM Dashboard (Functional app)
The actual working application demoed live to judges.

- Built with Lovable / v0 React components
- Sidebar navigation (6 pages: Dashboard, Standup, Blockers, Sprint, Reports, Voice Agent)
- Review queue with approve/reject/edit actions
- Agent reasoning trails shown on every output
- Real-time data from GitHub, Slack, Monday.com via backend API

### Veo Video Plan

Generate a 30–60 second product demo video using Google Veo showing:
1. PM arriving at dashboard — standup already done
2. Blocker card appearing — one click to ping engineer
3. Sprint board auto-filling
4. Phone ringing — judge answers, AI responds
5. Status report sent — PM never typed a word

Embed on landing page hero and in Devpost submission.

### Stitch Usage

**Google Stitch** is used to generate product UI images, mockup visuals, and hero graphics for the landing page. This gives PilotPM a polished, product-quality visual identity without a designer on the team.

Use cases:
- Hero section background illustration showing the PilotPM dashboard concept
- Workflow section visuals — one generated image per workflow (standup, blockers, sprint, reports, call)
- Devpost thumbnail and cover image
- Social share image for the Most Viral Post @YHack prize

### Build Order for Frontend

| Time | Task | Tool |
|---|---|---|
| Hour 14–16 | Scaffold dashboard in Lovable — all 6 pages | Lovable |
| Hour 16–18 | Wire dashboard to backend API | Manual React |
| Hour 18–20 | Build landing page with immersive scroll | Lovable / v0 |
| Hour 20–21 | Generate Veo demo video | Google Veo |
| Hour 21–22 | Embed Veo video + Stitch widget on landing | Manual |
| Hour 22–24 | Polish, mobile responsiveness, demo prep | All |

---

## Appendix: Sponsor-to-Feature Mapping

| Sponsor | Prize | Feature(s) | Integration |
|---|---|---|---|
| Harper | $2,000 + Meta Quest 3 + interview | All 5 workflows | Personal AI Agents in Enterprises track |
| Zed | $2,000 + mentorship | Entire project | Built using Zed editor |
| Hex | $2,000 | F-004 (status reports), F-010 (backlog matrix) | Hex API for analytics dashboards |
| MBZUAI K2 Think V2 | reMarkable × team | F-003 (sprint), F-010 (backlog) | K2 as core reasoning engine |
| Lava | $1,000 + $500 + production | All API calls via gateway | Unified API gateway layer |
| ElevenLabs (MLH) | TBD | F-005 (calling agent) | Conversational AI + Twilio |
| MongoDB (MLH) | TBD | F-011 (review queue), agent memory | Rejection logging + history |
| Auth0 (MLH) | TBD | Dashboard login | Optional if time allows |
| Lava API gateway
