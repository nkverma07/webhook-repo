"""
GitHub webhook parser.

This module translates GitHub webhook payloads into our internal `Event` model.
It stores ONLY required normalized fields and ignores everything else.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from models.event_model import Event


@dataclass(frozen=True)
class ParseResult:
    event: Optional[Event]
    ignored_reason: Optional[str] = None


def _to_utc_iso(dt_str: str) -> str:
    """
    Convert GitHub timestamps into a strict UTC ISO-8601 string.

    We return `YYYY-MM-DDTHH:MM:SSZ` (or with fractional seconds if present).
    """
    # GitHub often uses "Z" (Zulu) for UTC, but Python's fromisoformat expects +00:00.
    normalized = dt_str.strip().replace("Z", "+00:00")

    # fromisoformat supports offsets like "+00:00" and "+05:30".
    # If the timestamp lacks timezone info, we treat it as UTC.
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    dt_utc = dt.astimezone(timezone.utc)
    iso = dt_utc.isoformat(timespec="seconds").replace("+00:00", "Z")
    return iso


def parse_github_event(event_type: str, payload: dict[str, Any]) -> ParseResult:
    """
    Parse supported GitHub webhook types:
    - push
    - pull_request (opened)
    - pull_request merged (closed + merged=true)
    """
    event_type = (event_type or "").strip()

    if event_type == "push":
        return _parse_push(payload)

    if event_type == "pull_request":
        return _parse_pull_request(payload)

    return ParseResult(event=None, ignored_reason=f"Unsupported event type: {event_type}")


def _parse_push(payload: dict[str, Any]) -> ParseResult:
    try:
        author = str(payload["pusher"]["name"])

        # Git refs look like "refs/heads/main" for branches.
        ref = str(payload.get("ref", ""))
        if ref.startswith("refs/heads/"):
            to_branch = ref[len("refs/heads/") :]
        else:
            to_branch = ref

        commits = payload.get("commits") or []
        latest_commit_hash = ""
        if isinstance(commits, list) and commits:
            # Last commit in the array is typically the latest.
            latest_commit_hash = str(commits[-1].get("id", ""))

        head_commit = payload.get("head_commit") or {}
        timestamp_raw = str(head_commit.get("timestamp", ""))

        if not (author and to_branch and latest_commit_hash and timestamp_raw):
            return ParseResult(event=None, ignored_reason="Missing required fields for push event")

        return ParseResult(
            event=Event(
                request_id=latest_commit_hash,
                author=author,
                action="PUSH",
                from_branch="",
                to_branch=to_branch,
                timestamp=_to_utc_iso(timestamp_raw),
            )
        )
    except Exception:
        # We intentionally don't log/store the payload to avoid raw dumping.
        return ParseResult(event=None, ignored_reason="Failed to parse push event")


def _parse_pull_request(payload: dict[str, Any]) -> ParseResult:
    """
    Handles:
    - opened PR -> action "PULL_REQUEST"
    - merged PR -> action "MERGE" (closed + merged=true)
    """
    try:
        action = str(payload.get("action", "")).strip()
        pr = payload.get("pull_request") or {}

        merged = bool(pr.get("merged", False))

        # Common normalized fields.
        author = str(pr["user"]["login"])
        from_branch = str(pr["head"]["ref"])
        to_branch = str(pr["base"]["ref"])
        request_id = str(pr["id"])

        if action == "opened":
            timestamp_raw = str(pr.get("created_at", ""))
            if not timestamp_raw:
                return ParseResult(event=None, ignored_reason="Missing created_at for opened PR")

            return ParseResult(
                event=Event(
                    request_id=request_id,
                    author=author,
                    action="PULL_REQUEST",
                    from_branch=from_branch,
                    to_branch=to_branch,
                    timestamp=_to_utc_iso(timestamp_raw),
                )
            )

        # MERGE detection: action == closed AND merged == true
        if action == "closed" and merged is True:
            timestamp_raw = str(pr.get("merged_at", ""))
            if not timestamp_raw:
                return ParseResult(event=None, ignored_reason="Missing merged_at for merged PR")

            return ParseResult(
                event=Event(
                    request_id=request_id,
                    author=author,
                    action="MERGE",
                    from_branch=from_branch,
                    to_branch=to_branch,
                    timestamp=_to_utc_iso(timestamp_raw),
                )
            )

        return ParseResult(event=None, ignored_reason="Pull request action not tracked")
    except Exception:
        return ParseResult(event=None, ignored_reason="Failed to parse pull_request event")

