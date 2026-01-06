"""Task database with embeddings using Turso and libsql."""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional

import libsql_experimental as libsql
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Embedding provider configuration
# Supports: 'openai' (default), 'deepseek' (uses DeepSeek's OpenAI-compatible endpoint)
# Note: DeepSeek does not have dedicated embedding models, but their API may support it
EMBEDDING_PROVIDERS = {
    "openai": {
        "base_url": None,  # Uses default OpenAI URL
        "default_model": "text-embedding-3-small",
        "dimensions": 1536,
    },
    "deepseek": {
        # DeepSeek uses OpenAI-compatible API but may not support embeddings
        # Fall back to OpenAI for embeddings if available
        "base_url": "https://api.deepseek.com",
        "default_model": None,  # DeepSeek doesn't have embedding models
        "dimensions": None,
    },
}


@dataclass
class TaskRecord:
    """Task record with embedding."""

    id: Optional[int] = None
    name: str = ""
    priority: int = 2
    due_date: str = ""
    created_at: str = ""
    embedding: Optional[List[float]] = None
    email_context: Optional[str] = None
    similarity_distance: Optional[float] = (
        None  # Cosine distance for similarity searches
    )


class TaskDatabase:
    """Manage tasks with embeddings in Turso database."""

    def __init__(self, db_url: Optional[str] = None, auth_token: Optional[str] = None):
        """Initialize database connection."""
        self.db_url = db_url or os.getenv("TURSO_DATABASE_URL")
        self.auth_token = auth_token or os.getenv("TURSO_AUTH_TOKEN")
        
        # Initialize embedding client
        # Priority: EMBEDDING_PROVIDER env var > LLM_PROVIDER > OpenAI if available
        self._init_embedding_client()

        # Connect to database
        if self.db_url and self.auth_token:
            # Remote Turso database
            self.conn = libsql.connect(self.db_url, auth_token=self.auth_token)
        else:
            # Local SQLite database
            self.conn = libsql.connect("tasks.db")
        
        # Ensure tables exist
        self._create_tables()
    
    def _init_embedding_client(self):
        """Initialize the embedding client based on configuration."""
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "").lower()
        llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        
        self.embedding_client = None
        self.embedding_model = None
        self.embedding_dimensions = 1536  # Default
        
        # Determine which provider to use for embeddings
        # Note: DeepSeek doesn't have embedding models, so we fall back to OpenAI
        if embedding_provider == "openai" or (not embedding_provider and openai_api_key):
            # Use OpenAI for embeddings
            if openai_api_key:
                self.embedding_client = OpenAI(api_key=openai_api_key)
                self.embedding_model = "text-embedding-3-small"
                self.embedding_dimensions = 1536
                print("🔢 Using OpenAI for embeddings")
        elif embedding_provider == "deepseek":
            # DeepSeek doesn't have embedding models - check if OpenAI is available as fallback
            if openai_api_key:
                print("⚠️  DeepSeek doesn't have embedding models, falling back to OpenAI for embeddings")
                self.embedding_client = OpenAI(api_key=openai_api_key)
                self.embedding_model = "text-embedding-3-small"
                self.embedding_dimensions = 1536
            else:
                print("⚠️  DeepSeek doesn't have embedding models and no OpenAI key available")
                print("   Duplicate detection will use text matching instead of semantic similarity")
        elif llm_provider == "deepseek" and not openai_api_key:
            # Using DeepSeek for LLM but no OpenAI for embeddings
            print("⚠️  Using DeepSeek for LLM but no OpenAI key for embeddings")
            print("   Duplicate detection will use text matching instead of semantic similarity")
        
        # Legacy compatibility: also set self.openai for backward compatibility
        self.openai = self.embedding_client

    def _create_tables(self):
        """Create tasks table with embeddings if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                priority INTEGER NOT NULL,
                due_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                email_context TEXT,
                embedding F32_BLOB({self.embedding_dimensions})
            )
        """)

        # Create vector index for similarity search
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS tasks_embedding_idx 
            ON tasks(libsql_vector_idx(embedding))
        """)

        self.conn.commit()
        cursor.close()

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for given text using the configured embedding client."""
        if not self.embedding_client or not self.embedding_model:
            return None
        try:
            response = self.embedding_client.embeddings.create(model=self.embedding_model, input=text)
            return response.data[0].embedding
        except Exception as e:
            print(f"⚠️  Error generating embedding: {e}")
            return None

    def add_task(self, task: Any, email_context: Optional[str] = None) -> TaskRecord:
        """Add a task to the database with embeddings."""
        # Generate embedding from task name and context (if embedding client available)
        embedding_text = f"{task.name}"
        if email_context:
            embedding_text += f" Context: {email_context}"

        embedding = self.generate_embedding(embedding_text)

        cursor = self.conn.cursor()
        
        if embedding:
            # Convert embedding to vector format
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            cursor.execute(
                """
                INSERT INTO tasks (name, priority, due_date, created_at, email_context, embedding)
                VALUES (?, ?, ?, ?, ?, vector32(?))
            """,
                (
                    task.name,
                    task.priority,
                    task.due_date,
                    datetime.now().isoformat(),
                    email_context,
                    embedding_str,
                ),
            )
        else:
            # Insert without embedding
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
            embedding=embedding,
            email_context=email_context,
        )

    def find_similar_tasks(self, query: str, limit: int = 5) -> List[TaskRecord]:
        """Find similar tasks based on embedding similarity."""
        # Generate embedding for query
        query_embedding = self.generate_embedding(query)
        
        # If no embedding available, fall back to simple text search
        if not query_embedding:
            return self._search_tasks_by_name(query, limit)
        
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """
                SELECT 
                    t.id, t.name, t.priority, t.due_date, t.created_at, 
                    t.email_context,
                    vector_distance_cos(t.embedding, vector32(?)) as distance
                FROM vector_top_k('tasks_embedding_idx', vector32(?), ?) AS v
                JOIN tasks t ON t.rowid = v.id
                ORDER BY distance ASC
            """,
                (embedding_str, embedding_str, limit),
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
                        similarity_distance=row[6],  # Include the distance from the query
                    )
                )

            cursor.close()
            return results
        except Exception:
            cursor.close()
            # Fall back to text search if vector search fails
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

    def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        deleted = cursor.rowcount > 0
        self.conn.commit()
        cursor.close()
        return deleted

    def complete_task(self, task_id: int) -> bool:
        """
        Mark a task as completed by removing it from the active task list.
        
        Note: This implementation removes the task from the database as tasks
        do not have a completed status field. For a full implementation with
        task history, consider adding a completed_tasks table.
        
        Args:
            task_id: The ID of the task to complete
            
        Returns:
            True if the task was found and completed, False otherwise
        """
        return self.delete_task(task_id)

    def close(self):
        """Close database connection."""
        self.conn.close()
