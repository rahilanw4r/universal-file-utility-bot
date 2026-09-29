import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured.")

# Telegram's hosted Bot API getFile download ceiling is 20 MB.
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "19"))
if not 1 <= MAX_FILE_SIZE_MB <= 19:
    raise ValueError("MAX_FILE_SIZE_MB must be between 1 and 19 for the hosted Bot API.")
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

MAX_BATCH_FILES = int(os.getenv("MAX_BATCH_FILES", "8"))
if not 1 <= MAX_BATCH_FILES <= 20:
    raise ValueError("MAX_BATCH_FILES must be between 1 and 20.")

TEMP_DIR = Path(os.getenv("TEMP_DIR", "downloads")).resolve()
TEMP_DIR.mkdir(parents=True, exist_ok=True)
