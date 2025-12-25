"""
Telnet Server Implementation
"""
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
from app.protocols.telnet_handler import TelnetHandler
from app.core.config import settings
from app.utils.monitor import (
    initialize_monitor,
    get_monitor,
    periodic_health_check_task,
    periodic_metrics_collection_task
)

logger = logging.getLogger(__name__)


class TelnetServer:
    """Async Telnet Server for BBS"""

    def __init__(self, host: str = "0.0.0.0", port: int = 23):
        self.host = host
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self.handlers: Dict[str, TelnetHandler] = {}
        self.connection_count = 0
        self.max_connections = settings.TELNET_MAX_CONNECTIONS
        self.chat_users: Dict[str, TelnetHandler] = {}  # Users in chat room
        self.monitor_tasks: list[asyncio.Task] = []  # Background monitoring tasks

        # Initialize monitor
        try:
            import os
            db_path = os.path.join(os.getcwd(), "data", "mtbbs.db")
            data_dir = os.path.join(os.getcwd(), "data")
            initialize_monitor(db_path, data_dir)
            logger.info("System monitor initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize monitor: {e}")

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Handle new client connection"""
        addr = writer.get_extra_info("peername")
        client_id = f"{addr[0]}:{addr[1]}"

        # Check max connections
        if len(self.handlers) >= self.max_connections:
            logger.warning(f"Max connections reached, rejecting {client_id}")
            await self._send_and_close(writer, "Server full. Please try again later.\r\n")
            return

        logger.info(f"New Telnet connection from {client_id}")
        self.connection_count += 1

        handler = TelnetHandler(reader, writer, client_id, server=self)
        self.handlers[client_id] = handler

        # Register session with monitor
        try:
            monitor = get_monitor()
            monitor.register_session(client_id, user_id=None, state="connected")
        except Exception as e:
            logger.warning(f"Failed to register session with monitor: {e}")

        try:
            await handler.handle()
        except Exception as e:
            logger.error(f"Error handling {client_id}: {e}", exc_info=True)
        finally:
            # Unregister session from monitor
            try:
                monitor = get_monitor()
                monitor.unregister_session(client_id)
            except Exception as e:
                logger.warning(f"Failed to unregister session from monitor: {e}")

            if client_id in self.handlers:
                del self.handlers[client_id]

            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

            logger.info(f"Telnet disconnected: {client_id} (Total: {self.connection_count})")

    async def _send_and_close(self, writer: asyncio.StreamWriter, message: str):
        """Send message and close connection"""
        try:
            writer.write(message.encode("utf-8"))
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    async def start(self):
        """Start Telnet server"""
        try:
            self.server = await asyncio.start_server(
                self.handle_client, self.host, self.port
            )

            addr = self.server.sockets[0].getsockname()
            logger.info(f"Telnet server started on {addr[0]}:{addr[1]}")

            # Start monitoring background tasks
            try:
                health_check_task = asyncio.create_task(
                    periodic_health_check_task(interval=300)  # Every 5 minutes
                )
                metrics_task = asyncio.create_task(
                    periodic_metrics_collection_task(interval=600)  # Every 10 minutes
                )
                self.monitor_tasks.extend([health_check_task, metrics_task])
                logger.info("Monitoring background tasks started")
            except Exception as e:
                logger.warning(f"Failed to start monitoring tasks: {e}")

            async with self.server:
                await self.server.serve_forever()
        except Exception as e:
            logger.error(f"Failed to start Telnet server: {e}", exc_info=True)
            raise

    async def stop(self):
        """Stop Telnet server"""
        if self.server:
            logger.info("Stopping Telnet server...")

            # Cancel monitoring tasks
            for task in self.monitor_tasks:
                task.cancel()

            if self.monitor_tasks:
                await asyncio.gather(*self.monitor_tasks, return_exceptions=True)
                logger.info("Monitoring background tasks stopped")

            # Close all active connections
            for handler in list(self.handlers.values()):
                try:
                    await handler.disconnect()
                except Exception:
                    pass

            self.server.close()
            await self.server.wait_closed()
            logger.info("Telnet server stopped")

    def get_active_connections(self) -> int:
        """Get number of active connections"""
        return len(self.handlers)

    def get_connection_info(self) -> list:
        """Get information about active connections"""
        return [
            {
                "client_id": client_id,
                "user_id": handler.user_id,
                "handle": handler.handle_name,
                "connected_at": handler.connected_at.isoformat() if handler.connected_at else None,
            }
            for client_id, handler in self.handlers.items()
        ]

    async def broadcast_chat(self, message: str, exclude_client_id: Optional[str] = None):
        """Broadcast chat message to all users in chat room"""
        for client_id, handler in list(self.chat_users.items()):
            if exclude_client_id and client_id == exclude_client_id:
                continue
            try:
                await handler.send(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")

    def join_chat(self, client_id: str, handler: TelnetHandler):
        """Add user to chat room"""
        self.chat_users[client_id] = handler
        logger.info(f"User {handler.handle_name} joined chat room")

    def leave_chat(self, client_id: str):
        """Remove user from chat room"""
        if client_id in self.chat_users:
            handler = self.chat_users[client_id]
            del self.chat_users[client_id]
            logger.info(f"User {handler.handle_name} left chat room")

    def get_chat_users(self) -> list:
        """Get list of users in chat room"""
        return [
            {
                "user_id": handler.user_id,
                "handle": handler.handle_name,
            }
            for handler in self.chat_users.values()
        ]

    async def get_health_status(self) -> dict:
        """Get system health status"""
        try:
            monitor = get_monitor()
            return await monitor.check_health()
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }

    def update_session_login(self, client_id: str, user_id: str):
        """Update session state after user login"""
        try:
            monitor = get_monitor()
            monitor.update_session_state(client_id, user_id=user_id, state="logged_in")
        except Exception as e:
            logger.warning(f"Failed to update session login state: {e}")
