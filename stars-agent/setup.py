import os
from dotenv import set_key, load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

ENV = ".env"

def main():
    print("=== stars-agent setup ===")
    api_id = input("TG_API_ID (depuis my.telegram.org) : ").strip()
    api_hash = input("TG_API_HASH : ").strip()
    phone = input("TG_PHONE (ex: +33612345678) : ").strip()

    if not api_id or not api_hash:
        print("API_ID et API_HASH sont obligatoires.")
        return

    if not os.path.exists(ENV):
        with open(ENV, "w") as f:
            f.write("")

    set_key(ENV, "TG_API_ID", api_id)
    set_key(ENV, "TG_API_HASH", api_hash)
    set_key(ENV, "TG_PHONE", phone)
    set_key(ENV, "DAILY_POST_CAP", "25")
    set_key(ENV, "POST_INTERVAL_MIN", "420")
    set_key(ENV, "REPORT_HOUR", "20")

    load_dotenv(ENV)
    os.environ["TG_API_ID"] = api_id
    os.environ["TG_API_HASH"] = api_hash
    os.environ["TG_PHONE"] = phone

    print("\nConnexion a Telegram (code SMS possible)...")
    with TelegramClient(StringSession(), int(api_id), api_hash) as c:
        c.start(phone=phone)
        session = c.session.save()
        set_key(ENV, "TG_SESSION", session)
        print("\nSESSION sauvegardee dans .env")

    print("\nSetup termine. Lancez : python validate.py puis python main.py")

if __name__ == "__main__":
    main()