# CLAUDE.md — AI Assistant Guide for Reginald-Wilson Repository

## Repository Overview

This is a personal profile repository for **Reginald Wilson**, a real estate professional and entrepreneur based in Dallas-Fort Worth, Texas. It is a documentation-only repository — there is no application code, build system, or test suite.

## Repository Structure

```
Reginald-Wilson/
├── README.md      # Personal bio and professional profile
└── CLAUDE.md      # This file — AI assistant guidance
```

## About This Repository

| Property | Value |
|---|---|
| Type | Personal profile / documentation |
| Language | Markdown only |
| Frameworks | None |
| Dependencies | None |
| Tests | None |
| Build system | None |
| CI/CD | None |

## Git Conventions

- **Default branch**: `main`
- **Working branch pattern**: `claude/<task-description>-<session-id>`
- Commit messages should be short and descriptive (e.g., `Update README.md`)
- The repository has two commits in history; keep commits focused and meaningful

## Content Conventions

Since this is a profile/documentation repository, any changes should:

1. **Maintain factual accuracy** — only update information that is verifiably correct about Reginald Wilson
2. **Use plain Markdown** — no HTML, no complex formatting; keep it readable in plain text
3. **Keep a professional tone** — appropriate for a real estate professional's public profile
4. **No code files** — this repo is documentation only; do not add application code, scripts, or build configs without explicit instruction

## Subject Background (from README)

- **Name**: Reginald Wilson
- **Location**: Dallas-Fort Worth, Texas (born and raised in New Orleans, LA)
- **Profession**: Licensed real estate agent since 2004
- **Self-description**: "Unicorn Agent"
- **Real estate activities**: Property flipping, fix-and-hold for co-living, wholesale
- **Other business**: Estate Sales Liquidation Company
- **Personal**: Married to Annette Wilson since 1998, three children, enjoys traveling

## Common Tasks for AI Assistants

### Updating the profile
- Edit `README.md` directly — there is no build step required
- Commit changes with a descriptive message
- Push to the working branch or `main` as directed

### Adding new sections to the README
- Use standard Markdown headers (`##`, `###`)
- Keep sections short and scannable
- Do not add technical jargon unless explicitly asked

### Reviewing content
- Check for typos, spelling, and factual consistency with known profile details
- Note: the current README has a minor typo — "togther" should be "together" (fix only if asked)

## What AI Assistants Should NOT Do

- Do not add application code, scripts, or configuration files unless explicitly requested
- Do not assume this will become a software project and pre-emptively scaffold one
- Do not push to `main` directly without explicit permission — use the designated `claude/` branch
- Do not alter factual personal details (dates, names, locations) without user confirmation

## Branch & Push Instructions

Always work on the designated `claude/` branch:

```bash
git add <files>
git commit -m "Descriptive commit message"
git push -u origin <branch-name>
```

If push fails due to a network error, retry with exponential backoff (2s, 4s, 8s, 16s).
