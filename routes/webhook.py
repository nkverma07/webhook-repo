"""
Webhook routes.

Implements `POST /webhook` which receives GitHub webhook events, normalizes them,
and persists only the required fields.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from db import get_db
from models.event_model import EventRepository
from services.parser import parse_github_event

webhook_bp = Blueprint("webhook", __name__)


@webhook_bp.route("/webhook", methods=["POST"])
def webhook():
    """
    GitHub webhook receiver.

    GitHub sends the event type in the `X-GitHub-Event` header.
    We parse a small set of supported events and ignore everything else.
    """
    event_type = request.headers.get("X-GitHub-Event", "").strip()
    if not event_type:
        return jsonify({"error": "Missing required header X-GitHub-Event"}), 400

    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        return jsonify({"error": "Expected JSON object payload"}), 400

    parsed = parse_github_event(event_type=event_type, payload=payload)
    if parsed.event is None:
        # Not an error; many GitHub events/actions are intentionally ignored.
        return jsonify({"status": "ignored", "reason": parsed.ignored_reason}), 202

    repo = EventRepository(get_db())
    inserted_id = repo.insert(parsed.event)
    return jsonify({"status": "stored", "id": inserted_id}), 201

