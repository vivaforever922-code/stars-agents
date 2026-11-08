import asyncio, random, datetime
from loguru import logger
import db, tg, config

def load_targets():
    try:
        return [l.strip() for l in open(config.TARGETS_FILE, encoding="utf-8") if l.strip() and not l.startswith("#")]
    except FileNotFoundError:
        logger.warning("targets.txt manquant")
        return []

def posts_today(con):
    return con.execute(
        "SELECT COUNT(*) FROM posts WHERE date(sent_at)=date('now')"
    ).fetchone()[0]

TEMPLATES = [
    "Petit rappel : {title} te fait gagner des étoiles en continu. Teste ici → {url}",
    "Si tu utilises {title}, passe par ce lien, tu soutiens le canal sans rien payer de plus : {url}",
    "{title} — commissions reversées, achats au même prix. Lien : {url}",
]

async def gen_text(title, url):
    try:
        import llm
        prompt = ("Redige un court message Telegram (1-2 phrases) pour promouvoir {} "
                  "avec ce lien {}. Ton amical, sans spam. Inclus le lien.").format(title, url)
        return await llm.complete(prompt)
    except Exception as e:
        logger.debug("llm indisponible, template: {}", e)
        return random.choice(TEMPLATES).format(title=title, url=url)

async def distribute():
    con = db.init()
    if posts_today(con) >= config.DAILY_POST_CAP:
        logger.info("quota quotidien atteint ({}/{})", posts_today(con), config.DAILY_POST_CAP)
        con.close()
        return
    targets = load_targets()
    rows = con.execute(
        "SELECT bot_id,title,url FROM programs WHERE joined=1 AND url IS NOT NULL"
    ).fetchall()
    if not targets:
        logger.info("aucune cible dans targets.txt")
        con.close()
        return
    if not rows:
        logger.info("aucun programme rejoint")
        con.close()
        return
    for bot_id, title, url in rows:
        free = [t for t in targets
                if not con.execute("SELECT 1 FROM posts WHERE bot_id=? AND chat=?",
                                   (bot_id, t)).fetchone()]
        if not free:
            logger.info("toutes les cibles deja postees pour {}", bot_id)
            continue
        chat = random.choice(free)
        text = await gen_text(title, url)
        try:
            msg = await tg.get_client()
            sent = await msg.send_message(chat, text, link_preview=False)
            con.execute("INSERT INTO posts(bot_id,chat,msg_id,sent_at) VALUES(?,?,?,datetime('now'))",
                        (bot_id, chat, sent.id))
            con.commit()
            logger.success("posté {} dans {}", bot_id, chat)
            await asyncio.sleep(random.randint(90, 240))
        except Exception as e:
            logger.error("{}: {}", chat, e)
        if posts_today(con) >= config.DAILY_POST_CAP:
            break
    con.close()