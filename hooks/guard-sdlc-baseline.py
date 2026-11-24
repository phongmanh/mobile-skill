#!/usr/bin/env python3
"""Claude Code PreToolUse hook (Edit|Write|MultiEdit).

Keeps the phase gates of the SDLC skills (mobile-android-sdlc,
mobile-multiplatform-sdlc) real. Before Claude edits a deliverable
under docs/sdlc/<slug>/ that STATUS.md marks as Approved (baselined), the user
is asked to confirm. A baselined document should change only through an
approved change request (cr/CR-NNN-*.md).

The workspace's living files (STATUS.md, STATUS-archive.md, rtm.md and
cr/*.md) are never gated, and edits to them are allowed without a permission
prompt, because the workflow updates them in every session. Only a real file
directly inside <project>/docs/sdlc/<slug>/ (or its cr/) qualifies: no "..",
no symbolic link leading elsewhere. The user can turn the auto-allow off with
SDLC_AUTO_ALLOW=off; those edits then get Claude Code's usual prompt.

The user (never Claude) can switch the gate off by setting SDLC_GATE=off,
e.g. in the git-ignored .claude/settings.local.json:
    { "env": { "SDLC_GATE": "off" } }

Registered by the mobile-skill plugin in hooks/hooks.json.
"""
import fnmatch
import json
import os
import re
import sys
from pathlib import Path

LIVING_FILES = {"STATUS.md", "STATUS-archive.md", "rtm.md"}
DELIVERABLES_HEADING = "## Deliverables"


def cells(row):
    return [cell.strip().strip("`") for cell in row.strip().strip("|").split("|")]


def as_glob(file_cell):
    """Turns template placeholders such as design/<feature>.md or adr/NNNN-<decision>.md into a glob."""
    return re.sub(r"<[^>]*>|NNNN", "*", file_cell)


def is_approved(status_text, relative_path):
    """True if the Deliverables table in STATUS.md lists relative_path with status Approved."""
    in_section, file_col, status_col = False, None, None
    for line in status_text.splitlines():
        if line.startswith("#"):
            in_section = line.strip() == DELIVERABLES_HEADING
            continue
        if not in_section or not line.lstrip().startswith("|"):
            continue
        row = cells(line)
        if file_col is None:
            if "File" in row and any(cell.startswith("Status") for cell in row):
                file_col = row.index("File")
                status_col = next(i for i, cell in enumerate(row) if cell.startswith("Status"))
            continue
        if len(row) <= max(file_col, status_col):
            continue
        if fnmatch.fnmatch(relative_path, as_glob(row[file_col])) and row[status_col].lower().startswith("approved"):
            return True
    return False


def is_living(relative_path):
    return relative_path in LIVING_FILES or (relative_path.startswith("cr/") and relative_path.endswith(".md"))


def safe_to_allow(path, workspace, relative_path, project_dir):
    """True if path really is that living file of a workspace directly under <project>/docs/sdlc/."""
    if ".." in Path(relative_path).parts:
        return False
    try:
        root = workspace.resolve()
        if root.parent != (project_dir / "docs" / "sdlc").resolve():
            return False
        target = Path(path).resolve()  # follows symbolic links, so one leading elsewhere fails the test below
    except (OSError, RuntimeError):
        return False
    return target == root / relative_path and target.parent in (root, root / "cr")


def print_decision(decision, reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }))


def main():
    try:
        path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
    except ValueError:
        return 0
    match = re.search(r"^(.*/docs/sdlc/[^/]+)/(.+)$", path)
    if not match:
        return 0

    workspace, relative_path = Path(match.group(1)), match.group(2)
    if is_living(relative_path):
        project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
        if os.environ.get("SDLC_AUTO_ALLOW", "").lower() != "off" and safe_to_allow(
                path, workspace, relative_path, project_dir):
            print_decision("allow", f"{relative_path} is a living SDLC file (mobile-skill plugin).")
        return 0
    if os.environ.get("SDLC_GATE", "").lower() == "off":
        return 0
    status_file = workspace / "STATUS.md"
    if not status_file.is_file() or not is_approved(status_file.read_text(encoding="utf-8"), relative_path):
        return 0

    reason = (
        f"{relative_path} is baselined (Approved in STATUS.md). Change it only through an approved "
        "change request (cr/CR-NNN-*.md), or confirm that this is a non-substantive fix. Only the user "
        "may switch this gate off (SDLC_GATE=off in .claude/settings.local.json); don't edit STATUS.md, "
        "the hooks or the settings to get past it."
    )
    print_decision("ask", reason)
    return 0


if __name__ == "__main__":
    sys.exit(main())
