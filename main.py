import telebot
from telebot import types
import threading
from flask import Flask
from config import BOT_TOKEN, OWNER_ID, RAGHAD_ID, CHANNEL_ID, MONGO_URI, DATABASE_NAME, COLLECTION_NAME
from utils import is_authorized, get_user_name, get_love_message, calculate_love_duration
from datetime import datetime
import random
from pymongo import MongoClient

bot = telebot.TeleBot(BOT_TOKEN)

# MongoDB connection
mongo_client = None
db = None
memories_collection = None

def init_mongo():
    global mongo_client, db, memories_collection
    try:
        if MONGO_URI:
            mongo_client = MongoClient(MONGO_URI)
            db = mongo_client[DATABASE_NAME]
            memories_collection = db[COLLECTION_NAME]
            print("✅ اتصال MongoDB ناجح")
            return True
        else:
            print("❌ MONGO_URI غير محدد")
            return False
    except Exception as e:
        print(f"❌ خطأ MongoDB: {e}")
        return False

init_mongo()

# Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "🤍 بوت شغف يعمل!"

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

def save_memory_to_channel(user_id, content, file_id=None, file_type=None):
    try:
        name = get_user_name(user_id)
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        channel_text = f"💝 ذكرى من {name}\n\n{content}\n\n📅 {timestamp}"

        sent_message = None
        if file_id and file_type:
            if file_type == 'photo':
                sent_message = bot.send_photo(CHANNEL_ID, file_id, caption=channel_text)
            elif file_type == 'video':
                sent_message = bot.send_video(CHANNEL_ID, file_id, caption=channel_text)
            elif file_type == 'document':
                sent_message = bot.send_document(CHANNEL_ID, file_id, caption=channel_text)
            elif file_type == 'voice':
                sent_message = bot.send_voice(CHANNEL_ID, file_id, caption=channel_text)
            elif file_type == 'video_note':
                sent_message = bot.send_video_note(CHANNEL_ID, file_id)
                bot.send_message(CHANNEL_ID, channel_text)
            elif file_type == 'sticker':
                sent_message = bot.send_sticker(CHANNEL_ID, file_id)
                bot.send_message(CHANNEL_ID, channel_text)
        else:
            sent_message = bot.send_message(CHANNEL_ID, channel_text)

        # حفظ في قاعدة البيانات إذا كانت متاحة
        if sent_message and memories_collection is not None:
            memory_data = {
                "message_id": sent_message.message_id,
                "user_id": user_id,
                "user_name": name,
                "content": content,
                "file_id": file_id,
                "file_type": file_type,
                "timestamp": datetime.now(),
                "channel_id": CHANNEL_ID
            }
            memories_collection.insert_one(memory_data)

        return True
    except Exception as e:
        print(f"خطأ في حفظ الذكرى: {e}")
        return False

def get_random_memory():
    try:
        if memories_collection is None:
            return None

        total_memories = memories_collection.count_documents({})
        if total_memories == 0:
            return None

        random_memory = list(memories_collection.aggregate([{"$sample": {"size": 1}}]))[0]
        return random_memory

    except Exception as e:
        print(f"خطأ في جلب الذكرى: {e}")
        return None

def create_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("💝 إضافة ذكرى", callback_data="add_memory")
    btn2 = types.InlineKeyboardButton("🎁 ذكرى عشوائية", callback_data="get_memory")
    btn3 = types.InlineKeyboardButton("💕 ذكرى حبنا", callback_data="love_memory")
    btn4 = types.InlineKeyboardButton("⏰ عداد الحب", callback_data="love_counter")
    btn5 = types.InlineKeyboardButton("🌟 مفاجأة", callback_data="love_surprise")

    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5)
    return markup

def create_start_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn = types.KeyboardButton("بحبك ❤️")
    markup.add(btn)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        bot.send_message(message.chat.id, "🚫 هذا البوت خاص")
        return

    name = get_user_name(user_id)
    love_msg = get_love_message(user_id)
    welcome_text = f"أهلاً {name} 🤍\n\n💫 مرحباً بك في بوت شغف\n\n{love_msg}\n\nاختر ما تريد:"

    bot.send_message(message.chat.id, welcome_text, reply_markup=create_start_keyboard())
    bot.send_message(message.chat.id, "💝 القائمة الرئيسية:", reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "بحبك ❤️")
def love_button_handler(message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return

    name = get_user_name(user_id)
    love_msg = get_love_message(user_id, surprise=True)
    response_text = f"💕 وانا كمان بحبك {name} 🌸\n\n{love_msg}"

    bot.send_message(message.chat.id, response_text, reply_markup=create_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    if not is_authorized(user_id):
        try:
            bot.answer_callback_query(call.id, "❌ غير مسموح")
        except:
            pass
        return

    try:
        bot.answer_callback_query(call.id)
    except:
        pass

    try:
        if call.data == "add_memory":
            bot.edit_message_text("💝 أرسل الذكرى:", 
                                call.message.chat.id, call.message.message_id,
                                reply_markup=types.InlineKeyboardMarkup().add(
                                    types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main")))
            bot.register_next_step_handler(call.message, save_memory)

        elif call.data == "get_memory":
            random_memory = get_random_memory()

            if random_memory:
                try:
                    # تحويل الرسالة من القناة
                    bot.forward_message(call.message.chat.id, CHANNEL_ID, random_memory['message_id'])
                    bot.edit_message_text(f"🎁 ذكرى عشوائية", 
                                        call.message.chat.id, call.message.message_id,
                                        reply_markup=create_main_keyboard())
                except Exception as e:
                    print(f"خطأ في تحويل الرسالة: {e}")
                    bot.edit_message_text("❌ لا توجد ذكريات محفوظة", 
                                        call.message.chat.id, call.message.message_id,
                                        reply_markup=create_main_keyboard())
            else:
                bot.edit_message_text("📭 لا توجد ذكريات محفوظة", 
                                    call.message.chat.id, call.message.message_id,
                                    reply_markup=create_main_keyboard())

        elif call.data == "love_memory":
            love_text = "💕 ذكرى حبنا 💕\n\n📅 6 تموز 2025\n💫 بداية قصة حبنا\n\n🌸 أحلى ذكرى بحياتنا"
            bot.edit_message_text(love_text, call.message.chat.id, call.message.message_id,
                                reply_markup=types.InlineKeyboardMarkup().add(
                                    types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main")))

        elif call.data == "love_counter":
            duration_text = calculate_love_duration()
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="love_counter"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
            bot.edit_message_text(duration_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

        elif call.data == "love_surprise":
            name = get_user_name(user_id)
            surprise_msg = get_love_message(user_id, surprise=True)
            surprise_text = f"🌟 مفاجأة لـ {name} 🌟\n\n{surprise_msg}"

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("💕 مفاجأة أخرى", callback_data="love_surprise"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
            bot.edit_message_text(surprise_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

        elif call.data == "back_main":
            name = get_user_name(user_id)
            love_msg = get_love_message(user_id)
            main_text = f"🤍 أهلاً {name}\n\n{love_msg}\n\nاختر ما تريد:"
            bot.edit_message_text(main_text, call.message.chat.id, call.message.message_id, reply_markup=create_main_keyboard())

    except Exception as e:
        print(f"خطأ في الاستدعاء: {e}")

def save_memory(message):
    """دالة لحفظ الذكرى من خلال زر إضافة ذكرى"""
    save_automatic_memory(message)
    bot.send_message(message.chat.id, "✅ تم حفظ الذكرى 💝", reply_markup=create_main_keyboard())

def save_automatic_memory(message):
    """دالة مساعدة لحفظ أي نوع من المحتوى"""
    user_id = message.from_user.id
    content = ""
    file_id = None
    file_type = None

    if message.text:
        content = message.text
    elif message.photo:
        content = message.caption or "📸"
        file_id = message.photo[-1].file_id
        file_type = 'photo'
    elif message.video:
        content = message.caption or "🎥"
        file_id = message.video.file_id
        file_type = 'video'
    elif message.document:
        content = message.caption or "📄"
        file_id = message.document.file_id
        file_type = 'document'
    elif message.voice:
        content = "🎤"
        file_id = message.voice.file_id
        file_type = 'voice'
    elif message.video_note:
        content = "⭕"
        file_id = message.video_note.file_id
        file_type = 'video_note'
    elif message.sticker:
        content = "😊"
        file_id = message.sticker.file_id
        file_type = 'sticker'

    save_memory_to_channel(user_id, content, file_id, file_type)

# معالج جميع الرسائل العادية (ما عدا الأوامر والضغطات)
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'voice', 'video_note', 'sticker'])
def handle_all_messages(message):
    user_id = message.from_user.id

    if not is_authorized(user_id):
        bot.send_message(message.chat.id, "🚫 هذا البوت خاص")
        return

    # تجاهل رسالة "بحبك" لأنها معالجة بشكل منفصل
    if message.text == "بحبك ❤️":
        return

    # حفظ تلقائي لأي رسالة ترسل
    name = get_user_name(user_id)
    save_automatic_memory(message)
    bot.send_message(message.chat.id, f"✅ تم حفظ الذكرى {name} 💝", reply_markup=create_main_keyboard())

if __name__ == "__main__":
    print("🤍 بوت شغف بدأ العمل...")
    try:
        import signal
        import os

        def signal_handler(sig, frame):
            print("🔴 إيقاف البوت...")
            if mongo_client:
                mongo_client.close()
            exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        bot.infinity_polling(none_stop=True, interval=2, timeout=60)
    except Exception as e:
        print(f"خطأ في تشغيل البوت: {e}")
