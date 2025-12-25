"""
Initialize test data for MTBBS
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.user_service import UserService
from app.services.board_service import BoardService
from app.core.database import init_db


async def main():
    """Initialize test data"""
    print("Initializing database...")
    await init_db()

    user_service = UserService()
    board_service = BoardService()

    # Create admin user
    print("Creating admin user...")
    try:
        admin = await user_service.create_user(
            user_id="admin",
            password="admin123",
            handle_name="Administrator",
            email="admin@mtbbs.local",
            level=9,
        )
        print(f"[OK] Created admin user: {admin.user_id}")
    except Exception as e:
        print(f"[SKIP] Admin user might already exist: {e}")

    # Create test user
    print("Creating test user...")
    try:
        user = await user_service.create_user(
            user_id="testuser",
            password="test123",
            handle_name="TestUser",
            email="test@mtbbs.local",
            level=1,
        )
        print(f"[OK] Created test user: {user.user_id}")
    except Exception as e:
        print(f"[SKIP] Test user might already exist: {e}")

    # Create boards
    boards_data = [
        (1, "General", "General discussion board", False, None),
        (2, "Announcements", "System announcements and news", True, "admin"),  # Enforced news
        (3, "Help", "Help and support", False, "admin"),
        (4, "Off-Topic", "Off-topic discussions", False, None),
    ]

    for board_id, name, description, enforced_news, operator_id in boards_data:
        print(f"Creating board: {name}...")
        try:
            board = await board_service.create_board(
                board_id=board_id,
                name=name,
                description=description,
                read_level=0,
                write_level=1,
                enforced_news=enforced_news,
                operator_id=operator_id,
            )
            print(f"[OK] Created board: {board.name} (enforced_news={enforced_news}, operator={operator_id})")

            # Create sample messages
            messages_data = [
                ("Welcome!", "Welcome to the MTBBS! This is a test message."),
                ("About this board", f"This is the {name} board. Feel free to post here!"),
            ]

            for title, body in messages_data:
                try:
                    msg = await board_service.create_message(
                        board_id=board_id,
                        user_id="admin",
                        handle_name="Administrator",
                        title=title,
                        body=body,
                    )
                    print(f"  [OK] Created message: {msg.title}")
                except Exception as e:
                    print(f"  [ERROR] Error creating message: {e}")

        except Exception as e:
            print(f"[SKIP] Board might already exist: {e}")

    print("\n" + "=" * 50)
    print("Test data initialization complete!")
    print("=" * 50)
    print("\nYou can now login with:")
    print("  User: admin / Password: admin123")
    print("  User: testuser / Password: test123")
    print("\nTelnet: telnet localhost 23")
    print("Web Admin: http://localhost:3000")


if __name__ == "__main__":
    asyncio.run(main())
