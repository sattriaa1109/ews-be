import logging

from config import CONTEXT_KEYWORDS, NEGATIVE_KEYWORDS, ALERT_THRESHOLD
from models.tables import Alert

logger = logging.getLogger("detector")


def _contains(text: str, keyword: str) -> bool:
    return keyword.lower() in text.lower()


def _has_context(text: str) -> bool:
    """Artikel harus menyinggung TNI AD / entitas terkait dulu,
    biar gak nangkep berita yang gak relevan sama sekali."""
    return any(_contains(text, kw) for kw in CONTEXT_KEYWORDS)


def score_text(text: str) -> tuple[float, list[str], list[str]]:
    """Hitung skor severity dari sebuah teks.
    Return: (skor_total, kategori_yang_match, kata_yang_match)
    """
    total_score = 0.0
    matched_categories = []
    matched_words = []

    for category, rule in NEGATIVE_KEYWORDS.items():
        hits = [w for w in rule["words"] if _contains(text, w)]
        if hits:
            total_score += rule["weight"] * len(hits)
            matched_categories.append(category)
            matched_words.extend(hits)

    return total_score, matched_categories, matched_words


def evaluate_article(db, article) -> Alert | None:
    """Evaluasi satu artikel: cek konteks lalu skor. Kalau lolos threshold,
    buat record Alert. Return Alert kalau dibuat, None kalau tidak."""
    full_text = f"{article.title} {article.raw_summary or ''}"

    if not _has_context(full_text):
        return None

    score, categories, words = score_text(full_text)

    if score < ALERT_THRESHOLD:
        return None

    alert = Alert(
        article_id=article.id,
        severity_score=score,
        matched_categories=",".join(categories),
        matched_words=", ".join(sorted(set(words))),
        notified=0,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    logger.info(f"Alert dibuat untuk artikel #{article.id} dengan skor {score}")

    return alert
