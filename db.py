"""
MongoDB connection management.

This module centralizes the PyMongo client so we don't create multiple connections
per request, and so the rest of the codebase does not need to know about
connection details.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database


@dataclass
class Mongo:
    client: MongoClient
    db: Database


_mongo: Optional[Mongo] = None


def init_mongo(mongo_uri: str) -> Mongo:
    """
    Initialize a global Mongo client and database handle from a Mongo URI.

    The database name is taken from the URI path (e.g. .../webhook_repo).
    """
    global _mongo
    if _mongo is not None:
        return _mongo

    # Enforce mongodb+srv:// URI for Atlas
    if not mongo_uri.startswith("mongodb+srv://"):
        raise RuntimeError("MONGO_URI must use mongodb+srv:// for MongoDB Atlas SRV connection.")

    # Use PyMongo with SRV support and set serverSelectionTimeoutMS
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client.get_default_database()
    if db is None:
        raise RuntimeError(
            "MongoDB URI must include a database name, e.g. "
            "mongodb+srv://<user>:<pass>@cluster.mongodb.net/webhook_repo"
        )

    # Centralized index creation (runs only once at startup)
    from models.event_model import EventRepository
    EventRepository.ensure_indexes(db)

    _mongo = Mongo(client=client, db=db)
    return _mongo


def get_db() -> Database:
    """
    Get the initialized database handle.
    """
    if _mongo is None:
        raise RuntimeError("Mongo is not initialized. Call init_mongo() first.")
    return _mongo.db
