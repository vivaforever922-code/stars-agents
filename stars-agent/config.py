import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
SESSION = os.environ["TG_SESSION"]
PHONE = os.environ.get("TG_PHONE")

DAILY_POST_CAP = int(os.getenv("DAILY_POST_CAP", 25))
POST_INTERVAL_MIN = int(os.getenv("POST_INTERVAL_MIN", 420))
REPORT_HOUR = int(os.getenv("REPORT_HOUR", 20))

TARGETS_FILE = "targets.txt"
DB_PATH = "agent.db"
