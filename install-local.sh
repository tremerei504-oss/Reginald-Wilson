#!/bin/bash

# AI OS Blueprint — Local Install Script
# Reginald Wilson / Tremerealty LLC & Treme Estate Sales
#
# Usage: bash install-local.sh
# Run this from inside the cloned repo folder.

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
CLAUDE_MD="$HOME/CLAUDE.md"

echo ""
echo "============================================"
echo "   AI OS BLUEPRINT — LOCAL INSTALL"
echo "============================================"
echo ""

# Step 1: Create ~/.claude directories
echo "Creating directories..."
mkdir -p "$CLAUDE_DIR/brain/projects"
mkdir -p "$CLAUDE_DIR/brain/people"
mkdir -p "$CLAUDE_DIR/brain/sops"
mkdir -p "$CLAUDE_DIR/brain/daily"
mkdir -p "$CLAUDE_DIR/brain/calendar"
mkdir -p "$CLAUDE_DIR/brain/knowledge-base"
mkdir -p "$CLAUDE_DIR/brain/research"
mkdir -p "$CLAUDE_DIR/brain/pipeline/leads"
mkdir -p "$CLAUDE_DIR/brain/invoices"
mkdir -p "$CLAUDE_DIR/brain/drafts"
mkdir -p "$CLAUDE_DIR/skills"
mkdir -p "$CLAUDE_DIR/commands"
echo "  ✓ Directories ready"

# Step 2: Install brain files (never overwrite existing user data)
echo ""
echo "Installing brain files..."
if [ -d "$REPO_DIR/brain" ]; then
  # Copy README/template files (always overwrite — structural files)
  find "$REPO_DIR/brain" -name "README.md" | while read src; do
    rel="${src#$REPO_DIR/brain/}"
    dest="$CLAUDE_DIR/brain/$rel"
    mkdir -p "$(dirname "$dest")"
    cp "$src" "$dest"
  done

  # Copy user data files (never overwrite existing)
  find "$REPO_DIR/brain" -name "*.md" ! -name "README.md" | while read src; do
    rel="${src#$REPO_DIR/brain/}"
    dest="$CLAUDE_DIR/brain/$rel"
    mkdir -p "$(dirname "$dest")"
    if [ ! -f "$dest" ]; then
      cp "$src" "$dest"
    else
      echo "  SKIPPED (already exists): brain/$rel"
    fi
  done
  echo "  ✓ Brain files installed"
else
  echo "  WARNING: brain/ folder not found in repo"
fi

# Step 3: Install skills (skip if already exists)
echo ""
echo "Installing skills..."
SKILLS_INSTALLED=0
SKILLS_SKIPPED=0
if [ -d "$REPO_DIR/skills" ]; then
  for skill_dir in "$REPO_DIR/skills"/*/; do
    skill_name="$(basename "$skill_dir")"
    dest="$CLAUDE_DIR/skills/$skill_name"
    if [ ! -d "$dest" ]; then
      cp -r "$skill_dir" "$dest"
      SKILLS_INSTALLED=$((SKILLS_INSTALLED + 1))
    else
      SKILLS_SKIPPED=$((SKILLS_SKIPPED + 1))
    fi
  done
  echo "  ✓ Skills: $SKILLS_INSTALLED installed, $SKILLS_SKIPPED already existed"
else
  echo "  WARNING: skills/ folder not found in repo"
fi

# Step 4: Install commands (skip if already exists)
echo ""
echo "Installing commands..."
CMDS_INSTALLED=0
CMDS_SKIPPED=0
if [ -d "$REPO_DIR/commands" ]; then
  for cmd_file in "$REPO_DIR/commands"/*.md; do
    cmd_name="$(basename "$cmd_file")"
    dest="$CLAUDE_DIR/commands/$cmd_name"
    if [ ! -f "$dest" ]; then
      cp "$cmd_file" "$dest"
      CMDS_INSTALLED=$((CMDS_INSTALLED + 1))
    else
      CMDS_SKIPPED=$((CMDS_SKIPPED + 1))
    fi
  done
  echo "  ✓ Commands: $CMDS_INSTALLED installed, $CMDS_SKIPPED already existed"
else
  echo "  WARNING: commands/ folder not found in repo"
fi

# Step 5: Install CLAUDE.md
echo ""
echo "Installing CLAUDE.md..."
if [ -f "$CLAUDE_MD" ]; then
  cp "$REPO_DIR/CLAUDE.md" "$HOME/CLAUDE.md.ai-os-backup-$(date +%Y%m%d%H%M%S)"
  echo "  Existing ~/CLAUDE.md backed up"
fi
cp "$REPO_DIR/CLAUDE.md" "$CLAUDE_MD"
echo "  ✓ CLAUDE.md installed at ~/CLAUDE.md"

# Step 6: Install HOW-TO-ADD-SKILLS.md
if [ -f "$REPO_DIR/HOW-TO-ADD-SKILLS.md" ]; then
  cp "$REPO_DIR/HOW-TO-ADD-SKILLS.md" "$CLAUDE_DIR/HOW-TO-ADD-SKILLS.md"
  echo "  ✓ HOW-TO-ADD-SKILLS.md installed"
fi

# Step 7: Verify
echo ""
echo "Verifying installation..."
ERRORS=0
[ -f "$CLAUDE_DIR/brain/goals.md" ]          && echo "  ✓ brain/goals.md"          || { echo "  ✗ brain/goals.md MISSING";          ERRORS=$((ERRORS+1)); }
[ -f "$CLAUDE_DIR/brain/projects/README.md" ] && echo "  ✓ brain/projects/"          || { echo "  ✗ brain/projects/ MISSING";          ERRORS=$((ERRORS+1)); }
[ -f "$CLAUDE_DIR/brain/people/README.md" ]   && echo "  ✓ brain/people/"            || { echo "  ✗ brain/people/ MISSING";            ERRORS=$((ERRORS+1)); }
[ -f "$CLAUDE_DIR/brain/sops/README.md" ]     && echo "  ✓ brain/sops/"              || { echo "  ✗ brain/sops/ MISSING";              ERRORS=$((ERRORS+1)); }
[ -f "$CLAUDE_DIR/brain/daily/README.md" ]    && echo "  ✓ brain/daily/"             || { echo "  ✗ brain/daily/ MISSING";             ERRORS=$((ERRORS+1)); }
[ -f "$CLAUDE_DIR/brain/calendar/README.md" ] && echo "  ✓ brain/calendar/"          || { echo "  ✗ brain/calendar/ MISSING";          ERRORS=$((ERRORS+1)); }
[ -f "$CLAUDE_MD" ]                           && echo "  ✓ ~/CLAUDE.md"              || { echo "  ✗ ~/CLAUDE.md MISSING";              ERRORS=$((ERRORS+1)); }
[ -f "$CLAUDE_DIR/HOW-TO-ADD-SKILLS.md" ]    && echo "  ✓ HOW-TO-ADD-SKILLS.md"     || { echo "  ✗ HOW-TO-ADD-SKILLS.md MISSING";     ERRORS=$((ERRORS+1)); }

SKILLS_COUNT=$(ls "$CLAUDE_DIR/skills/" 2>/dev/null | wc -l)
CMDS_COUNT=$(ls "$CLAUDE_DIR/commands/"*.md 2>/dev/null | wc -l)
echo "  ✓ Skills: $SKILLS_COUNT folders in ~/.claude/skills/"
echo "  ✓ Commands: $CMDS_COUNT files in ~/.claude/commands/"

echo ""
if [ $ERRORS -eq 0 ]; then
  echo "============================================"
  echo "   INSTALL COMPLETE — YOU'RE LIVE, REGINALD"
  echo "============================================"
  echo ""
  echo "Open Claude Code and try: /morning-briefing"
  echo ""
else
  echo "============================================"
  echo "   INSTALL FINISHED WITH $ERRORS WARNING(S)"
  echo "============================================"
  echo "Check the items marked ✗ above."
  echo ""
fi
