"""Database setup script for local SQLite database."""

import os
import sqlite3
import sys
from dotenv import load_dotenv

load_dotenv()


def test_database():
    """Test database connection and functionality."""
    try:
        from src.database import TaskDatabase
        
        print("\n🔧 Testing database connection...")
        db = TaskDatabase()
        print(f"✅ Database connection successful ({db.db_path})")
        
        # Test adding a sample task
        from datetime import datetime
        
        class SampleTask:
            name = "Database Test Task"
            priority = 2
            due_date = datetime.now().isoformat()
        
        print("\n🧪 Testing task creation...")
        task_record = db.add_task(SampleTask(), email_context="Database setup test")
        print(f"✅ Created test task with ID: {task_record.id}")
        
        # Test search
        print("\n🔍 Testing task search...")
        similar_tasks = db.find_similar_tasks("database test", limit=1)
        if similar_tasks:
            print(f"✅ Found {len(similar_tasks)} matching task(s)")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False


def create_database_tables():
    """Create the required tables in local SQLite database."""
    
    from src.database import TaskDatabase
    
    # Get database path
    db_path = os.getenv("DATABASE_PATH", "tasks.db")
    
    print(f"📍 Database path: {db_path}")
    
    try:
        # Check if database file already exists
        if os.path.exists(db_path):
            print("⚠️  Database file already exists")
            recreate = input("Drop and recreate tables? (y/n): ").lower()
            if recreate == 'y':
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS tasks")
                conn.commit()
                cursor.close()
                conn.close()
                print("🗑️  Dropped existing table")
        
        # Create database and tables
        print("📝 Creating database and tables...")
        db = TaskDatabase(db_path=db_path)
        db.close()
        
        print("✅ Database tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        return False


def main():
    """Main setup function."""
    print("🗄️  Database Setup")
    print("=" * 30)
    
    # Check environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    arcade_key = os.getenv("ARCADE_API_KEY")
    
    print("Checking environment variables...")
    if openai_key:
        print("   ✅ OPENAI_API_KEY is set")
    else:
        print("   ⚠️  OPENAI_API_KEY not set (optional)")
        
    if arcade_key:
        print("   ✅ ARCADE_API_KEY is set")
    else:
        print("   ⚠️  ARCADE_API_KEY not set (required for email extraction)")
    
    # Ask about table creation
    print("\n" + "=" * 30)
    create_tables = input("Create/recreate database tables? (y/n): ").lower()
    
    if create_tables == 'y':
        if not create_database_tables():
            return
    
    # Test database
    print("\n" + "=" * 30)
    test_conn = input("Test database connection? (y/n): ").lower()
    
    if test_conn == 'y':
        if not test_database():
            return
    
    # Done
    print("\n" + "=" * 30)
    print("✅ Database setup complete!")
    print("\nYour database is ready. You can now run:")
    print("  - python agent.py      # Extract tasks from Gmail")
    print("  - python main.py       # Create a task from text")
    print("  - python dashboard.py  # Run the web dashboard")


if __name__ == "__main__":
    main()
