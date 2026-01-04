"""Flask dashboard application for task management."""

import os
from datetime import datetime
from typing import Optional

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from src.database.task_db import TaskDatabase, TaskRecord


def create_app(db_path: Optional[str] = None) -> Flask:
    """Create and configure the Flask dashboard application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    CORS(app)

    # Store database configuration
    app.config["DB_PATH"] = db_path

    def get_db() -> TaskDatabase:
        """Get database connection."""
        return TaskDatabase(db_path=app.config.get("DB_PATH"))

    @app.route("/")
    def index():
        """Render the main dashboard page."""
        return render_template("index.html")

    @app.route("/api/tasks", methods=["GET"])
    def get_tasks():
        """Get all tasks from the database."""
        db = get_db()
        try:
            tasks = db.get_recent_tasks(limit=100)
            task_list = [
                {
                    "id": t.id,
                    "name": t.name,
                    "priority": t.priority,
                    "due_date": t.due_date,
                    "created_at": t.created_at,
                    "email_context": t.email_context,
                }
                for t in tasks
            ]
            return jsonify({"tasks": task_list, "count": len(task_list)})
        finally:
            db.close()

    @app.route("/api/tasks", methods=["POST"])
    def add_task():
        """Add a new task."""
        data = request.get_json()
        if not data or not data.get("name"):
            return jsonify({"error": "Task name is required"}), 400

        db = get_db()
        try:
            task = TaskRecord(
                name=data["name"],
                priority=data.get("priority", 2),
                due_date=data.get("due_date", datetime.now().isoformat()[:10]),
                created_at=datetime.now().isoformat(),
                email_context=data.get("email_context"),
            )
            result = db.add_task(task)
            return jsonify(
                {
                    "success": True,
                    "task": {
                        "id": result.id,
                        "name": result.name,
                        "priority": result.priority,
                        "due_date": result.due_date,
                        "created_at": result.created_at,
                    },
                }
            )
        finally:
            db.close()

    @app.route("/api/tasks/search", methods=["GET"])
    def search_tasks():
        """Search for similar tasks."""
        query = request.args.get("q", "")
        if not query:
            return jsonify({"error": "Search query is required"}), 400

        db = get_db()
        try:
            similar_tasks = db.find_similar_tasks(query, limit=10)
            task_list = [
                {
                    "id": t.id,
                    "name": t.name,
                    "priority": t.priority,
                    "due_date": t.due_date,
                    "created_at": t.created_at,
                    "similarity_distance": t.similarity_distance,
                }
                for t in similar_tasks
            ]
            return jsonify({"tasks": task_list, "query": query})
        finally:
            db.close()

    @app.route("/api/stats", methods=["GET"])
    def get_stats():
        """Get task statistics."""
        db = get_db()
        try:
            tasks = db.get_recent_tasks(limit=1000)
            
            # Calculate stats
            total = len(tasks)
            high_priority = sum(1 for t in tasks if t.priority == 1)
            medium_priority = sum(1 for t in tasks if t.priority == 2)
            low_priority = sum(1 for t in tasks if t.priority == 3)
            
            # Tasks due today
            today = datetime.now().isoformat()[:10]
            due_today = sum(1 for t in tasks if t.due_date and t.due_date[:10] == today)
            
            return jsonify({
                "total": total,
                "high_priority": high_priority,
                "medium_priority": medium_priority,
                "low_priority": low_priority,
                "due_today": due_today,
            })
        finally:
            db.close()

    return app


def run_dashboard(host: str = "127.0.0.1", port: int = 5000, debug: bool = False) -> None:
    """Run the dashboard server."""
    app = create_app()
    print("=" * 50)
    print("TASK DASHBOARD")
    print(f"Running at http://{host}:{port}")
    print("=" * 50)
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_dashboard()
