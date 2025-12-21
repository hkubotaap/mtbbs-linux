"""
Telnet Handler - BBS Session Management
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from app.resources.messages_ja import MTBBS_VERSION
from app.services.user_service import UserService
from app.services.board_service import BoardService
from app.services.message_service import MessageService
from app.core.config import settings

logger = logging.getLogger(__name__)


class TelnetHandler:
    """Handles individual Telnet BBS session"""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, client_id: str):
        self.reader = reader
        self.writer = writer
        self.client_id = client_id

        # Session state
        self.user_id: Optional[str] = None
        self.handle_name: Optional[str] = None
        self.user_level: int = 0
        self.connected_at = datetime.now()
        self.authenticated = False

        # Services
        self.user_service = UserService()
        self.board_service = BoardService()
        self.message_service = MessageService()

        # Input buffer
        self.input_buffer = ""

    async def handle(self):
        """Main session handler"""
        try:
            await self.send_opening_message()
            await self.login()

            if self.authenticated:
                await self.main_loop()

        except asyncio.CancelledError:
            logger.info(f"Session cancelled: {self.client_id}")
        except Exception as e:
            logger.error(f"Session error {self.client_id}: {e}", exc_info=True)
        finally:
            await self.disconnect()

    async def send(self, text: str):
        """Send text to client"""
        try:
            self.writer.write(text.encode("utf-8"))
            await self.writer.drain()
        except Exception as e:
            logger.error(f"Send error: {e}")
            raise

    async def send_line(self, text: str = ""):
        """Send text with newline"""
        await self.send(text + "\r\n")

    async def receive_line(self, echo: bool = True) -> str:
        """Receive line of input from client"""
        line = ""
        try:
            while True:
                data = await self.reader.read(1)
                if not data:
                    raise ConnectionError("Connection closed")

                char = data.decode("utf-8", errors="ignore")

                if char == "\r" or char == "\n":
                    if line:
                        if echo:
                            await self.send("\r\n")
                        return line
                elif char == "\x08" or char == "\x7f":  # Backspace
                    if line:
                        line = line[:-1]
                        if echo:
                            await self.send("\x08 \x08")
                elif char >= " ":
                    line += char
                    if echo:
                        await self.send(char)
        except Exception as e:
            logger.error(f"Receive error: {e}")
            raise

    async def send_opening_message(self):
        """Send welcome message"""
        access_count = await self.user_service.get_access_count()

        msg = await self.message_service.get_message_content(
            "OPENING_MESSAGE",
            date=datetime.now().strftime("%Y/%m/%d"),
            weekday=["月", "火", "水", "木", "金", "土", "日"][datetime.now().weekday()],
            access_count=access_count,
        )
        await self.send(msg)

    async def login(self):
        """Login process"""
        max_attempts = 3

        for attempt in range(max_attempts):
            await self.send_line("\r\nUser ID: ")
            user_id = await self.receive_line()

            if not user_id:
                continue

            await self.send_line("Password: ")
            password = await self.receive_line(echo=False)

            # Guest login
            if user_id.lower() == "guest":
                self.user_id = "guest"
                self.handle_name = "Guest"
                self.user_level = 0
                self.authenticated = True
                await self.send_login_message()
                await self.user_service.record_login(user_id, self.client_id.split(":")[0])
                return

            # Regular user login
            user = await self.user_service.authenticate(user_id, password)
            if user:
                self.user_id = user.user_id
                self.handle_name = user.handle_name
                self.user_level = user.level
                self.authenticated = True
                await self.send_login_message()
                await self.user_service.record_login(user_id, self.client_id.split(":")[0])
                return
            else:
                await self.send_line("\r\nInvalid user ID or password.")

        await self.send_line("\r\nToo many failed attempts. Disconnecting.")

    async def send_login_message(self):
        """Send login success message"""
        hour = datetime.now().hour
        if 5 <= hour < 11:
            greeting = "おはようございます"
        elif 11 <= hour < 18:
            greeting = "こんにちは"
        else:
            greeting = "こんばんは"

        msg = await self.message_service.get_message_content(
            "LOGIN_MESSAGE",
            handle=self.handle_name,
            greeting=greeting
        )
        await self.send(msg)

    async def main_loop(self):
        """Main command loop"""
        while True:
            await self.show_main_menu()
            await self.send_line("\r\nCommand: ")
            command = await self.receive_line()

            if not command:
                continue

            cmd = command.upper().strip()

            try:
                if cmd == "Q":
                    await self.logout()
                    break
                elif cmd == "N":
                    await self.news()
                elif cmd == "R":
                    await self.read_board()
                elif cmd == "E":
                    await self.enter_message()
                elif cmd == "M":
                    await self.read_mail()
                elif cmd == "H" or cmd == "?":
                    await self.show_help()
                elif cmd == "U":
                    await self.show_users()
                elif cmd == "W":
                    await self.who_online()
                elif cmd == "Y":
                    await self.system_info()
                elif cmd == "_":
                    await self.version()
                elif cmd == "#":
                    await self.status()
                else:
                    await self.send_line("Unknown command. Type H for help.")
            except Exception as e:
                logger.error(f"Command error: {e}", exc_info=True)
                await self.send_line(f"Error: {str(e)}")

    async def show_main_menu(self):
        """Display main menu"""
        msg = await self.message_service.get_message_content(
            "MAIN_MENU",
            version=MTBBS_VERSION,
            time=datetime.now().strftime("%H:%M"),
            user_id=self.user_id,
            handle=self.handle_name,
        )
        await self.send(msg)

    async def news(self):
        """Show new messages"""
        await self.send_line("\r\n=== New Messages ===")
        boards = await self.board_service.get_boards()
        for board in boards:
            new_count = await self.board_service.get_new_message_count(board.id, self.user_id)
            if new_count > 0:
                await self.send_line(f"Board {board.board_id}: {board.name} ({new_count} new)")

    async def read_board(self):
        """Read message board"""
        await self.send_line("\r\nBoard number (0 to cancel): ")
        board_no = await self.receive_line()

        if not board_no or board_no == "0":
            return

        try:
            board_id = int(board_no)
            messages = await self.board_service.get_recent_messages(board_id, limit=20)

            await self.send_line(f"\r\n=== Board {board_id} ===")
            for msg in messages:
                await self.send_line(
                    f"[{msg.message_no}] {msg.title} - {msg.handle_name} ({msg.created_at.strftime('%Y/%m/%d %H:%M')})"
                )

            await self.send_line("\r\nMessage number to read (0 to cancel): ")
            msg_no = await self.receive_line()

            if msg_no and msg_no != "0":
                message = await self.board_service.get_message(board_id, int(msg_no))
                if message:
                    await self.display_message(message)

        except ValueError:
            await self.send_line("Invalid board number.")

    async def enter_message(self):
        """Post new message"""
        await self.send_line("\r\nBoard number: ")
        board_no = await self.receive_line()

        try:
            board_id = int(board_no)

            await self.send_line("Title: ")
            title = await self.receive_line()

            if not title:
                await self.send_line("Title is required.")
                return

            await self.send_line("Body (end with . on a line by itself):")
            body_lines = []

            while True:
                line = await self.receive_line()
                if line == ".":
                    break
                body_lines.append(line)

            body = "\n".join(body_lines)

            message = await self.board_service.create_message(
                board_id=board_id,
                user_id=self.user_id,
                handle_name=self.handle_name,
                title=title,
                body=body,
            )

            await self.send_line(f"\r\nMessage #{message.message_no} posted successfully.")

        except ValueError:
            await self.send_line("Invalid board number.")
        except Exception as e:
            await self.send_line(f"Error posting message: {str(e)}")

    async def display_message(self, message):
        """Display a message"""
        await self.send_line("\r\n" + "=" * 70)
        await self.send_line(f"From: {message.handle_name} ({message.user_id})")
        await self.send_line(f"Date: {message.created_at.strftime('%Y/%m/%d %H:%M:%S')}")
        await self.send_line(f"Title: {message.title}")
        await self.send_line("=" * 70)
        await self.send_line(message.body)
        await self.send_line("=" * 70)

    async def read_mail(self):
        """Read mail (placeholder)"""
        await self.send_line("\r\nMail system not yet implemented.")

    async def show_help(self):
        """Show help"""
        msg = await self.message_service.get_message_content("HELP_MESSAGE")
        await self.send(msg)

    async def show_users(self):
        """Show user list"""
        users = await self.user_service.get_recent_users(limit=20)
        await self.send_line("\r\n=== User List ===")
        for user in users:
            last_login = user.last_login.strftime("%Y/%m/%d") if user.last_login else "Never"
            await self.send_line(f"{user.user_id:8s} {user.handle_name:14s} Level:{user.level} Last:{last_login}")

    async def who_online(self):
        """Show who's online (placeholder)"""
        await self.send_line(f"\r\n=== Online Users ===")
        await self.send_line(f"{self.handle_name} ({self.user_id}) - You")

    async def system_info(self):
        """Show system information"""
        msg = await self.message_service.get_message_content(
            "SYSINFO_MESSAGE",
            version=MTBBS_VERSION
        )
        await self.send(msg)

    async def version(self):
        """Show version"""
        msg = await self.message_service.get_message_content(
            "HOST_VERSION",
            version=MTBBS_VERSION
        )
        await self.send(msg)

    async def status(self):
        """Show user status"""
        await self.send_line(f"\r\n=== Status ===")
        await self.send_line(f"User ID: {self.user_id}")
        await self.send_line(f"Handle: {self.handle_name}")
        await self.send_line(f"Level: {self.user_level}")
        await self.send_line(f"Connected: {self.connected_at.strftime('%Y/%m/%d %H:%M:%S')}")

    async def logout(self):
        """Logout"""
        msg = await self.message_service.get_message_content(
            "LOGOUT_MESSAGE",
            handle=self.handle_name
        )
        await self.send(msg)
        await self.user_service.record_logout(self.user_id)

    async def disconnect(self):
        """Disconnect client"""
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass
