#!/usr/bin/env python3
"""Arcade AI tools configuration and examples."""

import json
import os
from typing import Any, Dict, List, Optional

from arcadepy import Arcade
from dotenv import load_dotenv

from agent_config import get_llm_client, get_default_model, AgentConfig
from src.email_utils import get_email_key, extract_list_from_response

# Load environment variables
load_dotenv()


# Available Arcade toolkits
AVAILABLE_TOOLKITS = {
    "gmail": "📧 Read, search, send, and manage Gmail messages",
    "math": "🔢 Perform calculations and solve mathematical problems",
    "github": "🐙 Manage repositories, issues, and pull requests",
    "linkedin": "💼 Access professional network data",
    "slack": "💬 Send messages and manage team communication",
    "calendar": "📅 Schedule events and manage appointments",
    "notion": "📝 Access workspace and knowledge management",
    "asana": "✅ Manage projects and tasks",
    "stripe": "💳 Handle payments and transactions",
    "salesforce": "🏢 CRM operations and customer management",
    "discord": "🎮 Community chat and server management",
    "twitter": "🐦 Social media posting and engagement",
    "shopify": "🛒 E-commerce and store management",
}


class ToolkitAgent:
    """Generic agent that can use any combination of Arcade toolkits."""

    def __init__(
        self,
        name: str,
        toolkits: List[str],
        instructions: str,
        model: Optional[str] = None,
    ):
        """
        Initialize a toolkit agent.

        Args:
            name: Agent name
            toolkits: List of toolkit names to use
            instructions: Agent instructions
            model: AI model to use (defaults to configured provider's default)
        """
        self.name = name
        self.toolkits = toolkits
        self.instructions = instructions
        self.model = model or get_default_model()
        self.client = Arcade()
        self.llm_client = get_llm_client()
        self.user_id = AgentConfig.MAIL_ADDRESS

    def authorize_tool(self, tool_name: str) -> Optional[str]:
        """Authorize a specific tool."""
        try:
            auth_response = self.client.tools.authorize(
                tool_name=tool_name,
                user_id=self.user_id,
            )
            if auth_response.status == "completed":
                return None
            return auth_response.url
        except Exception as e:
            return f"Error: {str(e)}"

    def execute_tool(self, tool_name: str, inputs: Dict[str, Any]) -> Any:
        """Execute a specific Arcade tool."""
        try:
            response = self.client.tools.execute(
                tool_name=tool_name,
                input=inputs,
                user_id=self.user_id,
            )
            
            # Check for errors in the response
            if response.output is None:
                return "Error: No output in response"
            
            if hasattr(response.output, "error") and response.output.error:
                error = response.output.error
                return f"Error: {error.message}"
            
            if hasattr(response.output, "value") and response.output.value is not None:
                value = response.output.value
                
                # Try to extract a list from the response
                extracted_list = extract_list_from_response(value)
                if extracted_list:
                    return extracted_list
                
                # If no list found, return the value as-is (could be a dict or scalar)
                return value
            return str(response.output)
        except Exception as e:
            return f"Error: {str(e)}"

    def run(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Run the agent with the given input using LLM and Arcade tools."""
        # Build system prompt with available tools
        tools_info = "\n".join(
            [f"- {tk}: {AVAILABLE_TOOLKITS.get(tk, 'Unknown toolkit')}" 
             for tk in self.toolkits]
        )

        system_prompt = f"""You are {self.name}. {self.instructions}

You have access to these toolkits:
{tools_info}

When you need to use a tool, indicate which tool and what parameters to use.
Provide helpful, clear responses based on the available tools."""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": input_text},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"


# Example agent configurations
class AgentExamples:
    """Pre-configured agent examples for common use cases."""

    @staticmethod
    def email_assistant(user_email: Optional[str] = None) -> str:
        """Email management assistant."""
        agent = ToolkitAgent(
            name="Email Assistant",
            toolkits=["gmail"],
            instructions=(
                "You are an email assistant. Help manage emails, "
                "extract important information, and identify action items. "
                "Always prioritize urgent messages and provide clear summaries."
            ),
        )

        # Try to authorize Gmail
        auth_url = agent.authorize_tool("Google.ListEmails")
        if auth_url and auth_url.startswith("http"):
            return f"Authorization required. Please visit: {auth_url}"

        # Get all unread emails
        unread_emails = agent.execute_tool("Google.ListEmails", {"n_emails": AgentConfig.MAX_UNREAD_EMAILS, "query": "is:unread"})
        
        # Get the most recent emails
        recent_emails = agent.execute_tool("Google.ListEmails", {"n_emails": AgentConfig.RECENT_EMAILS_COUNT})
        
        # Combine emails avoiding duplicates
        all_emails = {}
        if isinstance(unread_emails, list):
            for email in unread_emails:
                email_key = get_email_key(email)
                all_emails[email_key] = email
        
        if isinstance(recent_emails, list):
            for email in recent_emails:
                email_key = get_email_key(email)
                if email_key not in all_emails:
                    all_emails[email_key] = email
        
        emails = list(all_emails.values())

        if isinstance(emails, str) and emails.startswith("Error"):
            return emails

        # Summarize with AI
        return agent.run(
            f"Summarize these emails and identify important action items:\n{json.dumps(emails, indent=2)}",
            context={"user_id": user_email} if user_email else {},
        )

    @staticmethod
    def math_solver() -> None:
        """Mathematical problem solver."""
        agent = ToolkitAgent(
            name="Math Solver",
            toolkits=["math"],
            instructions=(
                "You are a mathematical assistant. Solve equations, "
                "perform calculations, and explain mathematical concepts clearly."
            ),
        )

        # Interactive math solver
        print("Math Solver Ready! (type 'quit' to exit)")
        while True:
            problem = input("\nEnter math problem: ")
            if problem.lower() in ["quit", "exit"]:
                break

            result = agent.run(problem)
            print(f"Solution: {result}")

    @staticmethod
    def github_manager(repo: str) -> str:
        """GitHub repository manager."""
        agent = ToolkitAgent(
            name="GitHub Manager",
            toolkits=["github"],
            instructions=(
                "You are a GitHub repository manager. Help with issues, "
                "pull requests, and code management. Provide clear status updates."
            ),
        )

        return agent.run(f"Show me the open issues and recent activity for {repo}")

    @staticmethod
    def multi_tool_assistant() -> str:
        """Multi-tool assistant combining email, calendar, and tasks."""
        agent = ToolkitAgent(
            name="Productivity Assistant",
            toolkits=["gmail", "calendar", "asana"],
            instructions=(
                "You are a productivity assistant with access to email, calendar, "
                "and task management. Help organize work, schedule meetings, "
                "and track tasks efficiently."
            ),
        )

        return agent.run(
            "Check my emails for meeting requests and help me schedule them"
        )


def list_available_tools() -> None:
    """List all available Arcade toolkits."""
    print("=" * 60)
    print("AVAILABLE ARCADE TOOLKITS")
    print("=" * 60)

    for toolkit, description in AVAILABLE_TOOLKITS.items():
        print(f"{description}")
        print(f"   Toolkit name: '{toolkit}'")
        print()


def create_custom_agent() -> None:
    """Interactive custom agent creator."""
    print("=" * 60)
    print("CREATE CUSTOM AGENT")
    print("=" * 60)

    # Get agent name
    name = input("\nAgent name: ")

    # Select toolkits
    print("\nAvailable toolkits:")
    for i, (toolkit, desc) in enumerate(AVAILABLE_TOOLKITS.items(), 1):
        print(f"{i}. {toolkit}: {desc}")

    toolkit_nums = input("\nSelect toolkits (comma-separated numbers): ")
    selected_toolkits = []
    toolkit_list = list(AVAILABLE_TOOLKITS.keys())

    for num in toolkit_nums.split(","):
        try:
            idx = int(num.strip()) - 1
            if 0 <= idx < len(toolkit_list):
                selected_toolkits.append(toolkit_list[idx])
        except ValueError:
            pass

    if not selected_toolkits:
        print("No valid toolkits selected!")
        return

    print(f"\nSelected toolkits: {', '.join(selected_toolkits)}")

    # Get instructions
    print("\nEnter agent instructions (end with empty line):")
    instructions_lines = []
    while True:
        line = input()
        if not line:
            break
        instructions_lines.append(line)

    instructions = " ".join(instructions_lines)

    # Create agent
    agent = ToolkitAgent(
        name=name, toolkits=selected_toolkits, instructions=instructions
    )

    print(f"\n✅ Agent '{name}' created successfully!")

    # Interactive mode
    print("\nEnter commands for your agent (type 'quit' to exit):")
    while True:
        command = input("\n>> ")
        if command.lower() in ["quit", "exit"]:
            break

        print("\n🔄 Processing...")
        result = agent.run(command)
        print(f"\n{result}")


def main() -> None:
    """Main entry point for tools demonstration."""
    print("=" * 60)
    print("ARCADE AI TOOLS")
    print("=" * 60)

    options = {
        "1": ("List available toolkits", list_available_tools),
        "2": ("Email assistant demo", lambda: print(AgentExamples.email_assistant())),
        "3": ("Math solver demo", AgentExamples.math_solver),
        "4": ("Create custom agent", create_custom_agent),
    }

    print("\nOptions:")
    for key, (desc, _) in options.items():
        print(f"{key}. {desc}")

    choice = input("\nSelect option: ")

    if choice in options:
        _, func = options[choice]
        func()
    else:
        print("Invalid option!")


if __name__ == "__main__":
    main()