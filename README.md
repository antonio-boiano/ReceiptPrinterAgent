# Receipt Printer Task Manager

A Python-based task management system that prints tasks to a thermal receipt printer and integrates with various services using Arcade.dev.

## Features

- Print tasks to thermal receipt printers
- Extract tasks from Gmail automatically
- AI-powered task parsing and prioritization
- Duplicate detection using vector embeddings
- **Local Dashboard** - Web-based UI for task tracking and management
- **Notion Integration** - Sync tasks to Notion for team collaboration
- Integration with multiple services (Gmail, Slack, Calendar, Notion) via Arcade.dev

## Installation

```bash
# Clone the repository
git clone https://github.com/CodingWithLewis/ReceiptPrinterAgent
cd receipt-printer-tasks

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## Quick Start with Local SQLite

For the fastest setup using local SQLite database (no cloud services required):

```bash
# Run the automatic setup script
python setup_local_db.py
```

This script will:
1. Check that dependencies are installed
2. Create a `.env` file configured for local SQLite
3. Create the local `tasks.db` database with required tables
4. Optionally add sample tasks for testing
5. Verify the setup is working

After running the script, start the dashboard:
```bash
python dashboard.py
# Access at http://127.0.0.1:5000
```

> **Note**: For AI-powered features (semantic search, task extraction), you'll need to add an `OPENAI_API_KEY` to your `.env` file. The basic functionality works without it.

## Configuration

### Required environment variables:
- `ARCADE_API_KEY` - Get from [arcade.dev](https://arcade.dev) - Used for tool integrations (Gmail, Slack, etc.)
- `ARCADE_USER_ID` - **Important:** This must match the email address of your signed-in Arcade account. You can find your Arcade account email at [arcade.dev](https://arcade.dev). If there is a mismatch, you will get authentication errors when using Arcade tools.

### LLM Provider (choose one):
The agent uses a Large Language Model for task extraction and analysis. You can choose between OpenAI and DeepSeek:

**Option 1: OpenAI (default)**
- `OPENAI_API_KEY` - Get from [OpenAI](https://platform.openai.com/)

**Option 2: DeepSeek**
- `LLM_PROVIDER=deepseek` - Set this to use DeepSeek
- `DEEPSEEK_API_KEY` - Get from [DeepSeek](https://platform.deepseek.com/)

### Optional environment variables:
- `MAIL_ADDRESS` - Email address for syncing with mail services. Defaults to the value of `ARCADE_USER_ID` if not set. Use this if your mail address differs from your Arcade user ID.
- `LLM_PROVIDER` - LLM provider: `openai` (default) or `deepseek`
- `TURSO_DATABASE_URL` - Database URL (optional, uses local SQLite by default)
- `TURSO_AUTH_TOKEN` - Database auth token (if using Turso)
- `NOTION_DATABASE_ID` - Notion database ID for task sync
- `DASHBOARD_HOST` - Dashboard host (default: 127.0.0.1)
- `DASHBOARD_PORT` - Dashboard port (default: 5000)
- `MAX_UNREAD_EMAILS` - Maximum number of unread emails to fetch (default: 100)
- `RECENT_EMAILS_COUNT` - Number of recent emails to fetch (default: 20)

### Database Configuration

The application supports two database options:

**Option 1: Local SQLite (Default - Recommended for development)**

No configuration needed! The application automatically creates a local `tasks.db` file.

For automated setup, run:
```bash
python setup_local_db.py
```

**Option 2: Turso Cloud Database (For production/cloud deployment)**

For cloud-based storage with Turso:
1. Create a database at [turso.tech](https://turso.tech)
2. Add to your `.env` file:
   ```
   TURSO_DATABASE_URL=libsql://your-database-name.turso.io
   TURSO_AUTH_TOKEN=your-turso-auth-token
   ```
3. Run the setup script:
   ```bash
   python setup_database.py
   ```

> **Note**: Arcade.dev handles authentication for external tools (Gmail, Slack, Calendar, etc.), while the LLM provider (OpenAI or DeepSeek) is used directly for AI-powered task extraction and analysis.

## Usage

### Run the Local Dashboard
```bash
python dashboard.py
# Access at http://127.0.0.1:5000
```

The dashboard provides:
- Real-time task statistics
- Task list with priority indicators
- Search functionality (semantic search)
- Add new tasks directly from the UI
- Auto-refresh every 30 seconds

### Extract tasks from Gmail
```bash
python agent.py
```

### Create a task from text
```bash
python main.py
```

### Use Arcade tools
```bash
python tools.py
```

### Sync tasks to Notion
```bash
python notion_sync.py
```

This will:
1. Check Notion authorization (redirect to login if needed)
2. Allow you to search for Notion databases
3. Sync local tasks to your Notion database
4. Create individual tasks in Notion

### Setup database

**For local SQLite (recommended for development):**
```bash
python setup_local_db.py
```

**For Turso cloud database:**
```bash
python setup_database.py
```

## Notion Integration

To use Notion integration:

1. Get your Notion database ID from the database URL:
   - Example: `https://notion.so/username/Tasks-abc123def456`
   - Database ID is: `abc123def456`

2. Add to your `.env` file:
   ```
   NOTION_DATABASE_ID=abc123def456
   ```

3. Your Notion database should have these properties:
   - **Name** (Title) - Task name
   - **Status** (Select) - Options: "To Do", "In Progress", "Done"
   - **Priority** (Select) - Options: "High", "Medium", "Low"
   - **Due Date** (Date) - Task due date

4. Run `python notion_sync.py` and authorize when prompted

## Dashboard API

The dashboard exposes a REST API:

- `GET /api/tasks` - List all tasks
- `POST /api/tasks` - Add a new task
- `GET /api/tasks/search?q=query` - Search tasks (semantic)
- `GET /api/stats` - Get task statistics

## Requirements

- Python 3.8+
- Thermal receipt printer (USB) - Optional
- Arcade.dev API key (for tool integrations)
- LLM API key: OpenAI or DeepSeek (for AI-powered task extraction)

## Architecture

The project uses:
- **Arcade.dev** for external tool integrations (Gmail, Notion, Slack, Calendar, etc.) with unified authentication
- **OpenAI or DeepSeek** for AI-powered task extraction and analysis (configurable via `LLM_PROVIDER`)

## License

MIT License - see LICENSE file for details.