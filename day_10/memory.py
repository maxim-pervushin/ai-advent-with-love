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
    
    # Create messages table (no session_id - single chat history)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()


def clear_history():
    """Clear all messages from the history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages')
    conn.commit()
    conn.close()


def add_message(role: str, content: str):
    """Add a message to the chat history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.utcnow().isoformat()
    cursor.execute(
        'INSERT INTO messages (role, content, timestamp) VALUES (?, ?, ?)',
        (role, content, timestamp)
    )
    
    conn.commit()
    conn.close()


def get_conversation_history() -> List[Dict[str, str]]:
    """Get the conversation history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT role, content FROM messages ORDER BY id ASC')
    
    messages = [{"role": row["role"], "content": row["content"]} for row in cursor.fetchall()]
    
    conn.close()
    return messages


def get_message_count() -> int:
    """Get the number of messages in the history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM messages')
    result = cursor.fetchone()
    
    conn.close()
    return result["count"] if result else 0


# Initialize the database when module is imported
init_database()