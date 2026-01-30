"""
Event model and persistence helpers.

We store only the normalized fields required by the problem statement
(no raw GitHub payloads).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal, TypedDict

from pymongo.database import Database

Action = Literal["PUSH", "PULL_REQUEST", "MERGE"]


@dataclass(frozen=True)
class Event:
    request_id: str
    author: str
    action: Action
    from_branch: str
    to_branch: str
    timestamp: str  # UTC datetime string (ISO-8601)

    def to_mongo(self) -> dict:
        """
        Convert to a MongoDB document.
        """
        return asdict(self)


class EventDocument(TypedDict):
    request_id: str
    author: str
    action: Action
    from_branch: str
    to_branch: str
    timestamp: str


class EventRepository:
    """
    Repository layer for the `events` collection.

    Keeping this separate makes it easy to test the webhook parsing logic
    without needing a database.
    """

    def __init__(self, db: Database):
        self._collection = db["events"]
        # Helpful index for sorting by timestamp.
        # Safe to call repeatedly; MongoDB will no-op if it already exists.
        self._collection.create_index([("timestamp", -1)])

    def insert(self, event: Event) -> str:
        result = self._collection.insert_one(event.to_mongo())
        return str(result.inserted_id)

    def latest(self, limit: int = 50) -> list[EventDocument]:
        cursor = (
            self._collection.find(
                {},
                # Explicit projection ensures we only return required fields.
                {
                    "_id": 0,
                    "request_id": 1,
                    "author": 1,
                    "action": 1,
                    "from_branch": 1,
                    "to_branch": 1,
                    "timestamp": 1,
                },
            )
            .sort("timestamp", -1)
            .limit(limit)
        )
        return list(cursor)
