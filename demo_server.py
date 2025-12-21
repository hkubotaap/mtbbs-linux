"""
MTBBS Linux - Simple Demo Server
Telnet BBS Server without database for quick testing
"""
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 接続情報ファイル
CONNECTIONS_FILE = "telnet_connections.json"

# In-memory storage
users_db = {
    "admin": {"password": "admin123", "handle": "Administrator", "level": 9},
    "test": {"password": "test123", "handle": "TestUser", "level": 1},
}

boards_db = {
    1: {"name": "General", "messages": []},
    2: {"name": "Announcements", "messages": []},
}

active_connections: Dict[str, "TelnetHandler"] = {}


def save_connections_info():
    """現在の接続情報をJSONファイルに保存"""
    connections_list = []
    for client_id, handler in active_connections.items():
        connections_list.append({
            "client_id": client_id,
            "user_id": handler.user_id or "not_logged_in",
            "handle_name": handler.handle_name,
            "level": handler.level,
            "authenticated": handler.authenticated,
            "connected_at": datetime.now().isoformat()
        })

    data = {
        "connections": connections_list,
        "last_updated": datetime.now().isoformat()
    }

    try:
        with open(CONNECTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save connections info: {e}")


class TelnetHandler:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, client_id: str):
        self.reader = reader
        self.writer = writer
        self.client_id = client_id
        self.user_id: Optional[str] = None
        self.handle_name: str = "Guest"
        self.level: int = 0
        self.authenticated = False

    async def send(self, text: str):
        try:
            self.writer.write(text.encode("utf-8"))
            await self.writer.drain()
        except:
            pass

    async def send_line(self, text: str = ""):
        await self.send(text + "\r\n")

    async def receive_line(self) -> str:
        line = ""
        try:
            while True:
                data = await self.reader.read(1)
                if not data:
                    raise ConnectionError()

                char = data.decode("utf-8", errors="ignore")

                if char == "\r" or char == "\n":
                    if line:
                        await self.send("\r\n")
                        return line
                elif char == "\x08" or char == "\x7f":
                    if line:
                        line = line[:-1]
                        await self.send("\x08 \x08")
                elif char >= " ":
                    line += char
                    await self.send(char)
        except:
            raise

    async def handle(self):
        try:
            await self.send_opening()
            await self.login()

            if self.authenticated:
                await self.main_loop()

        except Exception as e:
            logger.error(f"Handler error: {e}")
        finally:
            await self.disconnect()

    async def send_opening(self):
        msg = f"""

 KANJI CODE = [UTF-8]

今日は{datetime.now().strftime("%Y/%m/%d")} です。
---------------------------------------------------------
MTBBSへようこそ！
MTBBS Linux デモサーバー
---------------------------------------------------------

User ID: admin, test, または guest でログインしてください
"""
        await self.send(msg)

    async def login(self):
        for _ in range(3):
            await self.send_line("\r\nUser ID: ")
            user_id = await self.receive_line()

            if user_id.lower() == "guest":
                self.user_id = "guest"
                self.handle_name = "Guest"
                self.authenticated = True
                await self.send_line(f"\r\n{self.handle_name}さん、ようこそ！\r\n")
                save_connections_info()
                return

            await self.send_line("Password: ")
            password = await self.receive_line()

            if user_id in users_db and users_db[user_id]["password"] == password:
                self.user_id = user_id
                self.handle_name = users_db[user_id]["handle"]
                self.level = users_db[user_id]["level"]
                self.authenticated = True
                await self.send_line(f"\r\n{self.handle_name}さん、ようこそ！\r\n")
                save_connections_info()
                return
            else:
                await self.send_line("\r\nInvalid credentials.")

    async def main_loop(self):
        while True:
            await self.show_menu()
            await self.send_line("\r\nCommand: ")
            cmd = await self.receive_line()

            if not cmd:
                continue

            cmd = cmd.upper().strip()

            try:
                if cmd == "Q":
                    await self.send_line("\r\nさようなら！\r\n")
                    break
                elif cmd == "R":
                    await self.read_board()
                elif cmd == "E":
                    await self.enter_message()
                elif cmd == "W":
                    await self.who_online()
                elif cmd == "H" or cmd == "?":
                    await self.show_help()
                elif cmd == "#":
                    await self.show_status()
                else:
                    await self.send_line("Unknown command. Type H for help.")
            except Exception as e:
                logger.error(f"Command error: {e}")
                await self.send_line(f"Error: {str(e)}")

    async def show_menu(self):
        menu = f"""
MTBBS Demo - Main Menu   {datetime.now().strftime("%H:%M")}  {self.user_id} / {self.handle_name}
BOARD/MAIL -------------  INFORMATION ------------  OTHERS -----------------
[R]ead  メッセージを読む| [H]elp    ヘルプ        | [Q]uit    ログアウト
[E]nter メッセージ書込  | [W]ho     ログイン中    | [#]       ステータス
"""
        await self.send(menu)

    async def read_board(self):
        await self.send_line("\r\n=== Boards ===")
        for board_id, board in boards_db.items():
            msg_count = len(board["messages"])
            await self.send_line(f"{board_id}. {board['name']} ({msg_count} messages)")

        await self.send_line("\r\nBoard number (0 to cancel): ")
        board_no = await self.receive_line()

        if not board_no or board_no == "0":
            return

        try:
            board_id = int(board_no)
            if board_id in boards_db:
                board = boards_db[board_id]
                await self.send_line(f"\r\n=== {board['name']} ===")

                if not board["messages"]:
                    await self.send_line("No messages yet.")
                else:
                    for idx, msg in enumerate(board["messages"], 1):
                        await self.send_line(
                            f"[{idx}] {msg['title']} - {msg['handle']} "
                            f"({msg['date'].strftime('%m/%d %H:%M')})"
                        )
        except ValueError:
            await self.send_line("Invalid board number.")

    async def enter_message(self):
        await self.send_line("\r\nBoard number: ")
        board_no = await self.receive_line()

        try:
            board_id = int(board_no)
            if board_id not in boards_db:
                await self.send_line("Invalid board.")
                return

            await self.send_line("Title: ")
            title = await self.receive_line()

            if not title:
                await self.send_line("Title required.")
                return

            await self.send_line("Body (end with . on a line): ")
            body_lines = []
            while True:
                line = await self.receive_line()
                if line == ".":
                    break
                body_lines.append(line)

            message = {
                "title": title,
                "body": "\n".join(body_lines),
                "handle": self.handle_name,
                "user_id": self.user_id,
                "date": datetime.now(),
            }

            boards_db[board_id]["messages"].append(message)
            await self.send_line(f"\r\nMessage posted to {boards_db[board_id]['name']}!")

        except ValueError:
            await self.send_line("Invalid board number.")

    async def who_online(self):
        await self.send_line("\r\n=== Online Users ===")
        count = 0
        for client_id, handler in active_connections.items():
            if handler.authenticated:
                await self.send_line(f"{handler.handle_name} ({handler.user_id})")
                count += 1
        await self.send_line(f"\r\nTotal: {count} users online")

    async def show_help(self):
        help_text = """
=== Help ===
[R] Read  - 掲示板を読む
[E] Enter - メッセージを投稿
[W] Who   - ログイン中のユーザー
[#] Status - ステータス表示
[H] Help  - このヘルプ
[Q] Quit  - ログアウト
"""
        await self.send(help_text)

    async def show_status(self):
        await self.send_line(f"\r\n=== Status ===")
        await self.send_line(f"User: {self.user_id}")
        await self.send_line(f"Handle: {self.handle_name}")
        await self.send_line(f"Level: {self.level}")
        await self.send_line(f"Connected: {self.client_id}")

    async def disconnect(self):
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except:
            pass


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info("peername")
    client_id = f"{addr[0]}:{addr[1]}"

    logger.info(f"New connection: {client_id}")

    handler = TelnetHandler(reader, writer, client_id)
    active_connections[client_id] = handler
    save_connections_info()

    try:
        await handler.handle()
    finally:
        if client_id in active_connections:
            del active_connections[client_id]
        save_connections_info()
        logger.info(f"Disconnected: {client_id}")


async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 2323)

    addr = server.sockets[0].getsockname()
    logger.info(f"MTBBS Demo Server started on {addr[0]}:{addr[1]}")
    logger.info("Connect with: telnet localhost 2323")
    logger.info("Logins: admin/admin123, test/test123, guest")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")
