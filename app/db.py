import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import settings


@contextmanager
def connect():
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(str(path), timeout=30)
    db.row_factory = sqlite3.Row

    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    with connect() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id);

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_conversations (
                conversation_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_user_conversations_user
            ON user_conversations(user_id);
        """)

        columns = {
            row["name"]
            for row in db.execute(
                "PRAGMA table_info(user_memories)"
            ).fetchall()
        }

        if not columns:
            db.execute("""
                CREATE TABLE user_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            if "title" not in columns:
                db.execute("""
                    ALTER TABLE user_memories
                    ADD COLUMN title TEXT NOT NULL DEFAULT ''
                """)

            if "content" not in columns:
                db.execute("""
                    ALTER TABLE user_memories
                    ADD COLUMN content TEXT NOT NULL DEFAULT ''
                """)

            db.execute("""
                UPDATE user_memories
                SET title = 'Eski kayıt ' || id
                WHERE title = ''
            """)

        db.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_user_title
            ON user_memories(user_id, title)
        """)


def create_user(email, password_hash):
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email.lower().strip(), password_hash)
        )
        return cursor.lastrowid


def get_user_by_email(email):
    with connect() as db:
        return db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.lower().strip(),)
        ).fetchone()


def get_user_by_id(user_id):
    with connect() as db:
        return db.execute(
            "SELECT id, email, created_at FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()


def claim_conversation(user_id, conversation_id):
    with connect() as db:
        row = db.execute(
            "SELECT user_id FROM user_conversations WHERE conversation_id = ?",
            (conversation_id,)
        ).fetchone()

        if row:
            return int(row["user_id"]) == int(user_id)

        try:
            db.execute(
                """
                INSERT INTO user_conversations (conversation_id, user_id)
                VALUES (?, ?)
                """,
                (conversation_id, user_id)
            )
            return True
        except sqlite3.IntegrityError:
            row = db.execute(
                "SELECT user_id FROM user_conversations WHERE conversation_id = ?",
                (conversation_id,)
            ).fetchone()
            return bool(row and int(row["user_id"]) == int(user_id))


def get_user_history(user_id, conversation_id, limit=30):
    with connect() as db:
        owner = db.execute(
            """
            SELECT user_id FROM user_conversations
            WHERE conversation_id = ?
            """,
            (conversation_id,)
        ).fetchone()

        if not owner or int(owner["user_id"]) != int(user_id):
            raise PermissionError("Konuşmaya erişim izniniz yok.")

        rows = db.execute(
            """
            SELECT role, content FROM messages
            WHERE conversation_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (conversation_id, limit)
        ).fetchall()

        return [
            {"role": row["role"], "content": row["content"]}
            for row in reversed(rows)
        ]


def save_user_message(user_id, conversation_id, role, content):
    with connect() as db:
        owner = db.execute(
            """
            SELECT user_id FROM user_conversations
            WHERE conversation_id = ?
            """,
            (conversation_id,)
        ).fetchone()

        if not owner or int(owner["user_id"]) != int(user_id):
            raise PermissionError("Konuşmaya erişim izniniz yok.")

        db.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, role, content)
        )


def save_message(conversation_id, role, content):
    with connect() as db:
        db.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, role, content)
        )


def get_history(conversation_id, limit=30):
    with connect() as db:
        rows = db.execute(
            """
            SELECT role, content FROM messages
            WHERE conversation_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (conversation_id, limit)
        ).fetchall()

        return [
            {"role": row["role"], "content": row["content"]}
            for row in reversed(rows)
        ]
