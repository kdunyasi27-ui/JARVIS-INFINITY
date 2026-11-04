from app.db import connect


def save_memory(user_id: int, title: str, content: str):
    title = title.strip()
    content = content.strip()

    if not title or not content:
        raise ValueError("Başlık ve içerik boş olamaz.")

    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, title)
            )
        """)

        db.execute("""
            INSERT INTO user_memories (user_id, title, content)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, title)
            DO UPDATE SET content = excluded.content
        """, (user_id, title, content))


def get_memories(user_id: int):
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, title)
            )
        """)

        rows = db.execute("""
            SELECT id, title, content, created_at
            FROM user_memories
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,)).fetchall()

    return [dict(row) for row in rows]


def delete_memory(user_id: int, memory_id: int):
    with connect() as db:
        cursor = db.execute("""
            DELETE FROM user_memories
            WHERE user_id = ? AND id = ?
        """, (user_id, memory_id))

    return cursor.rowcount > 0
