import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS programs(
  bot_id INTEGER PRIMARY KEY, title TEXT, commission INTEGER,
  url TEXT, joined INTEGER DEFAULT 0, created_at TEXT);
CREATE TABLE IF NOT EXISTS posts(
  id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id INTEGER, chat TEXT,
  msg_id INTEGER, sent_at TEXT, UNIQUE(bot_id, chat));
CREATE TABLE IF NOT EXISTS balances(
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, stars INTEGER);
CREATE TABLE IF NOT EXISTS missions(
  id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, status TEXT DEFAULT 'pending',
  created_at TEXT, done_at TEXT);
"""

def init():
    con = sqlite3.connect("agent.db")
    con.executescript(SCHEMA)
    con.commit()
    return con
