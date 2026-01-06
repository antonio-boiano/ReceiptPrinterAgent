#!/usr/bin/env python3
"""AI Agent for email task extraction using Arcade tools."""

import asyncio
import datetime
import json
import os
from dataclasses import dataclass
from typing import List, Optional

from arcadepy import Arcade
from dotenv import load_dotenv

from agent_config import get_llm_client, get_default_model
from src.database.task_db import TaskDatabase, TaskRecord

# Load environment variables
load_dotenv()


@dataclass
class Task:
    """Task model for extracted email tasks."""

    name: str
    priority: int  # 1 for high, 2 for medium, 3 for low
    due_date: str  # ISO format date string


@dataclass
class ImportantTasks:
    """Container for extracted tasks and summary."""

    tasks: List[Task]
    summary: str


class ArcadeEmailAgent:
    """Email task extraction agent using Arcade tools directly."""

    def __init__(self, user_id: Optional[str] = None):
        """Initialize the agent with Arcade client."""
        self.client = Arcade()
        self.llm_client = get_llm_client()
        self.model = get_default_model()
        self.user_id = user_id or os.getenv("ARCADE_USER_ID", "user@example.com")

    def authorize_gmail(self) -> Optional[str]:
        """Authorize Gmail access via Arcade."""
        try:
            auth_response = self.client.tools.authorize(
                tool_name="Google.ListEmails",
                user_id=self.user_id,
            )
            if auth_response.status == "completed":
                return None  # Already authorized
            return auth_response.url  # Return auth URL
        except Exception as e:
            return f"Error: {str(e)}"

    def get_emails(self, max_results: int = 10) -> List[dict]:
        """Fetch recent emails using Arcade Gmail tool."""
        try:
            response = self.client.tools.execute(
                tool_name="Google.ListEmails",
                input={"n_emails": max_results},
                user_id=self.user_id,
            )
            if hasattr(response.output, "value"):
                return response.output.value if isinstance(response.output.value, list) else []
            return []
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def analyze_emails_for_tasks(self, emails: List[dict]) -> ImportantTasks:
        """Use OpenAI to analyze emails and extract tasks."""
        if not emails:
            return ImportantTasks(tasks=[], summary="No emails to analyze")

        # Format emails for analysis
        emails_text = ""
        for i, email in enumerate(emails, 1):
            subject = email.get("subject", "No subject")
            sender = email.get("sender", "Unknown")
            snippet = email.get("snippet", "")
            emails_text += f"\n{i}. From: {sender}\n   Subject: {subject}\n   Preview: {snippet}\n"

        prompt = f"""Analyze these emails and extract actionable tasks. Ignore promotional emails.

Emails:
{emails_text}

For each actionable email, create a task with:
- name: Clear task description
- priority: 1 (HIGH), 2 (MEDIUM), or 3 (LOW)
- due_date: ISO format date (use today's date + reasonable deadline based on urgency)

Return JSON with format:
{{"tasks": [{{"name": "...", "priority": 1, "due_date": "2024-01-15"}}], "summary": "Brief summary of what was found"}}

If no actionable tasks, return: {{"tasks": [], "summary": "No actionable tasks found"}}
"""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)

            tasks = [
                Task(
                    name=t["name"],
                    priority=t.get("priority", 2),
                    due_date=t.get("due_date", datetime.datetime.now().isoformat()[:10]),
                )
                for t in result.get("tasks", [])
            ]

            return ImportantTasks(
                tasks=tasks, summary=result.get("summary", "Analysis complete")
            )
        except Exception as e:
            print(f"Error analyzing emails: {e}")
            return ImportantTasks(tasks=[], summary=f"Error: {str(e)}")

    def extract_tasks(self) -> ImportantTasks:
        """Main method to extract tasks from emails."""
        # Check authorization
        auth_url = self.authorize_gmail()
        if auth_url and auth_url.startswith("http"):
            print(f"\n🔑 Authorization required. Please visit:\n{auth_url}")
            input("\nPress Enter after authorizing...")

        # Fetch emails
        emails = self.get_emails()
        if not emails:
            return ImportantTasks(tasks=[], summary="No emails found")

        # Analyze and extract tasks
        return self.analyze_emails_for_tasks(emails)


def extract_email_tasks(user_email: Optional[str] = None) -> ImportantTasks:
    """
    Extract tasks from Gmail emails using Arcade tools.

    Args:
        user_email: User email for context (optional)

    Returns:
        ImportantTasks object containing extracted tasks and summary
    """
    agent = ArcadeEmailAgent(user_id=user_email)
    return agent.extract_tasks()


def main():
    """Main entry point for the email task extraction agent."""
    print("=" * 50)
    print("EMAIL TASK EXTRACTION AGENT")
    print("Powered by Arcade AI Tools")
    print("=" * 50)

    # Initialize database
    db = TaskDatabase()

    try:
        # Get user email from environment or ask
        user_email = os.getenv("ARCADE_USER_ID")
        if not user_email:
            user_email = input("\nEnter your email address: ")

        print(f"\n📧 Analyzing emails for: {user_email}")
        print("🔄 Processing...")

        # Extract tasks
        result = extract_email_tasks(user_email=user_email)

        if result and result.tasks:
            print(f"\n✅ Found {len(result.tasks)} tasks")
            print("\n📊 SUMMARY:")
            print(f"   {result.summary}")

            print("\n📋 EXTRACTED TASKS:")
            priority_map = {1: "🔴 HIGH", 2: "🟡 MEDIUM", 3: "🟢 LOW"}

            # Process and store tasks
            new_tasks = []
            duplicate_tasks = []

            for i, task in enumerate(result.tasks, 1):
                print(f"\n{i}. {task.name}")
                print(f"   Priority: {priority_map.get(task.priority, '❓ UNKNOWN')}")
                print(f"   Due: {task.due_date}")

                # Check for duplicates
                similar_tasks = db.find_similar_tasks(task.name)
                if (
                    similar_tasks
                    and len(similar_tasks) > 0
                    and similar_tasks[0].similarity_distance is not None
                    and similar_tasks[0].similarity_distance < 0.1
                ):
                    duplicate_tasks.append(task)
                    continue

                # Add new task to database
                db_task = TaskRecord(
                    name=task.name,
                    priority=task.priority,
                    due_date=task.due_date,
                    created_at=datetime.datetime.now().isoformat(),
                )
                db.add_task(db_task)
                new_tasks.append(task)

            # Print summary of database operations
            if new_tasks:
                print(f"\n💾 Saved {len(new_tasks)} new tasks to database")
            if duplicate_tasks:
                print(
                    f"\n🔁 Found {len(duplicate_tasks)} duplicate tasks that were not saved:"
                )
                for task in duplicate_tasks:
                    print(f"   - {task.name}")
        else:
            print("\n❌ No actionable tasks found in recent emails")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

    print("\n" + "=" * 50)
    # Close database connection
    db.close()


if __name__ == "__main__":
    main()
