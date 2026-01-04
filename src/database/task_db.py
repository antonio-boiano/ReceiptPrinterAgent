"""Task database with local SQLite storage."""

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional

from dotenv import load_dotenv

load_dotenv()

# Default database path
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tasks.db")


@dataclass
class TaskRecord:
    """Task record."""

    id: Optional[int] = None
    name: str = ""
    priority: int = 2
    due_date: str = ""
    created_at: str = ""
    embedding: Optional[List[float]] = None
    email_context: Optional[str] = None
    similarity_distance: Optional[float] = (
        None  # Reserved for future similarity searches
    )


class TaskDatabase:
    """Manage tasks in local SQLite database."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.
        
        Args:
            db_path: Path to the SQLite database file. Defaults to tasks.db in project root.
        """
        self.db_path = db_path or os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)

        # Connect to local SQLite database
        self.conn = sqlite3.connect(self.db_path)
        
        # Ensure tables exist
        self._create_tables()

    def _create_tables(self):
        """Create tasks table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                priority INTEGER NOT NULL,
                due_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                email_context TEXT
            )
        """)

        # Create index for faster name searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS tasks_name_idx 
            ON tasks(name)
        """)

        self.conn.commit()
        cursor.close()

    def add_task(self, task: Any, email_context: Optional[str] = None) -> TaskRecord:
        """Add a task to the database.
        
        Args:
            task: Task object with name, priority, and due_date attributes
            email_context: Optional email context for the task
            
        Returns:
            TaskRecord with the created task data
        """
        cursor = self.conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO tasks (name, priority, due_date, created_at, email_context)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                task.name,
                task.priority,
                task.due_date,
                datetime.now().isoformat(),
                email_context,
            ),
        )

        task_id = cursor.lastrowid
        self.conn.commit()
        cursor.close()

        return TaskRecord(
            id=task_id,
            name=task.name,
            priority=task.priority,
            due_date=task.due_date,
            created_at=datetime.now().isoformat(),
            email_context=email_context,
        )

    def find_similar_tasks(self, query: str, limit: int = 5) -> List[TaskRecord]:
        """Find tasks matching the query using text search.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of matching TaskRecord objects
        """
        return self._search_tasks_by_name(query, limit)

    def _search_tasks_by_name(self, query: str, limit: int = 5) -> List[TaskRecord]:
        """Simple text search fallback when embeddings are not available."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, name, priority, due_date, created_at, email_context
            FROM tasks
            WHERE name LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """,
            (f"%{query}%", limit),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                TaskRecord(
                    id=row[0],
                    name=row[1],
                    priority=row[2],
                    due_date=row[3],
                    created_at=row[4],
                    email_context=row[5],
                    similarity_distance=None,
                )
            )

        cursor.close()
        return results

    def get_recent_tasks(self, limit: int = 10) -> List[TaskRecord]:
        """Get most recent tasks."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, name, priority, due_date, created_at, email_context
            FROM tasks
            ORDER BY created_at DESC
            LIMIT ?
        """,
            (limit,),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                TaskRecord(
                    id=row[0],
                    name=row[1],
                    priority=row[2],
                    due_date=row[3],
                    created_at=row[4],
                    email_context=row[5],
                )
            )

        cursor.close()
        return results

    def close(self):
        """Close database connection."""
        self.conn.close()
