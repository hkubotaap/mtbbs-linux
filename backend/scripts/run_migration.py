"""
Simple migration script to add new columns - ASCII only for Windows compatibility
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def run_migration():
    """Add new columns to existing tables"""
    # Try both possible database locations
    db_path_data = Path(__file__).parent.parent / "data" / "mtbbs.db"
    db_path_root = Path(__file__).parent.parent / "mtbbs.db"

    if db_path_data.exists():
        db_path = db_path_data
    elif db_path_root.exists():
        db_path = db_path_root
    else:
        print("ERROR: Database file not found")
        print(f"Checked: {db_path_data}")
        print(f"Checked: {db_path_root}")
        return False

    print(f"Database: {db_path}")
    print("Starting migration...")

    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)

    async with engine.begin() as conn:
        # Add columns to boards table
        print("\n[1] Migrating boards table...")
        try:
            await conn.execute(text("ALTER TABLE boards ADD COLUMN enforced_news BOOLEAN DEFAULT 0"))
            print("    Added: enforced_news")
        except Exception as e:
            print(f"    Already exists or error: {str(e)[:50]}")

        try:
            await conn.execute(text("ALTER TABLE boards ADD COLUMN operator_id VARCHAR(8)"))
            print("    Added: operator_id")
        except Exception as e:
            print(f"    Already exists or error: {str(e)[:50]}")

        # Add columns to messages table
        print("\n[2] Migrating messages table...")
        try:
            await conn.execute(text("ALTER TABLE messages ADD COLUMN deleted BOOLEAN DEFAULT 0"))
            print("    Added: deleted")
        except Exception as e:
            print(f"    Already exists or error: {str(e)[:50]}")

        try:
            await conn.execute(text("ALTER TABLE messages ADD COLUMN deleted_at DATETIME"))
            print("    Added: deleted_at")
        except Exception as e:
            print(f"    Already exists or error: {str(e)[:50]}")

        try:
            await conn.execute(text("ALTER TABLE messages ADD COLUMN deleted_by VARCHAR(8)"))
            print("    Added: deleted_by")
        except Exception as e:
            print(f"    Already exists or error: {str(e)[:50]}")

    await engine.dispose()
    print("\n[OK] Migration completed!")
    return True

if __name__ == "__main__":
    result = asyncio.run(run_migration())
    sys.exit(0 if result else 1)
