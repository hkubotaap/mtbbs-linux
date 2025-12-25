#!/usr/bin/env python3
"""
Add mail table migration

Creates the mail table for user-to-user messaging system.
"""

import sys
import os
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_connection


def migrate_add_mail_table(db_path: str):
    """
    Add mail table to database

    Args:
        db_path: Path to SQLite database
    """
    print(f"Starting migration: Add mail table")
    print(f"Database: {db_path}")

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Check if mail table already exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='mail'"
        )
        if cursor.fetchone():
            print("⚠️  Mail table already exists. Skipping migration.")
            return

        # Create mail table
        print("Creating mail table...")
        cursor.execute(
            """
            CREATE TABLE mail (
                mail_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT NOT NULL,
                sender_handle TEXT NOT NULL,
                recipient_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                sent_at TEXT NOT NULL,
                read_at TEXT,
                is_read INTEGER NOT NULL DEFAULT 0,
                is_deleted_by_sender INTEGER NOT NULL DEFAULT 0,
                is_deleted_by_recipient INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (sender_id) REFERENCES users(user_id),
                FOREIGN KEY (recipient_id) REFERENCES users(user_id)
            )
            """
        )

        # Create indexes for performance
        print("Creating indexes...")
        cursor.execute(
            "CREATE INDEX idx_mail_recipient ON mail(recipient_id, is_deleted_by_recipient, is_read)"
        )
        cursor.execute(
            "CREATE INDEX idx_mail_sender ON mail(sender_id, is_deleted_by_sender)"
        )
        cursor.execute(
            "CREATE INDEX idx_mail_sent_at ON mail(sent_at)"
        )

        conn.commit()
        print("✅ Mail table created successfully")

        # Verify table creation
        cursor.execute("SELECT COUNT(*) FROM mail")
        print(f"✅ Mail table verified (row count: {cursor.fetchone()[0]})")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


def main():
    """Main migration script"""
    import argparse

    parser = argparse.ArgumentParser(description='Add mail table migration')
    parser.add_argument(
        '--db',
        default='data/mtbbs.db',
        help='Database file path (default: data/mtbbs.db)'
    )

    args = parser.parse_args()

    # Convert to absolute path
    db_path = os.path.join(project_root, args.db)

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        print("Please create the database first by running the application.")
        sys.exit(1)

    try:
        migrate_add_mail_table(db_path)
        print("\n✅ Migration completed successfully")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
