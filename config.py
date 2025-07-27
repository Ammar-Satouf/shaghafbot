
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URI = os.environ.get("MONGO_URI")
OWNER_ID = int(os.environ.get("OWNER_ID"))
RAGHAD_ID = int(os.environ.get("RAGHAD_ID"))
DB_NAME = os.environ.get("DB_NAME", "shaghaf_db")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "memories")

ALLOWED_USERS = [OWNER_ID, RAGHAD_ID]
CHANNEL_ID = -1002678532726  # القناة الخاصة
