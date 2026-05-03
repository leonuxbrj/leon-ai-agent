"""
Memory system - SQLite-based persistent memory for the AI agent.
Stores conversations, learned knowledge, and file references.
"""

import sqlite3
import json
import os
from datetime import datetime


class Memory:
    def __init__(self, db_path="memory.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT
            );

            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                timestamp TEXT NOT NULL,
                metadata TEXT
            );

            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                file_type TEXT,
                summary TEXT,
                content_preview TEXT,
                timestamp TEXT NOT NULL,
                metadata TEXT
            );

            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                description TEXT NOT NULL,
                result TEXT,
                timestamp TEXT NOT NULL,
                metadata TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_conv_timestamp ON conversations(timestamp);
            CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge(category);
            CREATE INDEX IF NOT EXISTS idx_files_filename ON files(filename);
        """)
        self.conn.commit()

    def add_message(self, role, content, metadata=None):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (role, content, timestamp, metadata) VALUES (?, ?, ?, ?)",
            (role, content, datetime.now().isoformat(), json.dumps(metadata) if metadata else None)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_recent_messages(self, limit=50):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT role, content, timestamp FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return list(reversed(cursor.fetchall()))

    def add_knowledge(self, source, content, category="general", metadata=None):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO knowledge (source, content, category, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
            (source, content, category, datetime.now().isoformat(), json.dumps(metadata) if metadata else None)
        )
        self.conn.commit()
        return cursor.lastrowid

    def search_knowledge(self, query, limit=10):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT source, content, category FROM knowledge WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{query}%", limit)
        )
        return cursor.fetchall()

    def get_all_knowledge(self, category=None, limit=100):
        cursor = self.conn.cursor()
        if category:
            cursor.execute(
                "SELECT source, content, category, timestamp FROM knowledge WHERE category = ? ORDER BY id DESC LIMIT ?",
                (category, limit)
            )
        else:
            cursor.execute(
                "SELECT source, content, category, timestamp FROM knowledge ORDER BY id DESC LIMIT ?",
                (limit,)
            )
        return cursor.fetchall()

    def add_file(self, filename, filepath, file_type=None, summary=None, content_preview=None, metadata=None):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO files (filename, filepath, file_type, summary, content_preview, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (filename, filepath, file_type, summary, content_preview, datetime.now().isoformat(),
             json.dumps(metadata) if metadata else None)
        )
        self.conn.commit()
        return cursor.lastrowid

    def search_files(self, query, limit=10):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT filename, filepath, file_type, summary FROM files WHERE filename LIKE ? OR content LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{query}%", f"%{query}%", limit)
        )
        return cursor.fetchall()

    def log_action(self, action_type, description, result=None, metadata=None):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO actions (action_type, description, result, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
            (action_type, description, result, datetime.now().isoformat(),
             json.dumps(metadata) if metadata else None)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_recent_actions(self, limit=20):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT action_type, description, result, timestamp FROM actions ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return list(reversed(cursor.fetchall()))

    def get_stats(self):
        cursor = self.conn.cursor()
        stats = {}
        for table in ["conversations", "knowledge", "files", "actions"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        return stats

    def close(self):
        self.conn.close()
