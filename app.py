"""
Flask entrypoint for the GitHub Webhook Event Tracker.

Run with:
  python app.py
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template

from config import Config, validate_config
from db import init_mongo
from routes.events import events_bp
from routes.webhook import webhook_bp


def create_app() -> Flask:
    validate_config(Config)

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # Centralized database initialization.
    init_mongo(app.config["MONGO_URI"])

    # Blueprints.
    app.register_blueprint(webhook_bp)
    app.register_blueprint(events_bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        # Lightweight health endpoint (does not leak secrets).
        return {"status": "ok"}, 200

    return app


if __name__ == "__main__":
    application = create_app()
    # For local development only; use a WSGI server in production.
    application.run(host="0.0.0.0", port=5000, debug=True)
