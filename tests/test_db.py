
from app.config import settings
from app.db import init_db, save_message, get_history


def test_database_saves_and_reads_messages(tmp_path, monkeypatch):
    database_file = tmp_path / "test_jarvis.db"

    monkeypatch.setattr(
        settings,
        "database_path",
        str(database_file)
    )

    init_db()

    save_message("conversation-1", "user", "Merhaba JARVIS")
    save_message("conversation-1", "assistant", "Merhaba, nasıl yardımcı olayım?")

    history = get_history("conversation-1")

    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Merhaba JARVIS"
    assert history[1]["role"] == "assistant"


def test_database_keeps_conversations_separate(tmp_path, monkeypatch):
    database_file = tmp_path / "separate_test.db"

    monkeypatch.setattr(
        settings,
        "database_path",
        str(database_file)
    )

    init_db()

    save_message("conversation-A", "user", "Birinci sohbet")
    save_message("conversation-B", "user", "İkinci sohbet")

    history_a = get_history("conversation-A")
    history_b = get_history("conversation-B")

    assert len(history_a) == 1
    assert len(history_b) == 1

    assert history_a[0]["content"] == "Birinci sohbet"
    assert history_b[0]["content"] == "İkinci sohbet"


def test_history_limit(tmp_path, monkeypatch):
    database_file = tmp_path / "limit_test.db"

    monkeypatch.setattr(
        settings,
        "database_path",
        str(database_file)
    )

    init_db()

    for number in range(5):
        save_message(
            "conversation-limit",
            "user",
            f"Mesaj {number}"
        )

    history = get_history("conversation-limit", limit=2)

    assert len(history) == 2
    assert history[0]["content"] == "Mesaj 3"
    assert history[1]["content"] == "Mesaj 4"
