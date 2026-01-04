# Receipt Printer Task Manager

A Python-based task management system that prints tasks to a thermal receipt printer and integrates with various services using Arcade.dev.

## Features

- Print tasks to thermal receipt printers
- Extract tasks from Gmail automatically
- AI-powered task parsing and prioritization
- Local SQLite database for task storage
- **Local Dashboard** - Web-based UI for task tracking and management
- **Notion Integration** - Sync tasks to Notion for team collaboration
- Integration with multiple services (Gmail, Slack, Calendar, Notion) via Arcade.dev

## Quick Start

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/CodingWithLewis/ReceiptPrinterAgent
cd ReceiptPrinterAgent

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys
# Required: ARCADE_API_KEY, OPENAI_API_KEY
```

### 3. Set Up Database

```bash
# Initialize the local SQLite database
python setup_database.py
```

### 4. Run the Application

```bash
# Option 1: Run the web dashboard
python dashboard.py
# Access at http://127.0.0.1:5000

# Option 2: Extract tasks from Gmail
python agent.py

# Option 3: Create a task from text input
python main.py
```

## Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `ARCADE_API_KEY` | Get from [arcade.dev](https://arcade.dev) |
| `OPENAI_API_KEY` | OpenAI API key for AI task parsing |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_PATH` | Path to SQLite database file | `tasks.db` |
| `NOTION_DATABASE_ID` | Notion database ID for task sync | - |
| `DASHBOARD_HOST` | Dashboard host address | `127.0.0.1` |
| `DASHBOARD_PORT` | Dashboard port number | `5000` |

## Usage

### Run the Local Dashboard
```bash
python dashboard.py
# Access at http://127.0.0.1:5000
```

The dashboard provides:
- Real-time task statistics
- Task list with priority indicators
- Search functionality
- Add new tasks directly from the UI
- Auto-refresh every 30 seconds

### Extract tasks from Gmail
```bash
python agent.py
```

This will:
1. Connect to your Gmail via Arcade (authorize if needed)
2. Analyze recent emails for actionable tasks
3. Extract and prioritize tasks using AI
4. Save new tasks to the local database

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
- `GET /api/tasks/search?q=query` - Search tasks
- `GET /api/stats` - Get task statistics

## Requirements

- Python 3.8+
- Thermal receipt printer (USB) - Optional
- API keys for OpenAI and Arcade.dev

## Architecture

The project uses:
- **Local SQLite database** for task storage (no external database required)
- **Arcade.dev** for all external integrations (Gmail, Notion, Calendar, Slack)
- **Flask** for the web dashboard

This provides a simple, self-contained setup with no need for remote database services.

## License

MIT License - see LICENSE file for details.