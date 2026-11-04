from dataclasses import dataclass


@dataclass(frozen=True)
class Agent:
    name: str
    purpose: str


AGENTS = [
    Agent("planner", "Görevleri analiz eder ve ayrıntılı plan oluşturur."),
    Agent("researcher", "Araştırma yapar ve kaynakları karşılaştırır."),
    Agent("coder", "Yazılım geliştirir ve kod taslakları hazırlar."),
    Agent("reviewer", "Sonuçları hata ve güvenlik açısından denetler."),
    Agent("writer", "Metin, belge ve içerik üretir."),
    Agent("analyst", "Verileri inceler ve analiz eder."),
    Agent("creative", "Yaratıcı fikirler, tasarımlar ve projeler üretir."),
    Agent("teacher", "Konuları öğretir ve kişiye özel eğitim hazırlar."),
]


def choose_agent(task: str) -> str:
    text = task.lower()
    if any(x in text for x in ("kod", "python", "uygulama", "yazılım", "program", "hata")):
        return "coder"
    if any(x in text for x in ("araştır", "kaynak", "güncel", "karşılaştır", "bilgi bul")):
        return "researcher"
    if any(x in text for x in ("analiz", "veri", "istatistik", "rapor", "hesapla")):
        return "analyst"
    if any(x in text for x in ("plan", "proje", "adım adım")):
        return "planner"
    if any(x in text for x in ("öğret", "ders", "konu anlat", "sınav", "öğren")):
        return "teacher"
    if any(x in text for x in ("tasarla", "yaratıcı", "fikir", "görsel", "tasarım")):
        return "creative"
    return "writer"
