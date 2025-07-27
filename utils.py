from config import OWNER_ID, RAGHAD_ID
from resources import LOVE_START_DATE, TIME_MESSAGES
from datetime import datetime, timedelta
import random


def is_authorized(user_id):
    return user_id in [OWNER_ID, RAGHAD_ID]


def get_user_name(user_id):
    if user_id == OWNER_ID:
        return "عمار ❤️"
    elif user_id == RAGHAD_ID:
        return "رغد 🌸"
    return "مجهول"


def calculate_love_duration():
    """حساب المدة منذ بداية الحب"""
    start_date = datetime.strptime(LOVE_START_DATE, "%Y-%m-%d")
    now = datetime.now()

    # حساب الفرق
    diff = now - start_date

    years = diff.days // 365
    remaining_days = diff.days % 365
    months = remaining_days // 30
    days = remaining_days % 30

    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60

    duration_text = "⏰ إحنا مع بعض من:\n\n"

    if years > 0:
        duration_text += f"📅 {years} {TIME_MESSAGES['years']}\n"
    if months > 0:
        duration_text += f"📅 {months} {TIME_MESSAGES['months']}\n"
    if days > 0:
        duration_text += f"📅 {days} {TIME_MESSAGES['days']}\n"
    if hours > 0:
        duration_text += f"🕐 {hours} {TIME_MESSAGES['hours']}\n"
    if minutes > 0:
        duration_text += f"⏱️ {minutes} {TIME_MESSAGES['minutes']}\n"

    duration_text += f"\n💕 إجمالي الأيام: {diff.days} يوم\n"
    duration_text += "🌟 وكل يوم بيمر حبنا بيزيد أكتر!"

    return duration_text


def get_love_message(user_id, surprise=False):
    from resources import LOVE_SURPRISES_AMMAR, LOVE_SURPRISES_RAGHAD, GENERAL_LOVE_QUOTES
    
    if surprise:
        # عند الضغط على مفاجأة حب، عرض رسائل الشخص الآخر
        if user_id == OWNER_ID:
            # عمار يشوف رسائل رغد له
            messages = LOVE_SURPRISES_RAGHAD
        elif user_id == RAGHAD_ID:
            # رغد تشوف رسائل عمار لها
            messages = LOVE_SURPRISES_AMMAR
        else:
            messages = ["💕 أهلاً وسهلاً"]
    else:
        # الرسائل العادية تبقى نفس الشيء
        messages = GENERAL_LOVE_QUOTES

    return random.choice(messages)

# لا حاجة لهذه الدالة بعد الآن لأننا لا نستخدم MongoDB
