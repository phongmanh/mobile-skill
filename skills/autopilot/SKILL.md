---
name: autopilot
description: Runs the android or multiplatform SDLC workflow unattended - a driver script starts one fresh headless Claude session per row of the current phase plan in docs/sdlc/<slug>/STATUS.md, and stops by itself at every gate sign-off, blocked row or decision only the owner can make. Takes the platform as its first argument (android or multiplatform). Use when the user asks to run autopilot, run the plan unattended or in the background, or keep going without them, for work run with the mobile SDLC skills.
argument-hint: "[android|multiplatform] [workspace slug] [--budget-usd N] [--max-sessions N]"
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/autopilot.py" *)
---
# Autopilot

Starts the unattended mode of the [android](../android/SKILL.md) or [multiplatform](../multiplatform/SKILL.md) skill. A driver script runs a fresh headless session (`claude -p`) for each row of the current `## Phase <n> plan`, and the SessionStart hook hands each one the last handoff. What each session does is in that skill's `## Autopilot` section. **Gates still stop:** autopilot never records a gate decision.

Arguments: `$ARGUMENTS`

## Steps
1. **Pick the platform.** The first argument, if it is `android` or `multiplatform`, is the skill every session runs; it goes to the driver as `--skill <platform>`. The old names `mobile-android-sdlc` and `mobile-multiplatform-sdlc` mean the same.
   - **Not given:** the driver detects it from STATUS.md (multiplatform when it has iOS fields). The dry run in step 5 says which one; ask the user to confirm it before step 6.
   - **Given, but STATUS.md looks like the other one** (e.g. `android` on a workspace with an `iOS deployment target` or `Platforms` row): say so and ask before running.
2. **Pick the workspace.** It's `docs/sdlc/<slug>/` in the project root. Use the slug from the arguments. With no slug and more than one workspace, ask which one. With none, explain that `/mobile-skill:android` or `/mobile-skill:multiplatform` creates it, and stop.
3. **Check it's ready.** Read the top of its `STATUS.md`. Scope (step 3 of the platform skill) must be done, and STATUS.md must have a `## Phase <n> plan` with real rows. If not, do those first, with the user, in that skill.
4. **Phase 4 only:** **Code review mode** must be *Review after writing*. *Approve before writing* needs the owner for every PR, so autopilot refuses it. Offer to switch it, or continue interactively.
5. **Dry run.** From the project root, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/autopilot.py" --workspace docs/sdlc/<slug> [--skill <platform>] --dry-run`, passing on any options from the arguments. Show the user the platform, the next item and the command.
6. **Run it** with the same command minus `--dry-run`, using Bash `run_in_background`. Options: `--model` and `--effort` (default: Claude Code's), `--max-sessions` (default 20), `--budget-usd`, `--session-timeout` (minutes, default 90), `--no-dashboard`.
7. **Tell the user:**
   - it stops by itself when it needs them (a gate sign-off, a decision, a blocked row, a failed session, or a cap);
   - `TaskStop` (or Ctrl-C) stops it early;
   - each session is logged in `.claude/autopilot/<slug>.jsonl`, and `/mobile-skill:progress` shows where it stands.

When it finishes, read its last lines and say why it stopped and what the user needs to do next.
