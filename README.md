# mobile-skill

A Claude Code plugin for building mobile apps phase by phase, with a gated waterfall lifecycle: requirements, architecture, detailed design, implementation, testing, store release and maintenance. Each phase produces reviewed deliverables from fixed templates, and the next phase starts only after an explicit sign-off.

## Install
```
/plugin marketplace add phongmanh/mobile-skill
/plugin install mobile-skill@mobile-skill
```

## Skills
| Skill | For | Run |
|---|---|---|
| `mobile-android-sdlc` | A native Android app or feature in Kotlin: Clean Architecture + MVVM, Jetpack Compose + Material 3, Hilt, Coroutines/Flow, Room, OWASP MASVS, Google Play release | `/mobile-skill:mobile-android-sdlc` |
| `mobile-multiplatform-sdlc` | One Kotlin codebase for Android and iOS: Kotlin Multiplatform + Compose Multiplatform, shared Clean Architecture + MVVM in `commonMain`, Koin, Ktor, Room KMP, iOS/Swift interop, Google Play and App Store release | `/mobile-skill:mobile-multiplatform-sdlc` |

Claude also picks a skill on its own when you ask it to plan, design, build, test or release an app or feature that way. Each skill bundles phase guides, references (architecture, code patterns, UI/UX, security and privacy, performance, testing, a PR review checklist) and deliverable templates.

The deliverables live in your project under `docs/sdlc/<initiative-slug>/`, with `STATUS.md` as the control file: phase, gate log, risks, change requests, the current phase plan and the session handoff.

## Hooks
| Hook | Event | What it does |
|---|---|---|
| `session-context.py` | `SessionStart` | For each `docs/sdlc/*/STATUS.md`, shows the current phase, the next open row of the newest `## Phase N plan` and the `## Handoff` section. A session can start after `/clear` and pick up where the last one stopped. |
| `guard-sdlc-baseline.py` | `PreToolUse` (`Edit`, `Write`, `MultiEdit`) | Asks you to confirm before Claude edits a deliverable that `STATUS.md` marks Approved. A baselined document changes only through an approved change request. |

Only you can switch the baseline gate off, in your git-ignored `.claude/settings.local.json`:
```json
{ "env": { "SDLC_GATE": "off" } }
```

## Progress dashboard
`scripts/progress.py` turns `STATUS.md` into `progress.html`, a colorful page you can open in a browser or share: the phase timeline, gate decisions, the current phase plan with a progress ring, deliverables, a risk grid, open items, change requests and the handoff, with what's waiting on you highlighted. It follows your light or dark setting and works at phone width.
```
python3 <plugin>/scripts/progress.py --workspace docs/sdlc/<slug> --open
```
Without `--workspace` it shows every workspace on one page (`docs/sdlc/progress.html`). Autopilot refreshes the page after each session. Commit it or git-ignore `docs/sdlc/**/progress.html`, as your team prefers. The page is self-contained apart from its web fonts; offline, it falls back to system fonts.

**In your own skill.** The dashboard reads the shape of `STATUS.md`, not anything mobile-specific, so other skills can use it too. It needs a `| Field | Value |` header table with a `Current phase` row starting with the phase number. These `##` sections are optional, and any that are missing are left out: `Deliverables`, `Gate log` (gates named `G<n> …`, one per phase), `Risks` (Likelihood and Impact as H/M/L), `Open items`, `Change requests`, `Phase <n> plan` (# · Work · … · Status) and `Handoff` (`- **Next action:**`, `- **Waiting on user:**`, …). Phase names come from `--phases "Discovery,Build,Launch"` or from `--skill-dir <your-skill>`, which reads its `phases/<n>-<name>.md` files.

## Autopilot
Runs the workflow unattended: `scripts/autopilot.py` starts a fresh headless session (`claude -p`) for each row of the current `## Phase N plan`, and the `session-context.py` hook hands each one the last handoff. Gates still stop: autopilot never records a sign-off.

Do scope and the first phase plan interactively, then ask Claude to "run autopilot", or run it yourself from the project root. The script is in the installed plugin (`~/.claude/plugins/cache/mobile-skill/mobile-skill/<version>/scripts/`) or your clone of this repo:
```
python3 <plugin>/scripts/autopilot.py --workspace docs/sdlc/<slug> --dry-run
python3 <plugin>/scripts/autopilot.py --workspace docs/sdlc/<slug> --budget-usd 20
```

| It stops when | Then you |
|---|---|
| The Handoff's **Waiting on user** isn't "nothing" (e.g. `G1 sign-off`, a decision, a CR approval) | Decide or sign off in an interactive session, set it back to "nothing", re-run |
| The next plan row is `Blocked: <reason>` | Unblock it, re-run |
| Phase 4 with code review mode *Approve before writing* | Switch to *Review after writing*, or continue interactively |
| A session fails, changes nothing in STATUS.md, or ends with `AUTOPILOT-RESULT: stop` | Read the reason and the log |
| `--max-sessions` (default 20) or `--budget-usd` is reached | Re-run when ready |

- **Permissions.** Sessions run with `--permission-mode acceptEdits` and allow file tools, `./gradlew`, `xcodebuild` and local git (`status`, `diff`, `log`, `branch`, `switch`, `checkout -b`, `add`, `commit`). They deny `git push`, merges, rebases, hard resets, `gh` and `AskUserQuestion`. The baseline gate's confirm becomes a denial. Your project's `.claude/settings.json` allow list still applies.
- **Phase 4.** One branch and commit per PR row, stacked on the previous one after the checks pass. You push, open and review the PRs.
- **Dashboard.** `progress.html` in the workspace is refreshed after each session; `--no-dashboard` turns that off.
- **Log.** One JSON line per session (time, session ID, plan item, cost, result) in `.claude/autopilot/<slug>.jsonl`; consider git-ignoring `.claude/autopilot/`.

## Optional: the SDLC rule
Plugins can't ship rule files. `rules/sdlc.md` restates the document rules (IDs, baselines, gate decisions, handoff format) and loads only while Claude edits `docs/sdlc/**`. To use it, copy it into your project as `.claude/rules/sdlc.md`.

## Development
Run the hook and autopilot tests from the repo root:
```
python3 -m unittest discover -s hooks/test
python3 -m unittest discover -s scripts/test
```
Check the plugin and the marketplace with `claude plugin validate .`.

## License
MIT. See [LICENSE](LICENSE).
