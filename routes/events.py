"""
Events API routes.

Implements `GET /events` returning the latest normalized events sorted by
timestamp descending.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from db import get_db
from models.event_model import EventRepository

events_bp = Blueprint("events", __name__)


@events_bp.route("/events", methods=["GET"])
def events():
    """
    Return latest events in reverse chronological order.
    """
    limit_raw = request.args.get("limit", "50")
    try:
        limit = int(limit_raw)
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    limit = max(1, min(limit, 200))

    repo = EventRepository(get_db())
    items = repo.latest(limit=limit)
    return jsonify(items), 200

