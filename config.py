
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))
RAGHAD_ID = int(os.environ.get("RAGHAD_ID"))

ALLOWED_USERS = [OWNER_ID, RAGHAD_ID]
CHANNEL_ID = -1002678532726  # القناة الخاصة

# MongoDB Configuration
MONGO_URI = os.environ.get("MONGO_URI")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "shaghaf_db")  # اسم قاعدة البيانات كمتغير مع قيمة افتراضية
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "memories")  # اسم الكولكشن كمتغير مع قيمة افتراضية
