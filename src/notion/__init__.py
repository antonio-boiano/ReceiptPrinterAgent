"""Notion integration for publishing tasks as a todolist."""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from arcadepy import Arcade
from dotenv import load_dotenv

from src.email_utils import extract_list_from_response

load_dotenv()


@dataclass
class NotionTask:
    """Task formatted for Notion."""

    name: str
    priority: int  # 1=High, 2=Medium, 3=Low
    due_date: Optional[str] = None
    status: str = "To Do"
    notes: Optional[str] = None


class NotionIntegration:
    """Handles Notion integration via Arcade tools."""

    def __init__(self, user_id: Optional[str] = None):
        """Initialize Notion integration with Arcade client."""
        self.client = Arcade()
        self.user_id = user_id or os.getenv("ARCADE_USER_ID", "user@example.com")
        self.database_id = os.getenv("NOTION_DATABASE_ID")

    def authorize(self) -> Optional[str]:
        """Authorize Notion access via Arcade."""
        try:
            auth_response = self.client.tools.authorize(
                tool_name="Notion.SearchPages",
                user_id=self.user_id,
            )
            if auth_response.status == "completed":
                return None  # Already authorized
            return auth_response.url  # Return auth URL
        except Exception as e:
            return f"Error: {str(e)}"

    def search_databases(self, query: str = "") -> List[Dict[str, Any]]:
        """Search for Notion databases."""
        try:
            response = self.client.tools.execute(
                tool_name="Notion.SearchPages",
                inputs={"query": query, "filter": {"property": "object", "value": "database"}},
                user_id=self.user_id,
            )
            
            # Check for errors in the response
            if response.output is None:
                print("   ⚠️  No output in response")
                return []
            
            if hasattr(response.output, "error") and response.output.error:
                error = response.output.error
                print(f"   ❌ API Error: {error.message}")
                return []
            
            if not hasattr(response.output, "value") or response.output.value is None:
                return []
            
            return extract_list_from_response(response.output.value)
        except Exception as e:
            print(f"Error searching databases: {e}")
            return []

    def create_page(
        self, database_id: str, task: NotionTask
    ) -> Optional[Dict[str, Any]]:
        """Create a new page (task) in a Notion database."""
        priority_map = {1: "High", 2: "Medium", 3: "Low"}
        priority_label = priority_map.get(task.priority, "Medium")

        # Build properties for the page
        properties = {
            "Name": {"title": [{"text": {"content": task.name}}]},
            "Status": {"select": {"name": task.status}},
            "Priority": {"select": {"name": priority_label}},
        }

        # Add due date if provided
        if task.due_date:
            properties["Due Date"] = {"date": {"start": task.due_date}}

        try:
            response = self.client.tools.execute(
                tool_name="Notion.CreatePage",
                inputs={
                    "parent": {"database_id": database_id},
                    "properties": properties,
                },
                user_id=self.user_id,
            )
            
            # Check for errors in the response
            if response.output is None:
                print("   ⚠️  No output in response")
                return None
            
            if hasattr(response.output, "error") and response.output.error:
                error = response.output.error
                print(f"   ❌ API Error: {error.message}")
                return None
            
            if hasattr(response.output, "value"):
                return response.output.value
            return None
        except Exception as e:
            print(f"Error creating Notion page: {e}")
            return None

    def publish_tasks(
        self, tasks: List[NotionTask], database_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Publish multiple tasks to a Notion database."""
        db_id = database_id or self.database_id
        if not db_id:
            return {"error": "No Notion database ID configured", "success": 0, "failed": len(tasks)}

        # Check authorization
        auth_url = self.authorize()
        if auth_url and auth_url.startswith("http"):
            return {"error": f"Authorization required: {auth_url}", "success": 0, "failed": len(tasks)}

        results = {"success": 0, "failed": 0, "errors": []}

        for task in tasks:
            result = self.create_page(db_id, task)
            if result:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"Failed to create: {task.name}")

        return results


def publish_tasks_to_notion(
    tasks: List[Dict[str, Any]], database_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to publish tasks to Notion.

    Args:
        tasks: List of task dictionaries with keys: name, priority, due_date
        database_id: Optional Notion database ID (uses env var if not provided)

    Returns:
        Dictionary with success/failed counts and any errors
    """
    integration = NotionIntegration()

    notion_tasks = [
        NotionTask(
            name=t.get("name", "Untitled Task"),
            priority=t.get("priority", 2),
            due_date=t.get("due_date"),
            status=t.get("status", "To Do"),
            notes=t.get("notes"),
        )
        for t in tasks
    ]

    return integration.publish_tasks(notion_tasks, database_id)


def sync_database_tasks(database_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Sync tasks from local database to Notion.

    Args:
        database_id: Optional Notion database ID

    Returns:
        Dictionary with sync results
    """
    from src.database.task_db import TaskDatabase

    # Get tasks from local database
    db = TaskDatabase()
    try:
        tasks = db.get_recent_tasks(limit=100)
        
        task_dicts = [
            {
                "name": t.name,
                "priority": t.priority,
                "due_date": t.due_date,
            }
            for t in tasks
        ]
        
        return publish_tasks_to_notion(task_dicts, database_id)
    finally:
        db.close()


def main():
    """CLI for Notion integration."""
    print("=" * 50)
    print("NOTION INTEGRATION")
    print("=" * 50)

    integration = NotionIntegration()

    # Check authorization
    print("\n🔑 Checking Notion authorization...")
    auth_url = integration.authorize()
    if auth_url and auth_url.startswith("http"):
        print(f"\n⚠️ Authorization required. Please visit:\n{auth_url}")
        input("\nPress Enter after authorizing...")

    print("\nOptions:")
    print("1. Search for databases")
    print("2. Sync local tasks to Notion")
    print("3. Publish a single task")

    choice = input("\nSelect option: ")

    if choice == "1":
        query = input("Search query (or press Enter for all): ")
        databases = integration.search_databases(query)
        if databases:
            print(f"\n📚 Found {len(databases)} database(s):")
            for db in databases:
                print(f"  - {db.get('title', 'Untitled')}: {db.get('id', 'No ID')}")
        else:
            print("\n❌ No databases found")

    elif choice == "2":
        print("\n🔄 Syncing local tasks to Notion...")
        result = sync_database_tasks()
        print(f"\n✅ Success: {result.get('success', 0)}")
        print(f"❌ Failed: {result.get('failed', 0)}")
        if result.get("errors"):
            for error in result["errors"]:
                print(f"  - {error}")

    elif choice == "3":
        name = input("Task name: ")
        priority = input("Priority (1=High, 2=Medium, 3=Low): ")
        due_date = input("Due date (YYYY-MM-DD) or press Enter to skip: ")

        task = NotionTask(
            name=name,
            priority=int(priority) if priority else 2,
            due_date=due_date if due_date else None,
        )

        db_id = input("Database ID (or press Enter to use env var): ")
        result = integration.publish_tasks([task], db_id if db_id else None)
        
        if result.get("success", 0) > 0:
            print("\n✅ Task published to Notion!")
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")

    else:
        print("Invalid option")


if __name__ == "__main__":
    main()
