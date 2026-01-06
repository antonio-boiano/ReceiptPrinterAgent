"""Flask dashboard application for task management."""

import os
import threading
import time
from datetime import datetime
from typing import Optional

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from src.database.task_db import TaskDatabase, TaskRecord


# Global variable for email checking status
_email_check_status = {
    "last_check": None,
    "checking": False,
    "error": None,
    "tasks_found": 0,
}
_email_check_thread = None
_stop_email_check = threading.Event()


def create_app(db_url: Optional[str] = None, auth_token: Optional[str] = None) -> Flask:
    """Create and configure the Flask dashboard application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    CORS(app)

    # Store database configuration
    app.config["DB_URL"] = db_url
    app.config["AUTH_TOKEN"] = auth_token

    def get_db() -> TaskDatabase:
        """Get database connection."""
        return TaskDatabase(
            db_url=app.config.get("DB_URL"), auth_token=app.config.get("AUTH_TOKEN")
        )

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

    @app.route("/api/email/check", methods=["POST"])
    def check_emails():
        """Manually trigger email checking for tasks."""
        global _email_check_status
        
        if _email_check_status["checking"]:
            return jsonify({
                "success": False,
                "message": "Email check already in progress",
                "status": _email_check_status
            }), 409
        
        # Run email check in a background thread
        thread = threading.Thread(target=_check_emails_for_tasks, args=(get_db,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "message": "Email check started",
            "status": _email_check_status
        })

    @app.route("/api/email/status", methods=["GET"])
    def email_status():
        """Get email checking status."""
        return jsonify(_email_check_status)

    return app


def _check_emails_for_tasks(get_db_func):
    """Check emails and extract tasks."""
    global _email_check_status
    
    _email_check_status["checking"] = True
    _email_check_status["error"] = None
    _email_check_status["tasks_found"] = 0
    
    try:
        # Import here to avoid circular imports
        from agent import ArcadeEmailAgent
        
        agent = ArcadeEmailAgent()
        result = agent.extract_tasks()
        
        if result and result.tasks:
            db = get_db_func()
            try:
                for task in result.tasks:
                    # Check for duplicates
                    similar_tasks = db.find_similar_tasks(task.name)
                    if (
                        similar_tasks
                        and len(similar_tasks) > 0
                        and similar_tasks[0].similarity_distance is not None
                        and similar_tasks[0].similarity_distance < 0.1
                    ):
                        continue
                    
                    # Add new task
                    db_task = TaskRecord(
                        name=task.name,
                        priority=task.priority,
                        due_date=task.due_date,
                        created_at=datetime.now().isoformat(),
                    )
                    db.add_task(db_task)
                    _email_check_status["tasks_found"] += 1
            finally:
                db.close()
        
        _email_check_status["last_check"] = datetime.now().isoformat()
    except Exception as e:
        _email_check_status["error"] = str(e)
    finally:
        _email_check_status["checking"] = False


def _periodic_email_check(get_db_func, interval_minutes: int):
    """Periodically check emails for tasks."""
    global _stop_email_check
    
    while not _stop_email_check.is_set():
        _check_emails_for_tasks(get_db_func)
        # Wait for the interval or until stopped
        _stop_email_check.wait(interval_minutes * 60)


def start_periodic_email_check(get_db_func, interval_minutes: int = 15):
    """Start the periodic email checking thread."""
    global _email_check_thread, _stop_email_check
    
    if _email_check_thread and _email_check_thread.is_alive():
        return  # Already running
    
    _stop_email_check.clear()
    _email_check_thread = threading.Thread(
        target=_periodic_email_check,
        args=(get_db_func, interval_minutes),
        daemon=True
    )
    _email_check_thread.start()


def stop_periodic_email_check():
    """Stop the periodic email checking thread."""
    global _stop_email_check
    _stop_email_check.set()


def run_dashboard(
    host: str = "127.0.0.1",
    port: int = 5000,
    debug: bool = False,
    email_check_interval: int = 0
) -> None:
    """
    Run the dashboard server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
        email_check_interval: Interval in minutes for periodic email checking (0 to disable)
    """
    app = create_app()
    print("=" * 50)
    print("TASK DASHBOARD")
    print(f"Running at http://{host}:{port}")
    if email_check_interval > 0:
        print(f"📧 Periodic email check: every {email_check_interval} minutes")
        
        def get_db():
            return TaskDatabase()
        
        start_periodic_email_check(get_db, email_check_interval)
    print("=" * 50)
    
    try:
        app.run(host=host, port=port, debug=debug)
    finally:
        stop_periodic_email_check()


if __name__ == "__main__":
    run_dashboard()
