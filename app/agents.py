from dataclasses import dataclass


@dataclass(frozen=True)
class Agent:
    name: str
    purpose: str
    instructions: str


AGENTS = [
    Agent(
        "planner",
        "Görevleri planlar.",
        "Görevi aşamalara böl, öncelikleri ve riskleri belirle."
    ),
    Agent(
        "researcher",
        "Araştırma ve kaynak değerlendirme.",
        "Bilgileri karşılaştır, belirsizlikleri açıkça belirt."
    ),
    Agent(
        "coder",
        "Yazılım geliştirme.",
        "Çalışabilir, güvenli ve açıklamalı kod üret."
    ),
    Agent(
        "reviewer",
        "Kalite ve güvenlik kontrolü.",
        "Hataları, eksikleri ve güvenlik risklerini bul."
    ),
    Agent(
        "writer",
        "Metin ve belge hazırlama.",
        "Açık, anlaşılır ve amaca uygun metin yaz."
    ),
    Agent(
        "analyst",
        "Veri ve mantık analizi.",
        "Verileri adım adım incele, sonuçları gerekçelendir."
    ),
    Agent(
        "creative",
        "Yaratıcı fikir üretimi.",
        "Özgün ve uygulanabilir fikirler geliştir."
    ),
    Agent(
        "teacher",
        "Eğitim ve konu anlatımı.",
        "Konuyu basitten karmaşığa örneklerle öğret."
    ),
]


def choose_agent(task: str) -> str:
    text = task.lower()

    rules = {
        "coder": [
            "kod", "python", "yazılım", "program",
            "uygulama", "hata", "html", "javascript"
        ],
        "researcher": [
            "araştır", "kaynak", "güncel",
            "internette bul", "karşılaştır"
        ],
        "analyst": [
            "analiz", "veri", "istatistik",
            "hesapla", "rapor"
        ],
        "planner": [
            "plan", "proje", "takvim",
            "adım adım", "strateji"
        ],
        "teacher": [
            "öğret", "ders", "konu anlat",
            "sınav", "öğren"
        ],
        "creative": [
            "tasarla", "yaratıcı", "fikir",
            "isim bul", "görsel"
        ],
        "reviewer": [
            "incele", "kontrol et", "denetle",
            "güvenlik", "hata bul"
        ],
    }

    for agent, keywords in rules.items():
        if any(word in text for word in keywords):
            return agent

    return "writer"


def get_agent(agent_name: str) -> Agent:
    for agent in AGENTS:
        if agent.name == agent_name:
            return agent

    return AGENTS[4]
