from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import config

with TelegramClient(StringSession(), config.API_ID, config.API_HASH) as c:
    print("\nSESSION:\n" + c.session.save() + "\n")
