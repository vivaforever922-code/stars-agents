import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.sessions import StringSession
from loguru import logger
import config

_client = None

async def get_client():
    global _client
    if _client is None:
        _client = TelegramClient(StringSession(config.SESSION), config.API_ID, config.API_HASH)
        await _client.start(phone=config.PHONE)
        if not await _client.is_user_authorized():
            raise SessionPasswordNeededError("session invalide, relance setup_session.py")
    return _client

async def call(fn, *a, **kw):
    """Appel API avec retry exponentiel sur FloodWait."""
    c = await get_client()
    for attempt in range(5):
        try:
            return await c(fn(*a, **kw))
        except FloodWaitError as e:
            wait = e.seconds + 5
            logger.warning(f"FloodWait {wait}s (tentative {attempt+1})")
            await asyncio.sleep(wait)
    raise RuntimeError("FloodWait persistant")
