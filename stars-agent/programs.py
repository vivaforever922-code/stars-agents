from loguru import logger
import db, tg

async def discover():
    """Liste les mini-apps proposant un programme d'affiliation."""
    try:
        from telethon.tl import functions
        res = await tg.call(
            functions.payments.GetSuggestedStarRefBotsRequest,
            peer="me", offset="", limit=50,
        )
    except Exception as e:
        logger.warning("discover indisponible: {}", e)
        return
    con = db.init()
    for bot in getattr(res, "bots", []) or []:
        try:
            con.execute(
                "INSERT OR IGNORE INTO programs(bot_id, title, commission, url, created_at) VALUES (?,?,?,?,?)",
                (bot.bot_id, getattr(bot, "title", ""), getattr(bot, "commission", 0),
                 getattr(bot, "url", ""), datetime_now()),
            )
        except Exception as e:
            logger.debug("insert program: %s", e)
    con.commit()
    con.close()

async def join_pending():
    logger.info("join_pending: rien a faire (placeholder)")

def datetime_now():
    import datetime
    return datetime.datetime.now().isoformat()
