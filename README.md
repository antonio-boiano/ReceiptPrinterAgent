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

## Configuration

### Required environment variables:
- `ARCADE_API_KEY` - Get from [arcade.dev](https://arcade.dev) - Used for tool integrations (Gmail, Slack, etc.)

### LLM Provider (choose one):
The agent uses a Large Language Model for task extraction and analysis. You can choose between OpenAI and DeepSeek:

**Option 1: OpenAI (default)**
- `OPENAI_API_KEY` - Get from [OpenAI](https://platform.openai.com/)

**Option 2: DeepSeek**
- `LLM_PROVIDER=deepseek` - Set this to use DeepSeek
- `DEEPSEEK_API_KEY` - Get from [DeepSeek](https://platform.deepseek.com/)

### Optional environment variables:
- `LLM_PROVIDER` - LLM provider: `openai` (default) or `deepseek`
- `TURSO_DATABASE_URL` - Database URL (optional, uses local SQLite by default)
- `TURSO_AUTH_TOKEN` - Database auth token (if using Turso)
- `NOTION_DATABASE_ID` - Notion database ID for task sync
- `DASHBOARD_HOST` - Dashboard host (default: 127.0.0.1)
- `DASHBOARD_PORT` - Dashboard port (default: 5000)

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