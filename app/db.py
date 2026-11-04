
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import settings


@contextmanager
def connect():
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        str(db_path),
        timeout=30
    )
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with connect() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id);

            CREATE TABLE IF NOT EXISTS review_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT '',
                details TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)


def save_message(conversation_id, role, content):
    with connect() as db:
        db.execute(
            """
            INSERT INTO messages (
                conversation_id,
                role,
                content
            )
            VALUES (?, ?, ?)
            """,
            (conversation_id, role, content)
        )


def get_history(conversation_id, limit=30):
    limit = max(1, min(int(limit), 100))

    with connect() as db:
        rows = db.execute(
            """
            SELECT role, content
            FROM (
                SELECT id, role, content
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
            )
            ORDER BY id ASC
            """,
            (conversation_id, limit)
        ).fetchall()

    return [dict(row) for row in rows]


def create_user(email, password_hash):
    with connect() as db:
        cursor = db.execute(
            """
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
            """,
            (email, password_hash)
        )

        return cursor.lastrowid


def get_user_by_email(email):
    with connect() as db:
        row = db.execute(
            """
            SELECT id, email, password_hash, created_at
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

    return dict(row) if row else None


def get_user_by_id(user_id):
    with connect() as db:
        row = db.execute(
            """
            SELECT id, email, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

    return dict(row) if row else None
