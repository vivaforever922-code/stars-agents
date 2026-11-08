import random
from loguru import logger
import llm, tg

FALLBACK = [
    "{title} — liens et achats au même prix, ça soutient le canal : {url}",
    "Rappel utile : {title} crédite des étoiles en continu → {url}",
]

PROMPT = """Tu écris un message Telegram court (max 25 mots) pour promouvoir {title}.
Contexte des derniers messages du groupe :
{context}
Contraintes : ton du groupe, une seule accroche, pas d'emoji, termine par le lien {url}."""

async def build(chat, title, url):
    try:
        c = await tg.get_client()
        msgs = await c.get_messages(chat, limit=15)
        context = " | ".join((m.message or "")[:120] for m in msgs if m.message)[:1800]
        out = await llm.complete(PROMPT.format(title=title, context=context, url=url))
        if out and url in out:
            return out.strip()
    except Exception as e:
        logger.warning(f"LLM indisponible ({e}), gabarit utilisé")
    return random.choice(FALLBACK).format(title=title, url=url)
