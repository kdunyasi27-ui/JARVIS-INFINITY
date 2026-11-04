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

Tarih: {datetime.now(timezone.utc).isoformat()}

Toplam mesaj: {total_messages}
Toplam konuşma: {total_conversations}
Bekleyen onay: {pending_approvals}

GELİŞİM ÖNERİLERİ

1. Model cevap kalitesini değerlendir.
2. Başarısız görevleri incele.
3. Güvenlik kontrollerini çalıştır.
4. Veritabanı yedeklerini doğrula.
5. Yeni özellik önerilerini değerlendir.

Otomatik kod değişikliği: KAPALI
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
