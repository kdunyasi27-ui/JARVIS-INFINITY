from datetime import datetime, timezone

from app.db import connect


def daily_review():

    with connect() as db:

        total_messages = db.execute(
            "SELECT COUNT(*) AS n FROM messages"
        ).fetchone()["n"]

        total_conversations = db.execute(
            "SELECT COUNT(DISTINCT conversation_id) AS n FROM messages"
        ).fetchone()["n"]

        pending_approvals = db.execute(
            "SELECT COUNT(*) AS n FROM approvals WHERE status = 'pending'"
        ).fetchone()["n"]

    report = f"""
JARVIS INFINITY — GÜNLÜK GELİŞİM RAPORU

Tarih:
{datetime.now(timezone.utc).isoformat()}

TOPLAM MESAJ: {total_messages}

TOPLAM KONUŞMA: {total_conversations}

BEKLEYEN ONAY: {pending_approvals}

GELİŞİM ÖNERİLERİ:

1. Model cevap kalitesini ölç.
2. Başarısız görevleri incele.
3. Güvenlik kontrollerini çalıştır.
4. Yedeklerin durumunu doğrula.
5. Yeni özellik önerilerini değerlendir.

OTOMATİK KOD DEĞİŞİKLİĞİ: KAPALI

Önemli değişiklikler kullanıcı onayı gerektirir.
"""

    with connect() as db:
        db.execute(
            "INSERT INTO review_reports (report) VALUES (?)",
            (report,)
        )

    return {
        "report": report,
        "auto_code_changes": False
    }
