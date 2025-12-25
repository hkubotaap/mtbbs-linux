"""
Telnet Handler - BBS Session Management
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Optional
from app.resources.messages_ja import MTBBS_VERSION
from app.services.user_service import UserService
from app.services.board_service import BoardService
from app.services.message_service import MessageService
from app.services.mail_service import MailService
from app.core.config import settings
from app.utils.rate_limiter import get_rate_limiter, RateLimitExceeded
from app.utils.input_sanitizer import (
    sanitize_text, sanitize_user_id, sanitize_title,
    sanitize_message_body, sanitize_command,
    detect_sql_injection, detect_xss
)

logger = logging.getLogger(__name__)


class TelnetHandler:
    """Handles individual Telnet BBS session"""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, client_id: str, server=None):
        self.reader = reader
        self.writer = writer
        self.client_id = client_id
        self.server = server  # Reference to TelnetServer for chat broadcasting

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

        # Get absolute path to database
        # __file__ is backend/app/protocols/telnet_handler.py
        # Go up from protocols -> app -> backend -> mtbbs-linux (project root)
        this_file = os.path.abspath(__file__)  # backend/app/protocols/telnet_handler.py
        app_dir = os.path.dirname(os.path.dirname(this_file))  # backend/app
        backend_dir = os.path.dirname(app_dir)  # backend
        project_root = os.path.dirname(backend_dir)  # mtbbs-linux
        db_path = os.path.join(project_root, "data", "mtbbs.db")
        self.mail_service = MailService(db_path)

        # Input buffer
        self.input_buffer = ""

        # Command line for continuous execution (e.g., "n@", "r0@")
        self.command_line = ""

        # Terminal size
        self.terminal_width = 80
        self.terminal_height = 24

    async def handle(self):
        """Main session handler"""
        try:
            # Send Telnet options to indicate Shift-JIS encoding and request terminal size
            # IAC WILL BINARY
            self.writer.write(bytes([255, 251, 0]))
            # IAC DO NAWS (Negotiate About Window Size)
            self.writer.write(bytes([255, 253, 31]))
            # IAC WILL ECHO (server handles echo)
            self.writer.write(bytes([255, 251, 1]))
            # IAC WILL SUPPRESS-GO-AHEAD
            self.writer.write(bytes([255, 251, 3]))
            await self.writer.drain()

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
        """Send text to client (Shift-JIS encoding with CR+LF line endings)"""
        try:
            # Convert LF to CR+LF for proper telnet line endings
            text = text.replace("\r\n", "\n").replace("\n", "\r\n")
            self.writer.write(text.encode("cp932", errors="replace"))
            await self.writer.drain()
        except Exception as e:
            logger.error(f"Send error: {e}")
            raise

    async def send_line(self, text: str = ""):
        """Send text with newline (CR+LF)"""
        await self.send(text + "\r\n")

    async def receive_line(self, echo: bool = True) -> str:
        """Receive line of input from client with Telnet IAC filtering and CP932 multi-byte support"""
        raw_bytes = bytearray()
        try:
            while True:
                data = await self.reader.read(1)
                if not data:
                    raise ConnectionError("Connection closed")

                byte_val = data[0]

                # Handle Telnet IAC (Interpret As Command) sequences
                if byte_val == 0xFF:  # IAC
                    # Read command byte
                    cmd_data = await self.reader.read(1)
                    if not cmd_data:
                        break
                    cmd = cmd_data[0]

                    # Commands that take an option byte (WILL, WONT, DO, DONT, SB)
                    if cmd in [0xFB, 0xFC, 0xFD, 0xFE, 0xFA]:
                        opt_data = await self.reader.read(1)
                        if cmd == 0xFA:  # SB (subnegotiation) - read until SE
                            while True:
                                sb_data = await self.reader.read(1)
                                if not sb_data:
                                    break
                                if sb_data[0] == 0xFF:
                                    se_data = await self.reader.read(1)
                                    if se_data and se_data[0] == 0xF0:  # SE
                                        break
                    # Skip IAC sequence and continue
                    continue

                # Check for line endings
                if byte_val == 0x0D or byte_val == 0x0A:  # CR or LF
                    if raw_bytes:
                        if echo:
                            await self.send("\r\n")
                        # Decode the complete byte sequence as CP932
                        try:
                            line = raw_bytes.decode("cp932", errors="replace")
                        except Exception as e:
                            logger.error(f"Decode error: {e}")
                            line = raw_bytes.decode("utf-8", errors="replace")

                        # Debug: log received input with byte representation
                        logger.info(f"Input received (raw): {line!r}")
                        logger.info(f"Input bytes (hex): {raw_bytes.hex()}")
                        # Strip leading/trailing whitespace including full-width spaces
                        cleaned = line.strip().replace('\u3000', '')
                        logger.info(f"Input cleaned: {cleaned!r}")
                        return cleaned
                    continue  # Skip empty lines (just CR/LF)

                # Handle backspace
                elif byte_val == 0x08 or byte_val == 0x7F:  # Backspace or DEL
                    if raw_bytes:
                        # Remove last character (may be 1 or 2 bytes for CP932)
                        if len(raw_bytes) >= 2 and raw_bytes[-2] >= 0x81:
                            # Last char was 2-byte (Shift-JIS lead byte)
                            raw_bytes = raw_bytes[:-2]
                        else:
                            # Last char was 1-byte (ASCII)
                            raw_bytes = raw_bytes[:-1]
                        if echo:
                            await self.send("\x08 \x08")
                else:
                    # Skip NULL bytes (0x00) which some telnet clients send
                    if byte_val == 0x00:
                        logger.info(f"Skipping NULL byte (0x00)")
                        continue
                    # Accumulate bytes
                    raw_bytes.append(byte_val)
                    # Echo back raw byte (terminal will handle display)
                    if echo:
                        self.writer.write(bytes([byte_val]))
                        await self.writer.drain()
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
        """Login process with rate limiting"""
        max_attempts = 3
        rate_limiter = get_rate_limiter()

        # レート制限チェック（IP単位で3回/60秒）
        ip_address = self.client_id.split(":")[0]
        allowed, remaining = rate_limiter.check_rate_limit(
            key=f"login:{ip_address}",
            max_calls=3,
            period=60
        )

        if not allowed:
            await self.send_line("\r\nToo many login attempts. Please wait 60 seconds.")
            logger.warning(f"Rate limit exceeded for login from {ip_address}")
            return

        for attempt in range(max_attempts):
            prompt = "\r\nUser ID: "
            logger.info(f"Sending prompt: {prompt!r}")
            await self.send(prompt)
            user_id_raw = await self.receive_line()

            if not user_id_raw:
                continue

            # ユーザーIDのサニタイゼーション
            user_id = sanitize_user_id(user_id_raw)

            if not user_id:
                await self.send_line("\r\nInvalid user ID format.")
                continue

            await self.send("Password: ")
            password = await self.receive_line(echo=False)

            # Guest login
            if user_id.lower() == "guest":
                self.user_id = "guest"
                self.handle_name = "Guest"
                self.user_level = 0
                self.authenticated = True
                await self.send_login_message()
                await self.user_service.record_login(user_id, self.client_id.split(":")[0])

                # Update session state in monitor
                if self.server:
                    self.server.update_session_login(self.client_id, "guest")

                await self.display_enforced_news()  # Display enforced news boards
                # ログイン成功時は制限をリセット
                rate_limiter.reset(f"login:{ip_address}")
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

                # Update session state in monitor
                if self.server:
                    self.server.update_session_login(self.client_id, user.user_id)

                await self.display_enforced_news()  # Display enforced news boards
                # ログイン成功時は制限をリセット
                rate_limiter.reset(f"login:{ip_address}")
                return
            else:
                await self.send_line("\r\nInvalid user ID or password.")
                # 失敗時はレート制限カウントを記録
                rate_limiter.record_call(f"login:{ip_address}")

        await self.send_line("\r\nToo many failed attempts. Disconnecting.")
        logger.warning(f"Login failed after {max_attempts} attempts from {ip_address}")

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

    async def display_enforced_news(self):
        """Display enforced news boards on login"""
        enforced_boards = await self.board_service.get_enforced_news_boards()

        if not enforced_boards:
            return

        # Get customizable header from system messages
        header = await self.message_service.get_message_content(
            "ENFORCED_NEWS_HEADER",
            default="=== IMPORTANT NEWS ==="
        )

        await self.send_line("\r\n" + "=" * 70)
        await self.send_line(header)
        await self.send_line("=" * 70)

        for board in enforced_boards:
            if board.read_level > self.user_level:
                continue

            # Get new messages
            new_count = await self.board_service.get_new_message_count(
                board.board_id,
                self.user_id
            )

            if new_count > 0:
                await self.send_line(f"\r\nBoard: {board.name}")
                await self.send_line(f"{new_count} new message(s)\r\n")

                # Display all new messages
                last_read = await self.board_service.get_read_position(
                    self.user_id,
                    board.board_id
                )

                messages = await self.board_service.get_all_messages(board.board_id)
                new_messages = [m for m in messages if m.message_no > last_read]

                for msg in new_messages:
                    await self.display_message(msg)
                    # Update read position
                    await self.board_service.update_read_position(
                        self.user_id,
                        board.board_id,
                        msg.message_no
                    )

        await self.send_line("=" * 70)
        # Note: Original MTBBS does not wait for user input here
        # Just display the enforced news and continue to main menu

    async def main_loop(self):
        """Main command loop with continuous command execution support"""
        while True:
            await self.show_main_menu()
            await self.send("\r\nCommand: ")
            command = await self.receive_line()
            logger.info(f"DEBUG: Command value received: {command!r}, type: {type(command)}, bool: {bool(command)}")

            if not command:
                logger.info("DEBUG: Command is empty, continuing")
                continue

            # Parse command: first character is the main command, rest is command_line
            full_cmd = command.upper().strip()
            cmd = full_cmd[0] if full_cmd else ""
            self.command_line = full_cmd[1:] if len(full_cmd) > 1 else ""

            # Debug log
            logger.info(f"Command received: full_cmd='{full_cmd}', cmd='{cmd}', command_line='{self.command_line}'")
            logger.info(f"Command character code: {ord(cmd) if cmd else 'empty'}")
            if cmd == "@":
                logger.info("DEBUG: @ command detected, calling sysop_menu()")
            elif "@" in full_cmd:
                logger.info(f"DEBUG: @ found in full_cmd but cmd='{cmd}', @ ord={ord('@')}")

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
                elif cmd == "A":
                    await self.apply_user()
                elif cmd == "H" or cmd == "?":
                    await self.show_help()
                elif cmd == "U":
                    await self.show_users()
                elif cmd == "W":
                    await self.who_online()
                elif cmd == "C":
                    await self.chat()
                elif cmd == "I":
                    await self.install()
                elif cmd == "O":
                    await self.profile()
                elif cmd == "@":
                    await self.sysop_menu()
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
            finally:
                # Clear command_line after execution
                self.command_line = ""

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
        """Show new messages with auto-read support (n@)"""
        auto_read = "@" in self.command_line

        await self.send_line("\r\n=== New Messages ===")
        boards = await self.board_service.get_boards()

        has_new = False
        for board in boards:
            if board.read_level > self.user_level:
                continue

            new_count = await self.board_service.get_new_message_count(board.board_id, self.user_id)
            if new_count > 0:
                has_new = True
                await self.send_line(f"Board {board.board_id}: {board.name} ({new_count} new)")

                if auto_read:
                    # Auto-read mode: display all unread messages
                    unread_messages = await self.board_service.get_unread_messages(board.board_id, self.user_id)
                    for msg in unread_messages:
                        await self.display_message(msg)
                        # Update read position after each message
                        await self.board_service.update_read_position(
                            self.user_id,
                            board.board_id,
                            msg.message_no
                        )

        if not has_new:
            await self.send_line("新着メッセージはありません。")

        await self.send_line("=" * 70)
        # Note: Original MTBBS does not wait for user input here
        logger.info("NEWS COMMAND COMPLETED - NO PRESS ENTER PROMPT SENT")

    async def read_board(self):
        """Read message board with continuous command support (r0@)"""
        # Parse command_line for board number and auto-read flag
        auto_read = "@" in self.command_line
        board_no_str = self.command_line.replace("@", "").strip()

        # If board number not in command_line, show board list and prompt
        if not board_no_str:
            boards = await self.board_service.get_boards()
            await self.send_line("\r\n=== Message Boards ===")
            for board in boards:
                if board.read_level <= self.user_level:
                    msg_count = len(await self.board_service.get_all_messages(board.board_id))
                    await self.send_line(f"[{board.board_id}] {board.name:20s} ({msg_count} messages) - {board.description or ''}")

            await self.send("\r\nBoard number (0 to cancel): ")
            board_no_str = await self.receive_line()

        if not board_no_str or board_no_str == "0":
            return

        try:
            board_id = int(board_no_str)
            board = await self.board_service.get_board(board_id)

            if not board:
                await self.send_line("Board not found.")
                return

            if board.read_level > self.user_level:
                await self.send_line("Access denied. Insufficient level.")
                return

            # Auto-read mode (r0@): Display all messages automatically
            if auto_read:
                messages = await self.board_service.get_all_messages(board_id)
                await self.send_line(f"\r\n=== Board {board_id}: {board.name} ===")
                if not messages:
                    await self.send_line("No messages in this board.")
                    return

                for msg in messages:
                    await self.display_message(msg)
                    await self.board_service.update_read_position(
                        self.user_id,
                        board_id,
                        msg.message_no
                    )
                return

            # Interactive mode: Show Read submenu
            await self.read_board_submenu(board_id, board)

        except ValueError:
            await self.send_line("Invalid board number.")
        except Exception as e:
            logger.error(f"Read board error: {e}", exc_info=True)
            await self.send_line(f"Error: {str(e)}")

    async def read_board_submenu(self, board_id: int, board):
        """Read board submenu (R/I/S/L/Q)"""
        while True:
            # Get message count and unread count
            all_messages = await self.board_service.get_all_messages(board_id)
            unread_messages = await self.board_service.get_unread_messages(board_id, self.user_id)
            last_read = await self.board_service.get_read_position(self.user_id, board_id)

            await self.send_line(f"\r\n=== Board {board_id}: {board.name} ===")
            await self.send_line(f"Total: {len(all_messages)} messages | Unread: {len(unread_messages)} messages | Last read: #{last_read}")
            await self.send_line("\r\nR) Read sequential  I) Individual select  S) Search  L) List  Q) Quit")
            await self.send("READ> ")

            command = await self.receive_line()
            if not command:
                continue

            command = command.upper().strip()

            if command == 'Q' or command == '':
                break

            elif command == 'R':
                # Sequential read from last position
                await self.read_sequential(board_id, board)

            elif command == 'I':
                # Individual message select
                await self.read_individual(board_id, board)

            elif command == 'S':
                # Search messages
                await self.read_search(board_id, board)

            elif command == 'L':
                # List messages
                await self.read_list(board_id, board)

            else:
                await self.send_line("Invalid command.")

    async def read_sequential(self, board_id: int, board):
        """Sequential read from last read position"""
        unread_messages = await self.board_service.get_unread_messages(board_id, self.user_id)

        if not unread_messages:
            await self.send_line("\r\nNo unread messages.")
            return

        await self.send_line(f"\r\n{len(unread_messages)} unread message(s). Reading sequentially...")

        for msg in unread_messages:
            await self.display_message(msg)
            await self.board_service.update_read_position(
                self.user_id,
                board_id,
                msg.message_no
            )

            # Prompt to continue or stop
            if msg != unread_messages[-1]:
                await self.send("\r\nPress Enter to continue, Q to quit: ")
                choice = await self.receive_line()
                if choice and choice.upper() == 'Q':
                    break

    async def read_individual(self, board_id: int, board):
        """Individual message selection"""
        messages = await self.board_service.get_recent_messages(board_id, limit=20)

        if not messages:
            await self.send_line("\r\nNo messages in this board.")
            return

        # Show recent messages
        await self.send_line("\r\n=== Recent Messages ===")
        for msg in reversed(messages):
            await self.send_line(
                f"[{msg.message_no}] {msg.title} - {msg.handle_name} ({msg.created_at.strftime('%Y/%m/%d %H:%M')})"
            )

        await self.send("\r\nMessage number to read (0 to cancel): ")
        msg_no_str = await self.receive_line()

        if not msg_no_str or msg_no_str == "0":
            return

        try:
            msg_no = int(msg_no_str)
            message = await self.board_service.get_message(board_id, msg_no)
            if message:
                await self.display_message(message)
                await self.board_service.update_read_position(
                    self.user_id,
                    board_id,
                    message.message_no
                )
            else:
                await self.send_line("Message not found.")
        except ValueError:
            await self.send_line("Invalid message number.")

    async def read_search(self, board_id: int, board):
        """Search messages by keyword"""
        await self.send("Search keyword: ")
        keyword = await self.receive_line()

        if not keyword:
            return

        messages = await self.board_service.search_messages(board_id, keyword, limit=50)

        if not messages:
            await self.send_line(f"\r\nNo messages found for '{keyword}'.")
            return

        await self.send_line(f"\r\n{len(messages)} message(s) found:")
        for msg in messages:
            await self.send_line(
                f"[{msg.message_no}] {msg.title} - {msg.handle_name} ({msg.created_at.strftime('%Y/%m/%d %H:%M')})"
            )

        # Allow selecting from search results
        await self.send("\r\nMessage number to read (0 to cancel): ")
        msg_no_str = await self.receive_line()

        if not msg_no_str or msg_no_str == "0":
            return

        try:
            msg_no = int(msg_no_str)
            message = await self.board_service.get_message(board_id, msg_no)
            if message:
                await self.display_message(message)
                await self.board_service.update_read_position(
                    self.user_id,
                    board_id,
                    message.message_no
                )
            else:
                await self.send_line("Message not found.")
        except ValueError:
            await self.send_line("Invalid message number.")

    async def read_list(self, board_id: int, board):
        """List all messages"""
        messages = await self.board_service.get_all_messages(board_id)

        if not messages:
            await self.send_line("\r\nNo messages in this board.")
            return

        await self.send_line(f"\r\n=== All Messages ({len(messages)} total) ===")
        for msg in messages:
            await self.send_line(
                f"[{msg.message_no}] {msg.title} - {msg.handle_name} ({msg.created_at.strftime('%Y/%m/%d %H:%M')})"
            )

        # Allow selecting from list
        await self.send("\r\nMessage number to read (0 to cancel): ")
        msg_no_str = await self.receive_line()

        if not msg_no_str or msg_no_str == "0":
            return

        try:
            msg_no = int(msg_no_str)
            message = await self.board_service.get_message(board_id, msg_no)
            if message:
                await self.display_message(message)
                await self.board_service.update_read_position(
                    self.user_id,
                    board_id,
                    message.message_no
                )
            else:
                await self.send_line("Message not found.")
        except ValueError:
            await self.send_line("Invalid message number.")

    async def enter_message(self):
        """Post new message with continuous command support (e0)"""
        # Parse command_line for board number
        board_no_str = self.command_line.strip()

        # If board number not in command_line, show board list and prompt
        if not board_no_str:
            boards = await self.board_service.get_boards()
            await self.send_line("\r\n=== Message Boards ===")
            for board in boards:
                if board.write_level <= self.user_level:
                    await self.send_line(f"[{board.board_id}] {board.name} - {board.description or ''}")

            await self.send("\r\nBoard number (0 to cancel): ")
            board_no_str = await self.receive_line()

        if not board_no_str or board_no_str == "0":
            return

        try:
            board_id = int(board_no_str)
            board = await self.board_service.get_board(board_id)

            if not board:
                await self.send_line("Board not found.")
                return

            if board.write_level > self.user_level:
                await self.send_line("Access denied. Insufficient level.")
                return

            await self.send("Title: ")
            title_raw = await self.receive_line()

            if not title_raw:
                await self.send_line("Title is required.")
                return

            # タイトルのサニタイゼーション
            title = sanitize_title(title_raw)

            # XSS/SQLインジェクション検出
            if detect_xss(title_raw) or detect_sql_injection(title_raw):
                await self.send_line("Invalid characters detected in title. Please try again.")
                logger.warning(f"Suspicious input detected in title from {self.user_id}: {title_raw!r}")
                return

            await self.send_line("Body (end with . on a line by itself):")
            await self.send_line("")
            body_lines = []

            while True:
                line = await self.receive_line()
                if line == ".":
                    break
                body_lines.append(line)

            body_raw = "\n".join(body_lines)

            # 本文のサニタイゼーション
            body = sanitize_message_body(body_raw)

            # XSS/SQLインジェクション検出
            if detect_xss(body_raw) or detect_sql_injection(body_raw):
                await self.send_line("Invalid characters detected in message body. Please try again.")
                logger.warning(f"Suspicious input detected in body from {self.user_id}")
                return

            if not body:
                await self.send_line("Message body is required.")
                return

            message = await self.board_service.create_message(
                board_id=board_id,
                user_id=self.user_id,
                handle_name=self.handle_name,
                title=title,
                body=body,
            )

            await self.send_line(f"\r\nMessage #{message.message_no} posted successfully to board '{board.name}'.")

        except ValueError:
            await self.send_line("Invalid board number.")
        except Exception as e:
            logger.error(f"Enter message error: {e}", exc_info=True)
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
        """Mail system main menu"""
        if not self.authenticated or self.user_id == "guest":
            await self.send_line("\r\nGuest users cannot access mail system.")
            return

        while True:
            # Get unread count
            unread_count = await self.mail_service.get_unread_count(self.user_id)

            # Show mail menu
            await self.send_line("\r\n" + "=" * 70)
            await self.send_line(f"Mail System - {self.handle_name}")
            await self.send_line("=" * 70)
            await self.send_line(f"Unread messages: {unread_count}")
            await self.send_line("")
            await self.send_line("R) Read Inbox")
            await self.send_line("S) Send Mail")
            await self.send_line("T) Sent Mail")
            await self.send_line("Q) Quit")
            await self.send_line("")
            await self.send("Command: ")

            command = await self.receive_line()
            if not command:
                continue

            command = command.upper().strip()

            if command == 'R':
                await self.mail_read_inbox()
            elif command == 'S':
                await self.mail_send()
            elif command == 'T':
                await self.mail_sent_box()
            elif command == 'Q':
                break
            else:
                await self.send_line("\r\nInvalid command.")

    async def mail_read_inbox(self):
        """Read inbox"""
        mails = await self.mail_service.get_inbox(self.user_id, include_read=True)

        if not mails:
            await self.send_line("\r\nNo mail in inbox.")
            return

        # Display mail list
        await self.send_line("\r\n" + "=" * 70)
        await self.send_line("Inbox")
        await self.send_line("=" * 70)
        await self.send_line(f"{'#':<4} {'Status':<6} {'From':<15} {'Subject':<30} {'Date':<15}")
        await self.send_line("-" * 70)

        for idx, mail in enumerate(mails, 1):
            status = "Read" if mail.is_read else "NEW"
            subject = mail.subject[:28] + ".." if len(mail.subject) > 30 else mail.subject
            date_str = mail.sent_at.strftime("%Y-%m-%d %H:%M")
            await self.send_line(
                f"{idx:<4} {status:<6} {mail.sender_id:<15} {subject:<30} {date_str:<15}"
            )

        # Select mail to read
        await self.send_line("")
        await self.send("Read mail number (or Q to quit): ")

        selection = await self.receive_line()
        if not selection or selection.upper() == 'Q':
            return

        try:
            mail_num = int(selection)
            if 1 <= mail_num <= len(mails):
                await self.mail_display(mails[mail_num - 1])
            else:
                await self.send_line("\r\nInvalid mail number.")
        except ValueError:
            await self.send_line("\r\nInvalid input.")

    async def mail_display(self, mail):
        """Display a mail message"""
        # Mark as read
        if not mail.is_read:
            await self.mail_service.mark_as_read(mail.mail_id, self.user_id)

        # Display mail
        await self.send_line("\r\n" + "=" * 70)
        await self.send_line(f"From: {mail.sender_handle} ({mail.sender_id})")
        await self.send_line(f"Date: {mail.sent_at.strftime('%Y-%m-%d %H:%M:%S')}")
        await self.send_line(f"Subject: {mail.subject}")
        await self.send_line("=" * 70)
        await self.send_line(mail.body)
        await self.send_line("=" * 70)

        # Actions
        await self.send_line("")
        await self.send_line("D) Delete  R) Reply  Q) Back")
        await self.send("Action: ")

        action = await self.receive_line()
        if not action:
            return

        action = action.upper().strip()

        if action == 'D':
            confirm = await self.confirm_action("Delete this mail?")
            if confirm:
                await self.mail_service.delete_mail(mail.mail_id, self.user_id)
                await self.send_line("\r\nMail deleted.")
        elif action == 'R':
            await self.mail_reply(mail)

    async def mail_reply(self, original_mail):
        """Reply to a mail"""
        await self.send_line("\r\n--- Reply ---")

        # Subject
        reply_subject = f"Re: {original_mail.subject}"
        if len(reply_subject) > 100:
            reply_subject = reply_subject[:100]

        await self.send_line(f"Subject: {reply_subject}")

        # Body
        await self.send_line("\r\nEnter message body (end with '.' on a line by itself):")

        body_lines = []
        while True:
            line = await self.receive_line()
            if line == ".":
                break
            body_lines.append(line)

        body = "\n".join(body_lines)

        if not body.strip():
            await self.send_line("\r\nEmpty message. Mail not sent.")
            return

        # Sanitize
        body = sanitize_message_body(body)
        if detect_xss(body) or detect_sql_injection(body):
            await self.send_line("\r\nInvalid characters detected in message.")
            return

        # Send mail
        from app.models.mail import MailCreate

        mail_data = MailCreate(
            sender_id=self.user_id,
            sender_handle=self.handle_name,
            recipient_id=original_mail.sender_id,
            subject=reply_subject,
            body=body
        )

        try:
            await self.mail_service.send_mail(mail_data)
            await self.send_line("\r\nReply sent successfully.")
        except Exception as e:
            await self.send_line(f"\r\nFailed to send reply: {e}")

    async def mail_send(self):
        """Send a new mail"""
        await self.send_line("\r\n--- Send Mail ---")

        # Select recipient
        users = await self.mail_service.get_all_users_for_mail()

        if not users:
            await self.send_line("\r\nNo users available.")
            return

        await self.send_line("\r\nAvailable users:")
        for idx, (user_id, handle_name) in enumerate(users, 1):
            await self.send_line(f"{idx}. {user_id} ({handle_name})")

        await self.send("")
        await self.send("Select recipient number (or Q to cancel): ")

        selection = await self.receive_line()
        if not selection or selection.upper() == 'Q':
            return

        try:
            user_num = int(selection)
            if 1 <= user_num <= len(users):
                recipient_id, recipient_handle = users[user_num - 1]
            else:
                await self.send_line("\r\nInvalid user number.")
                return
        except ValueError:
            await self.send_line("\r\nInvalid input.")
            return

        # Subject
        await self.send("Subject: ")
        subject = await self.receive_line()

        if not subject or not subject.strip():
            await self.send_line("\r\nSubject cannot be empty.")
            return

        subject = sanitize_title(subject)

        # Body
        await self.send_line("\r\nEnter message body (end with '.' on a line by itself):")

        body_lines = []
        while True:
            line = await self.receive_line()
            if line == ".":
                break
            body_lines.append(line)

        body = "\n".join(body_lines)

        if not body.strip():
            await self.send_line("\r\nEmpty message. Mail not sent.")
            return

        # Sanitize
        body = sanitize_message_body(body)
        if detect_xss(body) or detect_sql_injection(body):
            await self.send_line("\r\nInvalid characters detected in message.")
            return

        # Confirm
        await self.send_line(f"\r\nTo: {recipient_handle} ({recipient_id})")
        await self.send_line(f"Subject: {subject}")

        confirm = await self.confirm_action("Send this mail?")
        if not confirm:
            await self.send_line("\r\nMail cancelled.")
            return

        # Send mail
        from app.models.mail import MailCreate

        mail_data = MailCreate(
            sender_id=self.user_id,
            sender_handle=self.handle_name,
            recipient_id=recipient_id,
            subject=subject,
            body=body
        )

        try:
            await self.mail_service.send_mail(mail_data)
            await self.send_line("\r\nMail sent successfully.")
        except Exception as e:
            await self.send_line(f"\r\nFailed to send mail: {e}")

    async def mail_sent_box(self):
        """View sent mail"""
        mails = await self.mail_service.get_sent_mail(self.user_id)

        if not mails:
            await self.send_line("\r\nNo sent mail.")
            return

        # Display mail list
        await self.send_line("\r\n" + "=" * 70)
        await self.send_line("Sent Mail")
        await self.send_line("=" * 70)
        await self.send_line(f"{'#':<4} {'To':<15} {'Subject':<35} {'Date':<15}")
        await self.send_line("-" * 70)

        for idx, mail in enumerate(mails, 1):
            subject = mail.subject[:33] + ".." if len(mail.subject) > 35 else mail.subject
            date_str = mail.sent_at.strftime("%Y-%m-%d %H:%M")
            await self.send_line(
                f"{idx:<4} {mail.recipient_id:<15} {subject:<35} {date_str:<15}"
            )

        # Select mail to view
        await self.send_line("")
        await self.send("View mail number (or Q to quit): ")

        selection = await self.receive_line()
        if not selection or selection.upper() == 'Q':
            return

        try:
            mail_num = int(selection)
            if 1 <= mail_num <= len(mails):
                mail = mails[mail_num - 1]

                # Display mail
                await self.send_line("\r\n" + "=" * 70)
                await self.send_line(f"To: {mail.recipient_id}")
                await self.send_line(f"Date: {mail.sent_at.strftime('%Y-%m-%d %H:%M:%S')}")
                await self.send_line(f"Subject: {mail.subject}")
                await self.send_line(f"Status: {'Read' if mail.is_read else 'Unread'}")
                await self.send_line("=" * 70)
                await self.send_line(mail.body)
                await self.send_line("=" * 70)

                # Actions
                await self.send_line("")
                await self.send_line("D) Delete  Q) Back")
                await self.send("Action: ")

                action = await self.receive_line()
                if action and action.upper() == 'D':
                    confirm = await self.confirm_action("Delete this mail?")
                    if confirm:
                        await self.mail_service.delete_mail(mail.mail_id, self.user_id)
                        await self.send_line("\r\nMail deleted.")
            else:
                await self.send_line("\r\nInvalid mail number.")
        except ValueError:
            await self.send_line("\r\nInvalid input.")

    async def confirm_action(self, message: str) -> bool:
        """Ask for confirmation"""
        await self.send(f"\r\n{message} (Y/N): ")
        response = await self.receive_line()
        return response and response.upper() == 'Y'

    async def apply_user(self):
        """User registration"""
        if self.user_id != "guest":
            await self.send_line("\r\nYou are already registered.")
            return

        await self.send_line("\r\n" + "=" * 70)
        await self.send_line("User Registration")
        await self.send_line("=" * 70)
        await self.send_line("\r\nPlease enter your information:")

        # User ID
        while True:
            await self.send("\r\nUser ID (4-8 alphanumeric characters): ")
            user_id = await self.receive_line()

            if not user_id:
                await self.send_line("\r\nRegistration cancelled.")
                return

            # Sanitize user ID
            user_id = sanitize_user_id(user_id)

            # Validate length
            if len(user_id) < 4 or len(user_id) > 8:
                await self.send_line("\r\nUser ID must be 4-8 characters.")
                continue

            # Check if alphanumeric only
            if not user_id.replace("-", "").replace("_", "").isalnum():
                await self.send_line("\r\nUser ID must contain only alphanumeric characters, hyphens, and underscores.")
                continue

            # Check availability
            available = await self.user_service.is_user_id_available(user_id)
            if not available:
                await self.send_line(f"\r\nUser ID '{user_id}' is already taken. Please choose another.")
                continue

            break

        # Handle name
        await self.send("\r\nHandle Name (display name): ")
        handle_name = await self.receive_line()

        if not handle_name or not handle_name.strip():
            await self.send_line("\r\nHandle name cannot be empty.")
            await self.send_line("\r\nRegistration cancelled.")
            return

        handle_name = sanitize_text(handle_name, max_length=50)

        # Password
        while True:
            await self.send("\r\nPassword (min 4 characters): ")
            password = await self.receive_line(echo=False)

            if not password or len(password) < 4:
                await self.send_line("\r\nPassword must be at least 4 characters.")
                continue

            await self.send("\r\nConfirm Password: ")
            password_confirm = await self.receive_line(echo=False)

            if password != password_confirm:
                await self.send_line("\r\nPasswords do not match. Please try again.")
                continue

            break

        # Email (optional)
        await self.send("\r\nEmail (optional, press Enter to skip): ")
        email = await self.receive_line()

        if email and email.strip():
            from app.utils.input_sanitizer import validate_email
            if not validate_email(email):
                await self.send_line("\r\nInvalid email format. Proceeding without email.")
                email = None
            else:
                email = email.strip()
        else:
            email = None

        # Confirmation
        await self.send_line("\r\n" + "-" * 70)
        await self.send_line("Registration Summary:")
        await self.send_line(f"  User ID: {user_id}")
        await self.send_line(f"  Handle Name: {handle_name}")
        await self.send_line(f"  Email: {email if email else '(not provided)'}")
        await self.send_line("-" * 70)

        confirm = await self.confirm_action("Register with this information?")
        if not confirm:
            await self.send_line("\r\nRegistration cancelled.")
            return

        # Create user
        try:
            user = await self.user_service.create_user(
                user_id=user_id,
                password=password,
                handle_name=handle_name,
                email=email,
                level=1,  # Default user level
                is_active=True
            )

            await self.send_line("\r\n" + "=" * 70)
            await self.send_line("Registration Successful!")
            await self.send_line("=" * 70)
            await self.send_line(f"\r\nWelcome, {handle_name}!")
            await self.send_line(f"Your user ID is: {user_id}")
            await self.send_line("\r\nYou can now login with your new credentials.")
            await self.send_line("Please logout and login again.")

            logger.info(f"New user registered: {user_id} ({handle_name})")

        except Exception as e:
            logger.error(f"User registration failed: {e}", exc_info=True)
            await self.send_line(f"\r\nRegistration failed: {str(e)}")
            await self.send_line("Please try again or contact the administrator.")

    async def install(self):
        """Install menu - User settings"""
        if not self.authenticated or self.user_id == "guest":
            await self.send_line("\r\nGuest users cannot access settings.")
            return

        while True:
            # Show install menu
            await self.send_line("\r\n" + "=" * 70)
            await self.send_line(f"Install Menu - Settings for {self.handle_name}")
            await self.send_line("=" * 70)
            await self.send_line("")
            await self.send_line("P) Change Password")
            await self.send_line("H) Change Handle Name")
            await self.send_line("M) Edit Memo (Profile)")
            await self.send_line("E) Change Email")
            await self.send_line("Q) Quit")
            await self.send_line("")
            await self.send("Command: ")

            command = await self.receive_line()
            if not command:
                continue

            command = command.upper().strip()

            if command == 'P':
                await self.change_password()
            elif command == 'H':
                await self.change_handle()
            elif command == 'M':
                await self.edit_memo()
            elif command == 'E':
                await self.change_email()
            elif command == 'Q':
                break
            else:
                await self.send_line("\r\nInvalid command.")

    async def change_password(self):
        """Change password"""
        await self.send_line("\r\n--- Change Password ---")

        # Current password verification
        await self.send("\r\nCurrent Password: ")
        current_password = await self.receive_line(echo=False)

        user = await self.user_service.authenticate(self.user_id, current_password)
        if not user:
            await self.send_line("\r\nIncorrect password.")
            return

        # New password
        while True:
            await self.send("\r\nNew Password (min 4 characters): ")
            new_password = await self.receive_line(echo=False)

            if not new_password or len(new_password) < 4:
                await self.send_line("\r\nPassword must be at least 4 characters.")
                continue

            await self.send("\r\nConfirm New Password: ")
            confirm_password = await self.receive_line(echo=False)

            if new_password != confirm_password:
                await self.send_line("\r\nPasswords do not match. Please try again.")
                continue

            break

        # Update password
        try:
            hashed = self.user_service.hash_password(new_password)
            await self.user_service.update_user(self.user_id, password_hash=hashed)
            await self.send_line("\r\nPassword changed successfully.")
            logger.info(f"Password changed for user: {self.user_id}")
        except Exception as e:
            logger.error(f"Password change failed: {e}", exc_info=True)
            await self.send_line("\r\nFailed to change password.")

    async def change_handle(self):
        """Change handle name"""
        await self.send_line("\r\n--- Change Handle Name ---")
        await self.send_line(f"Current handle: {self.handle_name}")

        await self.send("\r\nNew Handle Name: ")
        new_handle = await self.receive_line()

        if not new_handle or not new_handle.strip():
            await self.send_line("\r\nHandle name cannot be empty.")
            return

        new_handle = sanitize_text(new_handle, max_length=50)

        confirm = await self.confirm_action(f"Change handle to '{new_handle}'?")
        if not confirm:
            await self.send_line("\r\nCancelled.")
            return

        try:
            await self.user_service.update_user(self.user_id, handle_name=new_handle)
            self.handle_name = new_handle
            await self.send_line("\r\nHandle name changed successfully.")
            logger.info(f"Handle name changed for user: {self.user_id} -> {new_handle}")
        except Exception as e:
            logger.error(f"Handle name change failed: {e}", exc_info=True)
            await self.send_line("\r\nFailed to change handle name.")

    async def edit_memo(self):
        """Edit user memo (profile description)"""
        await self.send_line("\r\n--- Edit Profile Memo ---")

        # Get current memo
        user = await self.user_service.get_user(self.user_id)
        current_memo = user.memo if user and user.memo else ""

        if current_memo:
            await self.send_line("\r\nCurrent memo:")
            await self.send_line("-" * 70)
            await self.send_line(current_memo)
            await self.send_line("-" * 70)

        await self.send_line("\r\nEnter new memo (end with '.' on a line by itself):")
        await self.send_line("(Press Enter then '.' to clear memo)")

        memo_lines = []
        while True:
            line = await self.receive_line()
            if line == ".":
                break
            memo_lines.append(line)

        new_memo = "\n".join(memo_lines).strip()

        # Sanitize
        if new_memo:
            new_memo = sanitize_message_body(new_memo)
            if detect_xss(new_memo) or detect_sql_injection(new_memo):
                await self.send_line("\r\nInvalid characters detected in memo.")
                return

        confirm = await self.confirm_action("Save this memo?")
        if not confirm:
            await self.send_line("\r\nCancelled.")
            return

        try:
            await self.user_service.update_user(self.user_id, memo=new_memo if new_memo else None)
            await self.send_line("\r\nMemo updated successfully.")
            logger.info(f"Memo updated for user: {self.user_id}")
        except Exception as e:
            logger.error(f"Memo update failed: {e}", exc_info=True)
            await self.send_line("\r\nFailed to update memo.")

    async def change_email(self):
        """Change email address"""
        await self.send_line("\r\n--- Change Email Address ---")

        # Get current email
        user = await self.user_service.get_user(self.user_id)
        current_email = user.email if user and user.email else "(not set)"
        await self.send_line(f"Current email: {current_email}")

        await self.send("\r\nNew Email (or press Enter to remove): ")
        new_email = await self.receive_line()

        if new_email and new_email.strip():
            from app.utils.input_sanitizer import validate_email
            if not validate_email(new_email):
                await self.send_line("\r\nInvalid email format.")
                return
            new_email = new_email.strip()
        else:
            new_email = None

        confirm = await self.confirm_action(f"Change email to '{new_email if new_email else '(none)'}'?")
        if not confirm:
            await self.send_line("\r\nCancelled.")
            return

        try:
            await self.user_service.update_user(self.user_id, email=new_email)
            await self.send_line("\r\nEmail updated successfully.")
            logger.info(f"Email updated for user: {self.user_id}")
        except Exception as e:
            logger.error(f"Email update failed: {e}", exc_info=True)
            await self.send_line("\r\nFailed to update email.")

    async def profile(self):
        """View user profile"""
        await self.send_line("\r\n" + "=" * 70)
        await self.send_line("User Profile")
        await self.send_line("=" * 70)

        # Get user info
        user = await self.user_service.get_user(self.user_id)

        if not user:
            await self.send_line("\r\nUser not found.")
            return

        # Display profile
        await self.send_line(f"\r\nUser ID: {user.user_id}")
        await self.send_line(f"Handle Name: {user.handle_name}")
        await self.send_line(f"Level: {user.level}")
        await self.send_line(f"Email: {user.email if user.email else '(not set)'}")
        await self.send_line(f"Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if user.last_login:
            await self.send_line(f"Last Login: {user.last_login.strftime('%Y-%m-%d %H:%M:%S')}")

        if user.memo:
            await self.send_line("\r\nProfile Memo:")
            await self.send_line("-" * 70)
            await self.send_line(user.memo)
            await self.send_line("-" * 70)

        await self.send_line("\r\nPress Enter to continue...")
        await self.receive_line()

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
        """Show who's online"""
        await self.send_line("\r\n" + "=" * 70)
        await self.send_line("Online Users")
        await self.send_line("=" * 70)

        if not self.server:
            await self.send_line("\r\nServer information not available.")
            return

        # Get connection info from server
        connections = self.server.get_connection_info()

        if not connections:
            await self.send_line("\r\nNo users online.")
            return

        await self.send_line(f"\r\n{'Handle':<20} {'User ID':<10} {'Connected At':<20} {'Status'}")
        await self.send_line("-" * 70)

        for conn in connections:
            handle = conn.get('handle', 'Unknown')
            user_id = conn.get('user_id', 'guest')
            connected_at = conn.get('connected_at', '')

            # Format connected time
            if connected_at:
                try:
                    from datetime import datetime
                    conn_time = datetime.fromisoformat(connected_at)
                    time_str = conn_time.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = "Unknown"
            else:
                time_str = "Unknown"

            # Mark current user
            status = "(You)" if conn.get('client_id') == self.client_id else ""

            await self.send_line(f"{handle:<20} {user_id:<10} {time_str:<20} {status}")

        await self.send_line("-" * 70)
        await self.send_line(f"Total: {len(connections)} user(s) online")

        await self.send_line("\r\nPress Enter to continue...")
        await self.receive_line()

    async def sysop_menu(self):
        """SYSOP menu - System administration"""
        if self.user_level < 9:
            await self.send_line("\r\nAccess denied. SYSOP privileges required.")
            return

        while True:
            # Show SYSOP menu
            await self.send_line("\r\n" + "=" * 70)
            await self.send_line("SYSOP Menu - System Administration")
            await self.send_line("=" * 70)
            await self.send_line("")
            await self.send_line("U) User Management")
            await self.send_line("L) Change User Level")
            await self.send_line("B) Board Management")
            await self.send_line("S) System Statistics")
            await self.send_line("K) Kick User")
            await self.send_line("Q) Quit")
            await self.send_line("")
            await self.send("Command: ")

            command = await self.receive_line()
            if not command:
                continue

            command = command.upper().strip()

            try:
                if command == 'U':
                    await self.sysop_user_management()
                elif command == 'L':
                    await self.sysop_change_level()
                elif command == 'B':
                    await self.sysop_board_management()
                elif command == 'S':
                    await self.sysop_statistics()
                elif command == 'K':
                    await self.sysop_kick_user()
                elif command == 'Q':
                    break
                else:
                    await self.send_line("\r\nInvalid command.")
            except Exception as e:
                logger.error(f"SYSOP command error: {e}", exc_info=True)
                await self.send_line(f"\r\nError: {str(e)}")

    async def sysop_user_management(self):
        """SYSOP: User management - list all users with details"""
        await self.send_line("\r\n" + "=" * 70)
        await self.send_line("User Management")
        await self.send_line("=" * 70)

        users = await self.user_service.get_users(limit=1000)

        if not users:
            await self.send_line("\r\nNo users found.")
            return

        await self.send_line(f"\r\n{'User ID':<10} {'Handle':<20} {'Level':<6} {'Email':<25} {'Active':<6} {'Last Login'}")
        await self.send_line("-" * 70)

        for user in users:
            last_login = user.last_login.strftime("%Y-%m-%d") if user.last_login else "Never"
            active_status = "Yes" if user.is_active else "No"
            email = user.email[:23] + ".." if user.email and len(user.email) > 25 else (user.email or "")

            await self.send_line(
                f"{user.user_id:<10} {user.handle_name:<20} {user.level:<6} {email:<25} {active_status:<6} {last_login}"
            )

        await self.send_line("-" * 70)
        await self.send_line(f"Total: {len(users)} user(s)")

        await self.send_line("\r\nPress Enter to continue...")
        await self.receive_line()

    async def sysop_change_level(self):
        """SYSOP: Change user level"""
        await self.send_line("\r\n--- Change User Level ---")

        await self.send("\r\nUser ID: ")
        target_user_id = await self.receive_line()

        if not target_user_id:
            await self.send_line("\r\nCancelled.")
            return

        target_user_id = sanitize_user_id(target_user_id)

        # Get user
        user = await self.user_service.get_user(target_user_id)
        if not user:
            await self.send_line(f"\r\nUser '{target_user_id}' not found.")
            return

        await self.send_line(f"\r\nCurrent user: {user.handle_name} ({user.user_id})")
        await self.send_line(f"Current level: {user.level}")

        # Level guide
        await self.send_line("\r\nLevel Guide:")
        await self.send_line("  0 = Guest (read-only)")
        await self.send_line("  1-8 = Regular users")
        await self.send_line("  9 = SYSOP (full access)")

        await self.send("\r\nNew level (0-9): ")
        level_input = await self.receive_line()

        try:
            new_level = int(level_input)
            if new_level < 0 or new_level > 9:
                await self.send_line("\r\nLevel must be between 0 and 9.")
                return
        except ValueError:
            await self.send_line("\r\nInvalid level.")
            return

        # Confirm
        confirm = await self.confirm_action(f"Change {user.handle_name}'s level from {user.level} to {new_level}?")
        if not confirm:
            await self.send_line("\r\nCancelled.")
            return

        # Update level
        try:
            await self.user_service.update_user(target_user_id, level=new_level)
            await self.send_line(f"\r\nUser level changed successfully: {user.handle_name} -> Level {new_level}")
            logger.info(f"SYSOP {self.user_id} changed {target_user_id} level: {user.level} -> {new_level}")
        except Exception as e:
            logger.error(f"Failed to change user level: {e}", exc_info=True)
            await self.send_line("\r\nFailed to change user level.")

    async def sysop_board_management(self):
        """SYSOP: Board management - view and configure boards"""
        await self.send_line("\r\n" + "=" * 70)
        await self.send_line("Board Management")
        await self.send_line("=" * 70)

        boards = await self.board_service.get_boards()

        if not boards:
            await self.send_line("\r\nNo boards found.")
            return

        await self.send_line(f"\r\n{'ID':<4} {'Name':<30} {'Read Lv':<8} {'Write Lv':<9} {'Enforced'}")
        await self.send_line("-" * 70)

        for board in boards:
            enforced = "Yes" if board.is_enforced_news else "No"
            await self.send_line(
                f"{board.board_id:<4} {board.name:<30} {board.read_level:<8} {board.write_level:<9} {enforced}"
            )

        await self.send_line("-" * 70)
        await self.send_line(f"Total: {len(boards)} board(s)")

        # Edit option
        await self.send_line("\r\nE) Edit board settings  Q) Back")
        await self.send("Command: ")

        command = await self.receive_line()
        if command and command.upper() == 'E':
            await self.sysop_edit_board()

    async def sysop_edit_board(self):
        """SYSOP: Edit board settings"""
        await self.send("\r\nBoard ID to edit: ")
        board_id_input = await self.receive_line()

        try:
            board_id = int(board_id_input)
        except ValueError:
            await self.send_line("\r\nInvalid board ID.")
            return

        # Get board
        board = await self.board_service.get_board_by_id(board_id)
        if not board:
            await self.send_line(f"\r\nBoard {board_id} not found.")
            return

        await self.send_line(f"\r\nEditing: {board.name}")
        await self.send_line(f"Current settings:")
        await self.send_line(f"  Read Level: {board.read_level}")
        await self.send_line(f"  Write Level: {board.write_level}")
        await self.send_line(f"  Enforced News: {'Yes' if board.is_enforced_news else 'No'}")

        # Edit menu
        await self.send_line("\r\nWhat to change?")
        await self.send_line("R) Read Level  W) Write Level  E) Enforced News  Q) Cancel")
        await self.send("Command: ")

        command = await self.receive_line()
        if not command:
            return

        command = command.upper().strip()

        try:
            if command == 'R':
                await self.send("New read level (0-9): ")
                level = int(await self.receive_line())
                if 0 <= level <= 9:
                    await self.board_service.update_board(board_id, read_level=level)
                    await self.send_line(f"\r\nRead level updated to {level}")
                    logger.info(f"SYSOP {self.user_id} changed board {board_id} read level to {level}")
                else:
                    await self.send_line("\r\nLevel must be 0-9.")

            elif command == 'W':
                await self.send("New write level (0-9): ")
                level = int(await self.receive_line())
                if 0 <= level <= 9:
                    await self.board_service.update_board(board_id, write_level=level)
                    await self.send_line(f"\r\nWrite level updated to {level}")
                    logger.info(f"SYSOP {self.user_id} changed board {board_id} write level to {level}")
                else:
                    await self.send_line("\r\nLevel must be 0-9.")

            elif command == 'E':
                await self.send("Enforced news? (Y/N): ")
                choice = await self.receive_line()
                enforced = choice.upper() == 'Y'
                await self.board_service.update_board(board_id, enforced_news=enforced)
                await self.send_line(f"\r\nEnforced news set to {'Yes' if enforced else 'No'}")
                logger.info(f"SYSOP {self.user_id} changed board {board_id} enforced news to {enforced}")

        except ValueError:
            await self.send_line("\r\nInvalid input.")
        except Exception as e:
            logger.error(f"Failed to update board settings: {e}", exc_info=True)
            await self.send_line("\r\nFailed to update board settings.")

    async def sysop_statistics(self):
        """SYSOP: System statistics"""
        await self.send_line("\r\n" + "=" * 70)
        await self.send_line("System Statistics")
        await self.send_line("=" * 70)

        # User statistics
        total_users = len(await self.user_service.get_users(limit=10000))
        await self.send_line(f"\r\nTotal Users: {total_users}")

        # Online users
        if self.server:
            online_count = self.server.get_active_connections()
            await self.send_line(f"Online Users: {online_count}")

        # Board statistics
        boards = await self.board_service.get_boards()
        await self.send_line(f"Total Boards: {len(boards)}")

        # Mail statistics (if accessible)
        try:
            unread_count = await self.mail_service.get_unread_count(self.user_id)
            await self.send_line(f"Your Unread Mail: {unread_count}")
        except:
            pass

        # System health
        if self.server:
            try:
                health = await self.server.get_health_status()
                db_healthy = health.get('database', {}).get('healthy', False)
                disk_free = health.get('disk_space', {}).get('free_gb', 'N/A')
                await self.send_line(f"\r\nSystem Health:")
                await self.send_line(f"  Database: {'OK' if db_healthy else 'WARNING'}")
                await self.send_line(f"  Disk Free: {disk_free} GB")
            except:
                pass

        await self.send_line("\r\nPress Enter to continue...")
        await self.receive_line()

    async def sysop_kick_user(self):
        """SYSOP: Kick a user (disconnect)"""
        await self.send_line("\r\n--- Kick User ---")

        if not self.server:
            await self.send_line("\r\nServer information not available.")
            return

        # Show online users
        connections = self.server.get_connection_info()

        if not connections:
            await self.send_line("\r\nNo users online.")
            return

        await self.send_line("\r\nOnline users:")
        for idx, conn in enumerate(connections, 1):
            handle = conn.get('handle', 'Unknown')
            user_id = conn.get('user_id', 'guest')
            await self.send_line(f"{idx}. {handle} ({user_id})")

        await self.send("\r\nSelect user number to kick (or Q to cancel): ")
        selection = await self.receive_line()

        if not selection or selection.upper() == 'Q':
            return

        try:
            user_num = int(selection)
            if 1 <= user_num <= len(connections):
                target_conn = connections[user_num - 1]
                target_client_id = target_conn.get('client_id')
                target_user_id = target_conn.get('user_id', 'unknown')

                # Don't kick yourself
                if target_client_id == self.client_id:
                    await self.send_line("\r\nYou cannot kick yourself.")
                    return

                confirm = await self.confirm_action(f"Kick user {target_conn.get('handle')}?")
                if confirm:
                    # Find and disconnect the handler
                    if target_client_id in self.server.handlers:
                        handler = self.server.handlers[target_client_id]
                        await handler.send_line("\r\n\r\nYou have been disconnected by SYSOP.")
                        await handler.disconnect()
                        await self.send_line(f"\r\nUser kicked: {target_conn.get('handle')}")
                        logger.warning(f"SYSOP {self.user_id} kicked user {target_user_id}")
                    else:
                        await self.send_line("\r\nUser connection not found.")
            else:
                await self.send_line("\r\nInvalid user number.")
        except ValueError:
            await self.send_line("\r\nInvalid input.")

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

    async def chat(self):
        """Chat room"""
        if not self.server:
            await self.send_line("Chat is not available.")
            return

        # Show chat room opening message
        msg = await self.message_service.get_message_content("CHAT_ROOM_OPENING")
        await self.send(msg)

        # Join chat room
        self.server.join_chat(self.client_id, self)

        # Announce join to other users
        join_msg = f"\r\n>>> {self.handle_name} さんが入室しました\r\n"
        await self.server.broadcast_chat(join_msg, exclude_client_id=self.client_id)

        await self.send_line("メッセージを入力してください。終了は // または ^^ です。")
        await self.send_line("")

        try:
            while True:
                # Show prompt
                await self.send(f"{self.handle_name}> ")

                # Receive message
                msg_text = await self.receive_line()

                # Check exit commands
                if msg_text in ["//", "^^"]:
                    break

                # Empty message
                if not msg_text:
                    continue

                # Broadcast message to all users in chat (excluding self)
                chat_msg = f"\r\n{self.handle_name}> {msg_text}\r\n"
                await self.server.broadcast_chat(chat_msg, exclude_client_id=self.client_id)

        except Exception as e:
            logger.error(f"Chat error: {e}")
        finally:
            # Leave chat room
            self.server.leave_chat(self.client_id)

            # Announce leave to other users
            leave_msg = f"\r\n<<< {self.handle_name} さんが退室しました\r\n"
            await self.server.broadcast_chat(leave_msg)

            await self.send_line("\r\nチャットルームを退出しました。")

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
