# How to Add Skills to Your AI OS

## What Is a Skill?

A skill is a folder in `~/.claude/skills/` containing a `SKILL.md` file. Claude Code detects these automatically and uses them when you invoke a slash command.

## Skill Folder Structure

```
~/.claude/skills/
  my-skill/
    SKILL.md        ← Required: the skill definition
    context.md      ← Optional: extra context or templates
    examples.md     ← Optional: example inputs/outputs
```

## SKILL.md Template

```markdown
# Skill: [Skill Name]

## Trigger
/skill-name

## Purpose
One sentence: what does this skill do?

## Instructions
Step-by-step instructions Claude follows when this skill is invoked.

1. Ask the user for [input]
2. Do [action]
3. Output [result]

## Output Format
Describe the expected output format.

## Example
**Input:** [example input]
**Output:** [example output]
```

## Creating a Slash Command

Add a `.md` file to `~/.claude/commands/`:

```markdown
# /command-name

[Description of what this command does]

## Steps
1.
2.
3.
```

## Adding Knowledge to the Brain

Drop any `.md` file into `~/.claude/brain/knowledge-base/` with a clear filename like `real-estate-terms.md` or `my-investment-criteria.md`. Claude will reference it when relevant.

## Tips

- Keep skill names short and memorable
- One skill = one job
- Test with: "Use my [skill-name] skill to [task]"
- Skills persist across all sessions automatically
