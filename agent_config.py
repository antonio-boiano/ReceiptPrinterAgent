#!/usr/bin/env python3
"""Configuration settings for the AI Arcade Agent."""

import os

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# LLM Provider configuration
LLM_PROVIDERS = {
    "openai": {
        "base_url": None,  # Uses default OpenAI URL
        "default_model": "gpt-4o-mini",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "gpt-4-turbo"],
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
}


def get_llm_client() -> OpenAI:
    """
    Get an LLM client configured based on environment variables.
    
    Supports OpenAI and DeepSeek (OpenAI-compatible API).
    Configure via LLM_PROVIDER env var: 'openai' (default) or 'deepseek'.
    
    Returns:
        OpenAI client configured for the selected provider.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required when LLM_PROVIDER is 'deepseek'")
        return OpenAI(
            api_key=api_key,
            base_url=LLM_PROVIDERS["deepseek"]["base_url"],
        )
    else:
        # Default to OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'")
        return OpenAI(api_key=api_key)


def get_default_model() -> str:
    """Get the default model for the configured LLM provider."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider in LLM_PROVIDERS:
        return LLM_PROVIDERS[provider]["default_model"]
    return LLM_PROVIDERS["openai"]["default_model"]


class AgentConfig:
    """Configuration class for the AI Arcade Agent."""

    # API Keys
    ARCADE_API_KEY = os.getenv("ARCADE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    ARCADE_USER_ID = os.getenv("ARCADE_USER_ID", "user@example.com")
    
    # Mail address for syncing with mail services (can differ from ARCADE_USER_ID)
    MAIL_ADDRESS = os.getenv("MAIL_ADDRESS") or os.getenv("ARCADE_USER_ID", "user@example.com")
    
    # LLM Provider (openai or deepseek)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

    # Agent Settings
    DEFAULT_MODEL = get_default_model()
    ALTERNATIVE_MODELS = LLM_PROVIDERS.get(
        os.getenv("LLM_PROVIDER", "openai").lower(), 
        LLM_PROVIDERS["openai"]
    )["models"]

    # Default Toolkits
    DEFAULT_TOOLKITS = ["gmail", "math"]

    # Available Toolkits
    AVAILABLE_TOOLKITS = [
        "gmail",  # Email management
        "math",  # Mathematical calculations
        "github",  # Git repository management
        "linkedin",  # Professional networking
        "slack",  # Team communication
        "calendar",  # Event scheduling
        "notion",  # Workspace management
        "asana",  # Project management
        "stripe",  # Payment processing
        "salesforce",  # CRM management
        "discord",  # Community chat
        "twitter",  # Social media
        "shopify",  # E-commerce
    ]

    # Toolkit Descriptions
    TOOLKIT_DESCRIPTIONS = {
        "gmail": "📧 Email: Read, search, send, and manage Gmail messages",
        "math": "🔢 Math: Perform calculations, solve equations, and mathematical operations",
        "github": "🐙 GitHub: Manage repositories, issues, pull requests, and code",
        "linkedin": "💼 LinkedIn: Access professional network and career data",
        "slack": "💬 Slack: Send messages, manage channels, and team communication",
        "calendar": "📅 Calendar: Schedule events, manage appointments, and time planning",
        "notion": "📝 Notion: Access workspace, databases, and knowledge management",
        "asana": "✅ Asana: Manage projects, tasks, and team collaboration",
        "stripe": "💳 Stripe: Handle payments, customers, and financial transactions",
        "salesforce": "🏢 Salesforce: CRM operations, leads, and customer management",
        "discord": "🎮 Discord: Community chat, server management, and messaging",
        "twitter": "🐦 Twitter: Social media posting, engagement, and content management",
        "shopify": "🛒 Shopify: E-commerce, products, orders, and store management",
    }

    # Printing Settings
    AUTO_PRINT = True
    PRINT_SUCCESS_MESSAGES = True
    SAVE_PDF_COPIES = True

    # Priority Mappings
    PRIORITY_KEYWORDS = {
        "HIGH": ["urgent", "critical", "important", "asap", "priority", "deadline"],
        "MEDIUM": ["task", "todo", "action", "follow-up", "reminder"],
        "LOW": ["info", "fyi", "reference", "note", "update"],
    }

    @classmethod
    def get_toolkit_description(cls, toolkit_name: str) -> str:
        """Get description for a toolkit."""
        return cls.TOOLKIT_DESCRIPTIONS.get(
            toolkit_name, f"📦 {toolkit_name.title()}: Third-party toolkit"
        )

    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present."""
        missing = []

        if not cls.ARCADE_API_KEY:
            missing.append("ARCADE_API_KEY")

        # Check LLM provider API key
        if cls.LLM_PROVIDER == "deepseek":
            if not cls.DEEPSEEK_API_KEY:
                missing.append("DEEPSEEK_API_KEY")
        else:
            if not cls.OPENAI_API_KEY:
                missing.append("OPENAI_API_KEY")

        if missing:
            print("❌ Missing required environment variables:")
            for var in missing:
                print(f"   - {var}")
            print("\nPlease set these in your .env file or environment.")
            return False

        return True

    @classmethod
    def show_config_info(cls):
        """Display current configuration information."""
        print("🔧 AGENT CONFIGURATION")
        print("=" * 50)
        print(f"LLM Provider: {cls.LLM_PROVIDER}")
        print(f"Model: {cls.DEFAULT_MODEL}")
        print(f"User ID: {cls.ARCADE_USER_ID}")
        print(f"Mail Address: {cls.MAIL_ADDRESS}")
        print(f"Auto Print: {cls.AUTO_PRINT}")
        print(f"Save PDFs: {cls.SAVE_PDF_COPIES}")
        print(f"Default Toolkits: {', '.join(cls.DEFAULT_TOOLKITS)}")
        print(f"Available Toolkits: {len(cls.AVAILABLE_TOOLKITS)}")

        print("\n📦 AVAILABLE TOOLKITS:")
        for toolkit in cls.AVAILABLE_TOOLKITS:
            print(f"   {cls.get_toolkit_description(toolkit)}")

        # Check API keys (without revealing them)
        print("\n🔑 API KEYS:")
        print(f"   Arcade API Key: {'✅ Set' if cls.ARCADE_API_KEY else '❌ Missing'}")
        if cls.LLM_PROVIDER == "deepseek":
            print(f"   DeepSeek API Key: {'✅ Set' if cls.DEEPSEEK_API_KEY else '❌ Missing'}")
        else:
            print(f"   OpenAI API Key: {'✅ Set' if cls.OPENAI_API_KEY else '❌ Missing'}")


# Preset configurations for different use cases
class PresetConfigs:
    """Predefined configurations for common use cases."""

    EMAIL_ASSISTANT = {
        "toolkits": ["gmail", "calendar"],
        "instructions": "You are an email assistant. Help manage emails, schedule meetings, and organize communications. Always prioritize urgent messages and provide clear summaries.",
    }

    DEVELOPER_ASSISTANT = {
        "toolkits": ["github", "slack", "notion"],
        "instructions": "You are a developer assistant. Help with code repositories, team communication, and project documentation. Focus on code quality and team collaboration.",
    }

    BUSINESS_ASSISTANT = {
        "toolkits": ["salesforce", "stripe", "asana", "linkedin"],
        "instructions": "You are a business assistant. Help with customer management, payments, project tracking, and professional networking. Focus on efficiency and business growth.",
    }

    SOCIAL_MEDIA_MANAGER = {
        "toolkits": ["twitter", "linkedin", "discord"],
        "instructions": "You are a social media manager. Help create engaging content, manage communities, and build professional networks. Focus on audience engagement and brand building.",
    }

    ECOMMERCE_ASSISTANT = {
        "toolkits": ["shopify", "stripe", "gmail"],
        "instructions": "You are an e-commerce assistant. Help manage online stores, process orders, handle payments, and communicate with customers. Focus on customer satisfaction and sales optimization.",
    }

    GENERAL_ASSISTANT = {
        "toolkits": ["gmail", "math", "calendar", "notion"],
        "instructions": "You are a general assistant. Help with various tasks including email management, calculations, scheduling, and note-taking. Adapt to the user's needs and provide helpful insights.",
    }


if __name__ == "__main__":
    # Show configuration when run directly
    AgentConfig.show_config_info()
    print(f"\nConfiguration valid: {AgentConfig.validate_config()}")
