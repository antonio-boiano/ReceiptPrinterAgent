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

from agent_config import get_llm_client, get_default_model, AgentConfig, DEFAULT_USER_ID
from src.database.task_db import TaskDatabase, TaskRecord
from src.email_utils import get_email_key

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
        self.user_id = user_id or AgentConfig.MAIL_ADDRESS

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

    def get_emails(self, max_results: int = 20, query: Optional[str] = None) -> List[dict]:
        """Fetch emails using Arcade Gmail tool.
        
        Args:
            max_results: Maximum number of emails to fetch
            query: Optional Gmail search query (e.g., 'is:unread')
        """
        try:
            input_params = {"n_emails": max_results}
            if query:
                input_params["query"] = query
            
            response = self.client.tools.execute(
                tool_name="Google.ListEmails",
                input=input_params,
                user_id=self.user_id,
            )
            
            # Check for errors in the response
            if response.output is None:
                print("   ⚠️  No output in response")
                return []
            
            if hasattr(response.output, "error") and response.output.error:
                error = response.output.error
                print(f"   ❌ API Error: {error.message}")
                if hasattr(error, "developer_message") and error.developer_message:
                    print(f"      Developer message: {error.developer_message}")
                return []
            
            if not hasattr(response.output, "value") or response.output.value is None:
                print("   ⚠️  No value in response output")
                return []
            
            value = response.output.value
            
            # Handle case where value is already a list
            if isinstance(value, list):
                return value
            
            # Handle case where value is a dict containing emails
            if isinstance(value, dict):
                # Try common keys that might contain the email list
                for key in ["emails", "messages", "items", "data", "results"]:
                    if key in value and isinstance(value[key], list):
                        return value[key]
                # If dict has no recognized list key, return empty
                print(f"   ⚠️  Response value is a dict but no email list found. Keys: {list(value.keys())}")
                return []
            
            print(f"   ⚠️  Unexpected response value type: {type(value)}")
            return []
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def get_all_emails(self) -> List[dict]:
        """Fetch all unread emails and the recent emails, avoiding duplicates.
        
        Returns:
            List of email dictionaries containing message data.
        """
        all_emails = {}
        
        # Fetch all unread emails
        print("📬 Fetching unread emails...")
        unread_emails = self.get_emails(max_results=AgentConfig.MAX_UNREAD_EMAILS, query="is:unread")
        print(f"   Found {len(unread_emails)} unread email(s)")
        for email in unread_emails:
            email_key = get_email_key(email)
            all_emails[email_key] = email
        
        # Fetch the most recent emails
        print(f"📧 Fetching {AgentConfig.RECENT_EMAILS_COUNT} most recent emails...")
        recent_emails = self.get_emails(max_results=AgentConfig.RECENT_EMAILS_COUNT)
        print(f"   Found {len(recent_emails)} recent email(s)")
        new_recent_count = 0
        for email in recent_emails:
            email_key = get_email_key(email)
            if email_key not in all_emails:
                all_emails[email_key] = email
                new_recent_count += 1
        
        print(f"📊 Total unique emails to analyze: {len(all_emails)} ({len(unread_emails)} unread + {new_recent_count} additional recent)")
        return list(all_emails.values())

    def analyze_emails_for_tasks(self, emails: List[dict]) -> ImportantTasks:
        """Use OpenAI to analyze emails and extract tasks."""
        if not emails:
            return ImportantTasks(tasks=[], summary="No emails to analyze")

        print(f"🔍 Analyzing {len(emails)} emails for actionable tasks...")
        
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
            print(f"🤖 Calling LLM API (model: {self.model})...")
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            print(f"✅ LLM API response received")
            
            # Log usage information if available
            if hasattr(response, 'usage') and response.usage:
                print(f"📊 Token usage - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}, Total: {response.usage.total_tokens}")
            
            result = json.loads(response.choices[0].message.content)
            print(f"📋 LLM extracted {len(result.get('tasks', []))} task(s)")

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

        # Fetch all unread emails and 20 recent emails
        emails = self.get_all_emails()
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
        user_email = AgentConfig.MAIL_ADDRESS
        if not user_email or user_email == DEFAULT_USER_ID:
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
