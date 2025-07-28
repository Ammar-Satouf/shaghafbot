import os
import hashlib

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))
RAGHAD_ID = int(os.environ.get("RAGHAD_ID"))

ALLOWED_USERS = [OWNER_ID, RAGHAD_ID]

# إعدادات الحماية المتقدمة
SECURITY_KEY = hashlib.sha256(f"SHAGHAD_PROTECTED_{BOT_TOKEN}".encode()).hexdigest()
ANTI_COPY_PROTECTION = True
ANTI_FORWARD_PROTECTION = True
RATE_LIMIT_ENABLED = True
CONTENT_ENCRYPTION = True

# رسائل الحماية
PROTECTION_MESSAGE = "🔒 هذا المحتوى محمي بنظام الأمان المتقدم"
ANTI_COPY_MESSAGE = "⚠️ محتوى محمي - لا تحول أو تنسخ"
ANTI_SCREENSHOT_MESSAGE = "📵 السكرينشوت والنسخ محظور"

# إعدادات حماية إضافية
MAX_FORWARD_ATTEMPTS = 3
SCREENSHOT_DETECTION = True
INVISIBLE_WATERMARK = True

# MongoDB Configuration
MONGO_URI = os.environ.get("MONGO_URI")
DATABASE_NAME = "shaghaf_db"
COLLECTION_NAME = "memories"
