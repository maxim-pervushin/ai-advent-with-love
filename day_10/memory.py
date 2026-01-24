import sqlite3
import os
from typing import List, Dict
from datetime import datetime

DATABASE_PATH = "chat_history.db"


def get_db_connection():
    """Get a database connection with row factory for dictionary-like access"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create messages table with summary tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            is_summary INTEGER DEFAULT 0,
            summary_id INTEGER NULL,
            FOREIGN KEY (summary_id) REFERENCES messages (id)
        )
    """)

    # Add new columns to existing table if they don't exist
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN is_summary INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN summary_id INTEGER NULL")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()


def clear_history():
    """Clear all messages from the history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages")
    conn.commit()
    conn.close()


def add_message(role: str, content: str):
    """Add a message to the chat history"""
    conn = get_db_connection()
    cursor = conn.cursor()

    timestamp = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO messages (role, content, timestamp) VALUES (?, ?, ?)",
        (role, content, timestamp),
    )

    conn.commit()
    conn.close()




def get_full_history() -> List[Dict[str, str]]:
    """Get the complete conversation history for user display"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT role, content, timestamp, is_summary FROM messages ORDER BY id ASC"
    )

    messages = [
        {
            "role": row["role"],
            "content": row["content"],
            "timestamp": row["timestamp"],
            "is_summary": bool(row["is_summary"]),
        }
        for row in cursor.fetchall()
    ]

    conn.close()
    return messages


def get_ai_history() -> List[Dict[str, str]]:
    """Get conversation history with only the last summary and messages after it for AI context"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the latest summary message
    cursor.execute(
        "SELECT id FROM messages WHERE is_summary = 1 ORDER BY id DESC LIMIT 1"
    )
    latest_summary = cursor.fetchone()

    if latest_summary:
        # Get the latest summary and all messages after it
        cursor.execute(
            "SELECT role, content FROM messages WHERE id >= ? ORDER BY id ASC",
            (latest_summary["id"],),
        )
    else:
        # No summary exists, get all messages
        cursor.execute("SELECT role, content FROM messages ORDER BY id ASC")

    messages = [
        {"role": row["role"], "content": row["content"]} for row in cursor.fetchall()
    ]

    conn.close()
    return messages


def get_latest_summary() -> Dict[str, str] | None:
    """Get the most recent summary message"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT role, content, timestamp FROM messages WHERE is_summary = 1 ORDER BY id DESC LIMIT 1"
    )
    result = cursor.fetchone()

    conn.close()

    if result:
        return {
            "role": result["role"],
            "content": result["content"],
            "timestamp": result["timestamp"],
        }
    return None


def add_summary(content: str) -> int:
    """Add a summary message and return its ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    timestamp = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO messages (role, content, timestamp, is_summary) VALUES (?, ?, ?, ?)",
        ("system", content, timestamp, 1),
    )

    summary_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return summary_id


def get_messages_since_summary() -> List[Dict[str, str]]:
    """Get all messages since the latest summary"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the latest summary message
    cursor.execute(
        "SELECT id FROM messages WHERE is_summary = 1 ORDER BY id DESC LIMIT 1"
    )
    latest_summary = cursor.fetchone()

    if latest_summary:
        # Get all messages after the latest summary
        cursor.execute(
            "SELECT role, content, timestamp FROM messages WHERE id > ? ORDER BY id ASC",
            (latest_summary["id"],),
        )
    else:
        # No summary exists, get all messages
        cursor.execute("SELECT role, content, timestamp FROM messages ORDER BY id ASC")

    messages = [
        {"role": row["role"], "content": row["content"], "timestamp": row["timestamp"]}
        for row in cursor.fetchall()
    ]

    conn.close()
    return messages


def get_message_count() -> int:
    """Get the number of messages in the history"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM messages")
    result = cursor.fetchone()

    conn.close()
    return result["count"] if result else 0


def get_messages_since_last_summary_count() -> int:
    """Get the number of messages since the last summary"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the latest summary message
    cursor.execute(
        "SELECT id FROM messages WHERE is_summary = 1 ORDER BY id DESC LIMIT 1"
    )
    latest_summary = cursor.fetchone()

    if latest_summary:
        # Count messages after the latest summary
        cursor.execute(
            "SELECT COUNT(*) as count FROM messages WHERE id > ?",
            (latest_summary["id"],),
        )
    else:
        # No summary exists, count all messages
        cursor.execute("SELECT COUNT(*) as count FROM messages")

    result = cursor.fetchone()
    conn.close()
    
    return result["count"] if result else 0


# Initialize the database when module is imported
init_database()
