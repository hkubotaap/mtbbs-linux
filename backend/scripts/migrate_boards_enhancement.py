"""
Migration script for Boards Enhancement
Adds new fields to boards and messages tables, creates user_read_positions table
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine
from app.models.board import Board, Message, UserReadPosition


async def migrate_boards_enhancement():
    """Migration for boards enhancement features"""
    print("Starting migration: Boards Enhancement")
    print("=" * 70)

    async with engine.begin() as conn:
        try:
            # Check if columns already exist
            print("\nChecking existing schema...")

            # Add columns to boards table
            print("\n1. Adding columns to boards table...")
            try:
                await conn.execute(text(
                    "ALTER TABLE boards ADD COLUMN enforced_news BOOLEAN DEFAULT 0"
                ))
                print("   ✓ Added 'enforced_news' column")
            except Exception as e:
                print(f"   ⚠ 'enforced_news' column may already exist: {e}")

            try:
                await conn.execute(text(
                    "ALTER TABLE boards ADD COLUMN operator_id VARCHAR(8)"
                ))
                print("   ✓ Added 'operator_id' column")
            except Exception as e:
                print(f"   ⚠ 'operator_id' column may already exist: {e}")

            # Add columns to messages table
            print("\n2. Adding columns to messages table...")
            try:
                await conn.execute(text(
                    "ALTER TABLE messages ADD COLUMN deleted BOOLEAN DEFAULT 0"
                ))
                print("   ✓ Added 'deleted' column")
            except Exception as e:
                print(f"   ⚠ 'deleted' column may already exist: {e}")

            try:
                await conn.execute(text(
                    "ALTER TABLE messages ADD COLUMN deleted_at DATETIME"
                ))
                print("   ✓ Added 'deleted_at' column")
            except Exception as e:
                print(f"   ⚠ 'deleted_at' column may already exist: {e}")

            try:
                await conn.execute(text(
                    "ALTER TABLE messages ADD COLUMN deleted_by VARCHAR(8)"
                ))
                print("   ✓ Added 'deleted_by' column")
            except Exception as e:
                print(f"   ⚠ 'deleted_by' column may already exist: {e}")

            # Create user_read_positions table
            print("\n3. Creating user_read_positions table...")
            try:
                await conn.run_sync(UserReadPosition.__table__.create, checkfirst=True)
                print("   ✓ Created 'user_read_positions' table")
            except Exception as e:
                print(f"   ⚠ 'user_read_positions' table may already exist: {e}")

            print("\n" + "=" * 70)
            print("Migration completed successfully!")
            print("\nNew features enabled:")
            print("  • Enforced News - Force display new messages on login")
            print("  • Board Operator - Assign operators to boards")
            print("  • Read Position Tracking - Track user's last read message")
            print("  • Message Soft Delete - Recoverable message deletion")
            print("=" * 70)

        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            raise


async def verify_migration():
    """Verify migration was successful"""
    print("\nVerifying migration...")

    async with engine.connect() as conn:
        # Check boards table
        result = await conn.execute(text("PRAGMA table_info(boards)"))
        boards_columns = {row[1] for row in result}

        required_board_columns = {'enforced_news', 'operator_id'}
        if required_board_columns.issubset(boards_columns):
            print("✓ Boards table has all new columns")
        else:
            print(f"❌ Boards table missing columns: {required_board_columns - boards_columns}")
            return False

        # Check messages table
        result = await conn.execute(text("PRAGMA table_info(messages)"))
        messages_columns = {row[1] for row in result}

        required_message_columns = {'deleted', 'deleted_at', 'deleted_by'}
        if required_message_columns.issubset(messages_columns):
            print("✓ Messages table has all new columns")
        else:
            print(f"❌ Messages table missing columns: {required_message_columns - messages_columns}")
            return False

        # Check user_read_positions table
        result = await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_read_positions'"
        ))
        if result.fetchone():
            print("✓ UserReadPosition table exists")
        else:
            print("❌ UserReadPosition table does not exist")
            return False

    print("\n✅ All migration checks passed!")
    return True


async def main():
    """Main migration execution"""
    print("\n🚀 MTBBS Boards Enhancement Migration")
    print("=" * 70)

    # Confirm before proceeding
    print("\nThis will modify the database schema.")
    print("Make sure you have a backup of your database!")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")

    try:
        input()
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user")
        return

    try:
        await migrate_boards_enhancement()
        await verify_migration()

        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("  1. Restart the backend server")
        print("  2. Test the new features in the admin UI")
        print("  3. Test enforced news on Telnet login")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nPlease restore from backup and check the error.")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
