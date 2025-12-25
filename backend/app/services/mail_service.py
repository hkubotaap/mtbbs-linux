"""
Mail Service
"""
import sqlite3
import logging
from typing import List, Optional
from datetime import datetime
from app.models.mail import Mail, MailCreate
from app.core.database import get_connection

logger = logging.getLogger(__name__)


class MailService:
    """Mail service for managing user mail"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def send_mail(self, mail_data: MailCreate) -> int:
        """
        Send a mail message

        Args:
            mail_data: Mail creation data

        Returns:
            mail_id of the created mail

        Raises:
            ValueError: If recipient doesn't exist
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if recipient exists
            cursor.execute(
                "SELECT user_id FROM users WHERE user_id = ?",
                (mail_data.recipient_id,)
            )
            if not cursor.fetchone():
                raise ValueError(f"Recipient '{mail_data.recipient_id}' not found")

            # Insert mail
            cursor.execute(
                """
                INSERT INTO mail (
                    sender_id, sender_handle, recipient_id,
                    subject, body, sent_at, is_read,
                    is_deleted_by_sender, is_deleted_by_recipient
                )
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0)
                """,
                (
                    mail_data.sender_id,
                    mail_data.sender_handle,
                    mail_data.recipient_id,
                    mail_data.subject,
                    mail_data.body,
                    datetime.now().isoformat()
                )
            )

            mail_id = cursor.lastrowid
            conn.commit()

            logger.info(f"Mail sent: {mail_data.sender_id} -> {mail_data.recipient_id}, mail_id={mail_id}")
            return mail_id

        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Failed to send mail: {e}")
            raise
        finally:
            conn.close()

    async def get_inbox(self, user_id: str, include_read: bool = True) -> List[Mail]:
        """
        Get inbox for a user

        Args:
            user_id: User ID
            include_read: Include already read messages

        Returns:
            List of mail messages
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        try:
            query = """
                SELECT mail_id, sender_id, sender_handle, recipient_id,
                       subject, body, sent_at, read_at, is_read,
                       is_deleted_by_sender, is_deleted_by_recipient
                FROM mail
                WHERE recipient_id = ? AND is_deleted_by_recipient = 0
            """
            params = [user_id]

            if not include_read:
                query += " AND is_read = 0"

            query += " ORDER BY sent_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            mails = []
            for row in rows:
                mail = Mail(
                    mail_id=row[0],
                    sender_id=row[1],
                    sender_handle=row[2],
                    recipient_id=row[3],
                    subject=row[4],
                    body=row[5],
                    sent_at=datetime.fromisoformat(row[6]),
                    read_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    is_read=bool(row[8]),
                    is_deleted_by_sender=bool(row[9]),
                    is_deleted_by_recipient=bool(row[10])
                )
                mails.append(mail)

            return mails

        except sqlite3.Error as e:
            logger.error(f"Failed to get inbox for {user_id}: {e}")
            raise
        finally:
            conn.close()

    async def get_sent_mail(self, user_id: str) -> List[Mail]:
        """
        Get sent mail for a user

        Args:
            user_id: User ID

        Returns:
            List of sent mail messages
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT mail_id, sender_id, sender_handle, recipient_id,
                       subject, body, sent_at, read_at, is_read,
                       is_deleted_by_sender, is_deleted_by_recipient
                FROM mail
                WHERE sender_id = ? AND is_deleted_by_sender = 0
                ORDER BY sent_at DESC
                """,
                (user_id,)
            )
            rows = cursor.fetchall()

            mails = []
            for row in rows:
                mail = Mail(
                    mail_id=row[0],
                    sender_id=row[1],
                    sender_handle=row[2],
                    recipient_id=row[3],
                    subject=row[4],
                    body=row[5],
                    sent_at=datetime.fromisoformat(row[6]),
                    read_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    is_read=bool(row[8]),
                    is_deleted_by_sender=bool(row[9]),
                    is_deleted_by_recipient=bool(row[10])
                )
                mails.append(mail)

            return mails

        except sqlite3.Error as e:
            logger.error(f"Failed to get sent mail for {user_id}: {e}")
            raise
        finally:
            conn.close()

    async def get_mail_by_id(self, mail_id: int, user_id: str) -> Optional[Mail]:
        """
        Get a specific mail message

        Args:
            mail_id: Mail ID
            user_id: User ID (for authorization)

        Returns:
            Mail object or None if not found or not authorized
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT mail_id, sender_id, sender_handle, recipient_id,
                       subject, body, sent_at, read_at, is_read,
                       is_deleted_by_sender, is_deleted_by_recipient
                FROM mail
                WHERE mail_id = ? AND (sender_id = ? OR recipient_id = ?)
                """,
                (mail_id, user_id, user_id)
            )
            row = cursor.fetchone()

            if not row:
                return None

            # Check if deleted
            if row[3] == user_id and row[10]:  # recipient deleted
                return None
            if row[1] == user_id and row[9]:  # sender deleted
                return None

            mail = Mail(
                mail_id=row[0],
                sender_id=row[1],
                sender_handle=row[2],
                recipient_id=row[3],
                subject=row[4],
                body=row[5],
                sent_at=datetime.fromisoformat(row[6]),
                read_at=datetime.fromisoformat(row[7]) if row[7] else None,
                is_read=bool(row[8]),
                is_deleted_by_sender=bool(row[9]),
                is_deleted_by_recipient=bool(row[10])
            )

            return mail

        except sqlite3.Error as e:
            logger.error(f"Failed to get mail {mail_id}: {e}")
            raise
        finally:
            conn.close()

    async def mark_as_read(self, mail_id: int, user_id: str) -> bool:
        """
        Mark a mail as read

        Args:
            mail_id: Mail ID
            user_id: User ID (must be recipient)

        Returns:
            True if successful, False otherwise
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE mail
                SET is_read = 1, read_at = ?
                WHERE mail_id = ? AND recipient_id = ? AND is_read = 0
                """,
                (datetime.now().isoformat(), mail_id, user_id)
            )

            success = cursor.rowcount > 0
            conn.commit()

            if success:
                logger.info(f"Mail {mail_id} marked as read by {user_id}")

            return success

        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Failed to mark mail {mail_id} as read: {e}")
            raise
        finally:
            conn.close()

    async def delete_mail(self, mail_id: int, user_id: str) -> bool:
        """
        Delete a mail (soft delete)

        Args:
            mail_id: Mail ID
            user_id: User ID

        Returns:
            True if successful, False otherwise
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if user is sender or recipient
            cursor.execute(
                """
                SELECT sender_id, recipient_id, is_deleted_by_sender, is_deleted_by_recipient
                FROM mail
                WHERE mail_id = ?
                """,
                (mail_id,)
            )
            row = cursor.fetchone()

            if not row:
                return False

            sender_id, recipient_id, deleted_by_sender, deleted_by_recipient = row

            # Determine which flag to set
            if user_id == sender_id:
                cursor.execute(
                    "UPDATE mail SET is_deleted_by_sender = 1 WHERE mail_id = ?",
                    (mail_id,)
                )
            elif user_id == recipient_id:
                cursor.execute(
                    "UPDATE mail SET is_deleted_by_recipient = 1 WHERE mail_id = ?",
                    (mail_id,)
                )
            else:
                return False

            # If both deleted, physically delete
            if (user_id == sender_id and deleted_by_recipient) or \
               (user_id == recipient_id and deleted_by_sender):
                cursor.execute("DELETE FROM mail WHERE mail_id = ?", (mail_id,))
                logger.info(f"Mail {mail_id} physically deleted")
            else:
                logger.info(f"Mail {mail_id} soft deleted by {user_id}")

            conn.commit()
            return True

        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Failed to delete mail {mail_id}: {e}")
            raise
        finally:
            conn.close()

    async def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread mail for a user

        Args:
            user_id: User ID

        Returns:
            Number of unread messages
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM mail
                WHERE recipient_id = ? AND is_read = 0 AND is_deleted_by_recipient = 0
                """,
                (user_id,)
            )
            count = cursor.fetchone()[0]
            return count

        except sqlite3.Error as e:
            logger.error(f"Failed to get unread count for {user_id}: {e}")
            return 0
        finally:
            conn.close()

    async def get_all_users_for_mail(self) -> List[tuple]:
        """
        Get list of all users (for recipient selection)

        Returns:
            List of (user_id, handle_name) tuples
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT user_id, handle_name
                FROM users
                WHERE user_id != 'guest'
                ORDER BY user_id
                """
            )
            users = cursor.fetchall()
            return users

        except sqlite3.Error as e:
            logger.error(f"Failed to get user list: {e}")
            return []
        finally:
            conn.close()
