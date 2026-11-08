import asyncio, datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
logger.add("agent.log", rotation="1 MB", level="INFO")
import db, programs, distributor, tracker, config

async def process_missions():
    con = db.init()
    cur = con.execute("SELECT id, text FROM missions WHERE status='pending'")
    rows = cur.fetchall()
    for mid, text in rows:
        logger.info("Mission recue: {}", text)
        con.execute("UPDATE missions SET status='done', done_at=? WHERE id=?", (datetime.datetime.now().isoformat(), mid))
    con.commit()
    con.close()

async def cycle():
    await programs.discover()
    await programs.join_pending()
    await distributor.distribute()
    await tracker.snapshot()
    await process_missions()

async def main():
    db.init()
    sched = AsyncIOScheduler()
    sched.add_job(cycle, "interval", minutes=config.POST_INTERVAL_MIN)
    sched.add_job(tracker.report, "cron", hour=config.REPORT_HOUR)
    sched.start()
    logger.info("agent demarre")
    await cycle()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
