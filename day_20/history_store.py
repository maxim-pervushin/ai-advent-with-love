import sqlite3
from typing import List, Dict
from datetime import datetime


class HistoryStore:
    """SQLite-based global chat history storage"""

    def __init__(self, db_path: str = "chat_history.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize the database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_message(self, role: str, content: str):
        """Add a message to the global history"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
                (role, content, now),
            )
            conn.commit()

    def get_all_messages(self) -> List[Dict]:
        """Get all messages from history"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content, created_at FROM messages ORDER BY created_at ASC"
            )
            rows = cursor.fetchall()
            return [{"role": row["role"], "content": row["content"]} for row in rows]

    def get_message_count(self) -> int:
        """Get the total number of messages"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM messages")
            result = cursor.fetchone()
            count = result[0] if result else 0
            return int(count)

    def delete_all_messages(self):
        """Delete all messages"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages")
            conn.commit()

    def update_messages_with_summary(self, summary: str, recent_messages: List[Dict]):
        """Replace all messages with a summary message and recent messages"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages")
            now = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
                ("system", f"Chat summary: {summary}", now),
            )
            for msg in recent_messages:
                cursor.execute(
                    "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
                    (msg["role"], msg["content"], now),
                )
            conn.commit()
