"""
Score = commission x confiance / saturation, pondéré par le rendement mesuré.
Aucune donnée de clic n'existe côté Telegram : on mesure le rendement
par programme via les stats du programme et on saisit les gains manuellement.
"""
from datetime import datetime, timedelta
import db

W_COMMISSION = 1.0
W_TRUST = 1.4
W_SATURATION = 0.8
W_YIELD = 2.2

BLACKLIST = ("scam", "casino", "ponzi")

def _trust(con, bot_id):
    row = con.execute("SELECT trust FROM programs WHERE bot_id=?", (bot_id,)).fetchone()
    return (row[0] if row and row[0] is not None else 0.5)

def _saturation(con, bot_id):
    since = (datetime.utcnow() - timedelta(days=7)).isoformat()
    n = con.execute("SELECT COUNT(*) FROM posts WHERE bot_id=? AND sent_at>=?",
                    (bot_id, since)).fetchone()[0]
    return 1.0 / (1.0 + n * 0.25)

def _yield(con, bot_id):
    """Étoiles gagnées par post publié. 0 si inconnu, ce qui pénalise."""
    row = con.execute(
        "SELECT COALESCE(earnings,0), COUNT(p.id) FROM programs pr "
        "LEFT JOIN posts p ON p.bot_id=pr.bot_id WHERE pr.bot_id=? "
        "GROUP BY pr.bot_id", (bot_id,)).fetchone()
    if not row or not row[1]:
        return 0.0
    return row[0] / row[1]

def score(con, bot_id, title, commission):
    if any(w in (title or "").lower() for w in BLACKLIST):
        return 0.0
    s = (commission / 1000.0) * W_COMMISSION
    s *= _trust(con, bot_id) * W_TRUST
    s *= _saturation(con, bot_id) * W_SATURATION
    s += _yield(con, bot_id) * W_YIELD
    return round(s, 4)

def ranked(con, limit=5, min_score=0.05):
    rows = con.execute(
        "SELECT bot_id,title,commission,url FROM programs "
        "WHERE joined=1 AND url IS NOT NULL").fetchall()
    scored = [(score(con, b, t, c), b, t, c, u) for b, t, c, u in rows]
    scored = [x for x in scored if x[0] >= min_score]
    scored.sort(reverse=True)
    for s, b, *_ in scored:
        con.execute("UPDATE programs SET score=? WHERE bot_id=?", (s, b))
    con.commit()
    return scored[:limit]
