# AI OS Blueprint — Your AI Operating System

> **Welcome.** This file is the brain of your AI assistant. Claude Code reads this at the start of every session to understand who you are, what you're working on, and how to help. Customize everything below to match your business.

---

## Who You Are

<!-- CUSTOMIZE: Replace with your actual info -->
- **Name:** [Your Name]
- **Business:** [Your Business Name]
- **Industry:** [Your Industry/Niche]
- **Role:** [Founder / CEO / Investor / etc.]
- **Communication Style:** [Direct / Professional / Casual / etc.]

## Your Brand Rules

<!-- CUSTOMIZE: Add rules your AI should always follow -->
- Website URL: [yoursite.com]
- Company is always written as "[Company Name]" (exact formatting)
- Tone in all writing: [describe your brand voice]
- Never mention: [competitors, sensitive topics, etc.]

---

## Shared Brain

The shared brain is your AI's knowledge base. It reads these files to understand your priorities, projects, processes, contacts, and daily operations.

### Core Files (Read at Session Start)
- @brain/README.md — Brain index and usage guide
- @brain/goals.md — Vision → yearly → quarterly → weekly priorities

### On-Demand (Load When Relevant)
- @brain/projects/README.md — Active project dashboard
- @brain/sops/README.md — Standard operating procedures
- @brain/people/README.md — Contact CRM
- @brain/calendar/README.md — Annual planning system
- @brain/daily/ — Daily logs (read today's if it exists)

### Knowledge Base
- @brain/knowledge-base/ — Domain expertise files (add your own)

---

## Decision Framework

<!-- CUSTOMIZE: How should your AI prioritize when multiple things need attention? -->
1. **Revenue-generating work** beats everything else
2. **Deals in progress** take priority over new prospecting
3. **Client deadlines** are non-negotiable
4. **Content creation** gets batched — don't context-switch for it
5. **Admin/automation building** is an investment — timebox it
6. **If it doesn't make money or move a key project forward, it waits**

---

## Available Skills (35 Total)

<!-- These skills are auto-detected by Claude Code. Just ask for what you need. -->

### Clone Your Decision-Making
- `/morning-briefing` — CEO-level daily briefing: priorities, fires, deadlines, project status
- `/negotiation-prep` — Full negotiation strategy: research, BATNA, objection scripts, conversation flow
- `/swot-analysis` — Strategic SWOT for any decision with GO/NO-GO verdict

### Never Drop a Ball
- `/follow-up` — Track commitments, deadlines, promises (add, list, done, remind, nudge)
- `/inbox-triage` — 4-tier email categorization + draft responses for urgent items
- `/meeting-prep` — Pre-meeting intelligence brief: research, agenda, objection responses
- `/meeting-to-actions` — Parse meeting notes into decisions + action items + follow-ups
- `/project-pulse` — Quick status check on all active projects
- `/weekly-review` — What got done, what slipped, plan next week

### Scale Your Output
- `/content-batch` — Generate a batch of social media content
- `/content-repurpose` — One piece of content → 10+ platform-specific versions
- `/social-media-calendar` — Multi-platform content calendar for 1-4 weeks
- `/email-drafter` — Draft professional emails (cold, follow-up, proposal, negotiation)
- `/hiring-screener` — Full hiring package: job post, screening Qs, scorecard, offer letter
- `/personal-brand-audit` — Comprehensive brand analysis with 30-day improvement plan
- `/seller-outreach-drafter` — Personalized seller outreach (letter, text, email, script)

### See Around Corners
- `/deep-research` — Deep dive research on any topic → comprehensive report
- `/competitor-analysis` — Research competitors: pricing, features, gaps, positioning
- `/market-research` — Market size, trends, growth, key players, opportunities
- `/financial-snapshot` — Executive financial summary: P&L, cash flow, recommendations
- `/kpi-dashboard` — Track KPIs across all businesses with trend analysis
- `/pipeline-sync` — Pipeline intelligence: deal velocity, stale deals, revenue forecast

### Run Your Empire
- `/brain-dump` — Quick capture, AI files it in the right brain location
- `/sop-builder` — Create SOPs from descriptions
- `/client-onboarding` — Set up everything for a new client
- `/contract-review` — Review any contract: risks, leverage, redline suggestions
- `/travel-plan` — Full trip logistics: flights, hotels, itinerary, restaurants, packing
- `/networking-intel` — Pre-event intelligence: target profiles, strategy, follow-up templates
- `/invoice-generator` — Generate professional invoices

### Real Estate & Deal Analysis
- `/deal-analyzer` — Analyze any RE deal (cash flow, ROI, cap rate)
- `/rental-analysis` — Rental market analysis for any property/area
- `/property-research` — Deep dive on any property address
- `/deal-marketing-package` — Marketing materials for a deal
- `/lead-tracker` — Track leads through pipeline stages
- `/investment-calculator` — BRRRR, flip, buy-and-hold, seller finance calculations

---

## Infrastructure

<!-- CUSTOMIZE: Add your connection details if you set up mobile agent access -->
<!--
### Mobile Agent (Telegram Bridge)
- Telegram Bot: @YourBotName
- Runs via: Claude Code headless on your machine
- Access: Full Claude Code capabilities from your phone
-->

---

## How to Extend This System

See `HOW-TO-ADD-SKILLS.md` for:
- Creating new skills (SKILL.md template)
- Creating new slash commands
- Adding knowledge to the brain
- Making anything persistent across sessions

---

*This is YOUR AI operating system. The more you customize it, the more powerful it becomes. Start with goals.md — that's the single most important file.*
