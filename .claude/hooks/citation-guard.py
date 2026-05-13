#!/usr/bin/env python3
"""PreToolUse hook on Write/Edit/MultiEdit targeting docs/.

Scans the new content for sentences that look like factual claims but lack a
[@citekey] citation. Warns the user; does not block.

Heuristic, not perfect — false positives are tolerated. The point is to nudge
the author to cite, not to enforce automatically.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# A claim sentence is: declarative, > 8 words, contains a "claim verb",
# does NOT already contain [@something] or \cite{...} or "we" / "our" (which
# we interpret as the author's own contribution, not requiring a citation).
CLAIM_VERBS = re.compile(
    r"\b(showed|shows|demonstrated|demonstrates|found|finds|observed|observes|"
    r"argued|argues|reported|reports|established|establishes|proved|proves|"
    r"confirmed|confirms|revealed|reveals|indicates|suggests|implies|implied|"
    r"is well known|well-known|are known|prior work|previous work|previously)\b",
    re.IGNORECASE,
)
HAS_CITE = re.compile(r"\[@[a-zA-Z][\w\-]*\]|\\cite[pt]?\{[^}]+\}")
SELF = re.compile(r"\b(we|our|this paper|in this work)\b", re.IGNORECASE)
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _project_root() -> Path:
    """Resolve project root from CLAUDE_PROJECT_DIR env var, else cwd."""
    root = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(root).resolve() if root else Path.cwd().resolve()


def is_doc_path(path: str) -> bool:
    """Return True iff `path` is a Markdown/LaTeX file under <project>/docs/
    that the citation-guard should scan.

    Scanned:
    - docs/research/**/*.md
    - docs/paper/<paper_id>/draft.md
    - docs/paper/<paper_id>/main.tex
    - docs/paper/<paper_id>/review-*.md
    - docs/paper/<paper_id>/rebuttal.md

    Skipped (paths under docs/, but not subject to citation rigor):
    - docs/paper/<paper_id>/submissions/**     (bundle copies — would double-flag)
    - docs/paper/<paper_id>/changelog.md       (bullet log)
    - docs/release/**                          (release manifests / data cards)

    Legacy flat layout (docs/paper/draft.md, docs/paper/main.tex,
    docs/paper/review-*.md, docs/paper/rebuttal.md) is also scanned for
    backward compatibility until the user runs lazy migration. See
    .claude/rules/multi-paper.md §5.

    Claude Code passes `tool_input.file_path` as an absolute path, so we
    relativize against the project root before checking.
    """
    if not path:
        return False
    p = Path(path)
    if p.suffix not in {".md", ".tex"}:
        return False
    try:
        rel = p.resolve().relative_to(_project_root())
    except ValueError:
        return False
    parts = rel.parts
    if not parts or parts[0] != "docs":
        return False

    # docs/research/**: always scan.
    if len(parts) >= 2 and parts[1] == "research":
        return True

    # docs/release/**: never scan.
    if len(parts) >= 2 and parts[1] == "release":
        return False

    # docs/paper/...
    if len(parts) >= 2 and parts[1] == "paper":
        # Legacy flat: docs/paper/<file>
        if len(parts) == 3:
            return parts[2] != "changelog.md"
        # Per-paper: docs/paper/<paper_id>/<file>
        if len(parts) == 4:
            if parts[3] == "changelog.md":
                return False
            return True
        # Deeper: docs/paper/<paper_id>/submissions/... or other nested dirs.
        # Never scan beyond depth 3 under docs/paper/.
        return False

    # Other docs/ subtrees: scan by default (covers stray .md files at docs/ root).
    return True


def extract_new_content(payload: dict) -> str:
    tool_name = payload.get("tool_name", "")
    inp = payload.get("tool_input", {})
    if tool_name == "Write":
        return inp.get("content", "") or ""
    if tool_name == "Edit":
        return inp.get("new_string", "") or ""
    if tool_name == "MultiEdit":
        edits = inp.get("edits", [])
        return "\n".join(e.get("new_string", "") for e in edits)
    return ""


def find_uncited_claims(text: str) -> list[str]:
    findings: list[str] = []
    # Strip code fences to avoid false positives in code blocks.
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    for sent in SENT_SPLIT.split(text):
        sent = sent.strip()
        if len(sent.split()) < 8:
            continue
        if HAS_CITE.search(sent):
            continue
        if SELF.search(sent):
            continue
        if not CLAIM_VERBS.search(sent):
            continue
        findings.append(sent[:200])
    return findings


def main() -> int:
    raw = sys.stdin.read() or "{}"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    inp = payload.get("tool_input", {}) or {}
    path = inp.get("file_path", "")
    if not is_doc_path(path):
        return 0
    content = extract_new_content(payload)
    if not content:
        return 0
    findings = find_uncited_claims(content)
    if not findings:
        return 0
    lines = [f"[citation-guard] 引用が見つからない可能性のある主張があります ({path}):"]
    for f in findings[:5]:
        lines.append(f"  - {f}")
    if len(findings) > 5:
        lines.append(f"  ...他 {len(findings) - 5} 件")
    lines.append("該当箇所に [@citekey] を追記するか、自分の貢献として we/our 文に書き換えてください。")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
