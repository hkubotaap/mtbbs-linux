"""
Telnet Server Implementation
"""
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
from app.protocols.telnet_handler import TelnetHandler
from app.core.config import settings

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

        handler = TelnetHandler(reader, writer, client_id)
        self.handlers[client_id] = handler

        try:
            await handler.handle()
        except Exception as e:
            logger.error(f"Error handling {client_id}: {e}", exc_info=True)
        finally:
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

            async with self.server:
                await self.server.serve_forever()
        except Exception as e:
            logger.error(f"Failed to start Telnet server: {e}", exc_info=True)
            raise

    async def stop(self):
        """Stop Telnet server"""
        if self.server:
            logger.info("Stopping Telnet server...")

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
