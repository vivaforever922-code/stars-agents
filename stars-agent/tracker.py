from loguru import logger
import db, tg, config

async def snapshot():
    try:
        st = await tg.call(__import__("telethon.tl.functions", fromlist=["payments"]).payments.GetStarsStatusRequest, peer="me")
        bal = getattr(getattr(st, "balance", None), "amount", 0)
    except Exception as e:
        logger.warning("snapshot indisponible: {}", e)
        bal = 0
    con = db.init()
    con.execute("INSERT INTO balances(ts,stars) VALUES(datetime('now'),?)", (bal,))
    con.commit()
    logger.info("solde snapshot: {} étoiles".format(bal))
    con.close()
    return bal

async def report():
    try:
        con = db.init()
        first = con.execute("SELECT stars FROM balances ORDER BY id LIMIT 1").fetchone()
        last = con.execute("SELECT stars FROM balances ORDER BY id DESC LIMIT 1").fetchone()
        total_posts = con.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        joined = con.execute("SELECT COUNT(*) FROM programs WHERE joined=1").fetchone()[0]
        delta = (last[0] - first[0]) if first and last else 0
        txt = ("Rapport agent\nProgrammes actifs : {}\nPosts cumulés : {}\n"
               "Solde actuel : {} étoiles\nGain depuis le début : {:+d}\n"
               "Retrait possible : {}").format(joined, total_posts, last[0] if last else 0, delta,
               "oui" if (last and last[0] >= 1000) else "non (min 1000)")
        c = await tg.get_client()
        await c.send_message("me", txt)
        logger.info("rapport envoyé")
        con.close()
    except Exception as e:
        logger.error("report: {}", e)