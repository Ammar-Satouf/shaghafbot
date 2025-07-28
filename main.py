import telebot
from telebot import types
import threading
from flask import Flask
from config import BOT_TOKEN, OWNER_ID, RAGHAD_ID, MONGO_URI, DATABASE_NAME, COLLECTION_NAME
from utils import is_authorized, get_user_name, get_love_message, calculate_love_duration
from datetime import datetime
import random
from pymongo import MongoClient
import time
import hashlib
import json

bot = telebot.TeleBot(BOT_TOKEN)

# نظام الحماية
SECURITY_HASH = hashlib.sha256(f"{BOT_TOKEN}{OWNER_ID}{RAGHAD_ID}".encode()).hexdigest()[:16]
user_sessions = {}

# MongoDB connection
mongo_client = None
db = None
memories_collection = None


def init_mongo():
    global mongo_client, db, memories_collection
    try:
        if MONGO_URI:
            mongo_client = MongoClient(MONGO_URI)
            # اختبار الاتصال
            mongo_client.admin.command('ping')
            db = mongo_client[DATABASE_NAME]
            memories_collection = db[COLLECTION_NAME]
            print("✅ اتصال MongoDB ناجح")
            print(f"📊 قاعدة البيانات: {DATABASE_NAME}")
            print(f"📁 المجموعة: {COLLECTION_NAME}")
            return True
        else:
            print("❌ MONGO_URI غير محدد")
            return False
    except Exception as e:
        print(f"❌ خطأ MongoDB: {e}")
        print("تأكد من صحة MONGO_URI في الـ Secrets")
        return False


init_mongo()

def security_check(user_id, chat_id):
    """فحص أمني بسيط للمستخدم"""
    current_time = time.time()
    
    # فحص صحة الجلسة فقط
    session_key = f"{user_id}_{chat_id}_{SECURITY_HASH}"
    session_hash = hashlib.md5(session_key.encode()).hexdigest()
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'hash': session_hash,
            'created': current_time,
            'requests': 1
        }
    else:
        user_sessions[user_id]['requests'] += 1
        # تجديد الجلسة كل ساعة
        if current_time - user_sessions[user_id]['created'] > 3600:
            user_sessions[user_id] = {
                'hash': session_hash,
                'created': current_time,
                'requests': 1
            }
    
    return True

def anti_forward_protection(message):
    """حماية من التحويل والنسخ بدون حظر"""
    # فحص التحويل المباشر
    if message.forward_from or message.forward_from_chat:
        return True
    
    # فحص الرد على رسائل محولة
    if message.reply_to_message:
        if message.reply_to_message.forward_from or message.reply_to_message.forward_from_chat:
            return True
    
    return False

def encrypt_content(content):
    """تشفير المحتوى"""
    if not content:
        return content
    
    # تشفير بسيط للمحتوى
    encrypted = ""
    for char in content:
        encrypted += chr((ord(char) + 7) % 1000 + 33)
    return encrypted

def decrypt_content(encrypted_content):
    """فك تشفير المحتوى"""
    if not encrypted_content:
        return encrypted_content
    
    try:
        decrypted = ""
        for char in encrypted_content:
            decrypted += chr((ord(char) - 7) % 1000 + 33)
        return decrypted
    except:
        return encrypted_content

def protection_watermark():
    """علامة مائية متقدمة للحماية"""
    import time
    timestamp = int(time.time())
    return f"\n\n🔒 محمي • لا تحول • لا تنسخ • {SECURITY_HASH[:6]}-{timestamp%1000}"

def anti_screenshot_protection():
    """نص خفي لمنع السكرينشوت"""
    # أحرف خفية وعلامات خاصة لتصعيب النسخ
    invisible_chars = "‌‍‎‏​‌‍‎‏"
    protection_text = ""
    for i, char in enumerate(invisible_chars):
        protection_text += char
        if i % 2 == 0:
            protection_text += "⠀"  # حرف برايل فارغ
    return protection_text

def get_random_love_emoji():
    """اختيار إيموجي حب عشوائي"""
    love_emojis = ["💕", "💖", "💗", "💝", "💞", "💓", "🤍", "❤️", "💜", "💙", "💚", "💛", "🧡", "💌", "💋", "😘", "🥰", "😍"]
    return random.choice(love_emojis)

def create_love_animation():
    """إنشاء أنيميشن قلوب متحركة"""
    hearts = ["💕", "💖", "💗", "💝", "💞", "💓"]
    animation = ""
    for i in range(5):
        animation += random.choice(hearts) + " "
    return animation

def get_romantic_quote():
    """اقتباسات رومانسية جميلة"""
    quotes = [
        "🌹 في عينيك أرى كل جمال العالم",
        "💫 حبك أضاء كل زوايا قلبي المظلمة",
        "🌸 معك أصبحت أفهم معنى الحب الحقيقي",
        "💎 أنت الكنز الذي بحثت عنه طوال حياتي",
        "🌙 تحت ضوء القمر، أهمس لك بأجمل كلمات الحب",
        "✨ حبنا قصة خيالية تُكتب بماء الذهب",
        "🦋 كالفراشة ترقص، كذلك قلبي عندما أراك"
    ]
    return random.choice(quotes)

def create_digital_rose_garden():
    """إنشاء حديقة ورود رقمية"""
    roses = "🌹🌺🌸🌻🌷🌼"
    garden = ""
    for i in range(3):
        garden += "".join(random.choice(roses) for _ in range(8)) + "\n"
    return garden

def love_compatibility_game():
    """لعبة توافق الحب"""
    compatibility = random.randint(85, 100)
    if compatibility >= 95:
        message = "💯 توافق مثالي! أنتما مخلوقان لبعضكما البعض"
    elif compatibility >= 90:
        message = "💫 توافق رائع! حبكما قوي كالجبال"
    else:
        message = "💕 توافق جميل! الحب بينكما ينمو كل يوم"
    
    return f"🎪 نتيجة لعبة الحب:\n\n{message}\n\n📊 نسبة التوافق: {compatibility}%"

def create_starry_night():
    """إنشاء ليلة مليئة بالنجوم"""
    stars = "⭐✨🌟💫⚡"
    night_sky = ""
    for i in range(4):
        night_sky += "".join(random.choice(stars) for _ in range(10)) + "\n"
    return night_sky

def hearts_map():
    """خريطة قلوب"""
    heart_map = """
    💖     💕     💗
💝    💫 أنتما 💫    💞
    💓     💘     💌
    """
    return heart_map

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


def save_memory_to_database(user_id, content, file_id=None, file_type=None):
    try:
        if memories_collection is None:
            print("❌ قاعدة البيانات غير متاحة")
            return False

        name = get_user_name(user_id)
        # تشفير المحتوى للحماية
        encrypted_content = encrypt_content(content) if content else content
        
        memory_data = {
            "user_id": user_id,
            "user_name": name,
            "content": encrypted_content,
            "file_id": file_id,
            "file_type": file_type,
            "timestamp": datetime.now(),
            "security_hash": SECURITY_HASH,
            "protected": True
        }
        
        result = memories_collection.insert_one(memory_data)
        print(f"✅ تم حفظ الذكرى المحمية بنجاح: {result.inserted_id}")
        return True
    except Exception as e:
        print(f"خطأ في حفظ الذكرى: {e}")
        return False


def get_random_memory():
    try:
        if memories_collection is None:
            return None

        total_memories = memories_collection.count_documents({"security_hash": SECURITY_HASH})
        if total_memories == 0:
            return None

        random_memory = list(
            memories_collection.aggregate([
                {"$match": {"security_hash": SECURITY_HASH}},
                {"$sample": {"size": 1}}
            ]))[0]
        
        # فك تشفير المحتوى
        if random_memory.get('content'):
            random_memory['content'] = decrypt_content(random_memory['content'])
        
        return random_memory

    except Exception as e:
        print(f"خطأ في جلب الذكرى: {e}")
        return None


def create_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("💝 إضافة ذكرى",
                                      callback_data="add_memory")
    btn2 = types.InlineKeyboardButton("🎁 ذكرى عشوائية",
                                      callback_data="get_memory")
    btn3 = types.InlineKeyboardButton("💕 ذكرى حبنا",
                                      callback_data="love_memory")
    btn4 = types.InlineKeyboardButton("⏰ عداد الحب",
                                      callback_data="love_counter")
    btn5 = types.InlineKeyboardButton("🌟 مفاجأة حب",
                                      callback_data="love_surprise")
    btn6 = types.InlineKeyboardButton("💌 رسالة حب يومية",
                                      callback_data="daily_love")
    btn7 = types.InlineKeyboardButton("🎵 أغنية حبنا",
                                      callback_data="love_song")
    btn8 = types.InlineKeyboardButton("🌹 باقة ورد رقمية",
                                      callback_data="digital_roses")
    btn9 = types.InlineKeyboardButton("💎 قصر الحب",
                                      callback_data="love_palace")
    btn10 = types.InlineKeyboardButton("🎪 لعبة الحب",
                                       callback_data="love_game")
    btn11 = types.InlineKeyboardButton("🌙 تحت النجوم",
                                       callback_data="under_stars")
    btn12 = types.InlineKeyboardButton("💫 خريطة قلوبنا",
                                       callback_data="hearts_map")

    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    markup.add(btn7, btn8)
    markup.add(btn9, btn10)
    markup.add(btn11, btn12)
    return markup


def create_start_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                       one_time_keyboard=False)
    btn = types.KeyboardButton("بحبك ❤️")
    markup.add(btn)
    return markup


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # فحص الحماية الأمنية
    security_check(user_id, chat_id)
    
    if not is_authorized(user_id):
        bot.send_message(chat_id, "🚫 هذا البوت محمي ومخصص للمستخدمين المصرح لهم فقط")
        return

    # فحص التحويل
    if anti_forward_protection(message):
        bot.send_message(chat_id, "🚫 لا يمكنك استخدام الرسائل المحولة")
        return

    name = get_user_name(user_id)
    love_msg = get_love_message(user_id)
    anti_copy = anti_screenshot_protection()
    animation = create_love_animation()
    current_time = datetime.now().strftime('%H:%M')
    welcome_text = f"✨ أهلاً وسهلاً {name} ✨{anti_copy}\n\n{animation}\n\n💫 مرحباً بك في بوت شغف السحري المحمي\n\n{love_msg}\n\n🕐 الوقت الآن: {current_time}\n💖 يوم جميل مع حبيبك\n\n🎪 اختر المغامرة التي تريدها:{protection_watermark()}"

    bot.send_message(chat_id,
                     welcome_text,
                     reply_markup=create_start_keyboard())
    bot.send_message(chat_id,
                     "💝 القائمة الرئيسية:",
                     reply_markup=create_main_keyboard())


@bot.message_handler(func=lambda message: message.text == "بحبك ❤️")
def love_button_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # فحص الحماية
    if not security_check(user_id, chat_id):
        return
    
    if not is_authorized(user_id):
        return

    if anti_forward_protection(message):
        bot.send_message(chat_id, "🚫 المحتوى محمي من التحويل")
        return

    name = get_user_name(user_id)
    love_msg = get_love_message(user_id, surprise=True)
    anti_copy = anti_screenshot_protection()
    response_text = f"💕 وانا كمان بحبك {name} 🌸{anti_copy}\n\n{love_msg}{protection_watermark()}"

    bot.send_message(chat_id,
                     response_text,
                     reply_markup=create_main_keyboard())


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    # فحص الحماية الأمنية
    security_check(user_id, chat_id)
    
    if not is_authorized(user_id):
        try:
            bot.answer_callback_query(call.id, "❌ محتوى محمي")
        except:
            pass
        return

    try:
        bot.answer_callback_query(call.id)
    except:
        pass

    try:
        if call.data == "add_memory":
            bot.edit_message_text(
                "💝 أرسل الذكرى:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🔙 رجوع",
                                               callback_data="back_main")))
            bot.register_next_step_handler(call.message, save_memory)

        elif call.data == "get_memory":
            random_memory = get_random_memory()

            if random_memory:
                try:
                    name = random_memory.get('user_name', 'مجهول')
                    content = random_memory.get('content', '')
                    timestamp = random_memory.get('timestamp', datetime.now())
                    formatted_timestamp = timestamp.strftime('%d/%m/%Y %H:%M')
                    
                    anti_copy = anti_screenshot_protection()
                    memory_text = f"🎁 ذكرى عشوائية محمية{anti_copy}\n\n💝 من {name}:\n{content}\n\n📅 {formatted_timestamp}{protection_watermark()}"
                    
                    file_id = random_memory.get('file_id')
                    file_type = random_memory.get('file_type')
                    
                    if file_id and file_type:
                        if file_type == 'photo':
                            bot.send_photo(call.message.chat.id, file_id, caption=memory_text)
                        elif file_type == 'video':
                            bot.send_video(call.message.chat.id, file_id, caption=memory_text)
                        elif file_type == 'document':
                            bot.send_document(call.message.chat.id, file_id, caption=memory_text)
                        elif file_type == 'voice':
                            bot.send_voice(call.message.chat.id, file_id, caption=memory_text)
                        elif file_type == 'video_note':
                            bot.send_video_note(call.message.chat.id, file_id)
                            bot.send_message(call.message.chat.id, memory_text)
                        elif file_type == 'sticker':
                            bot.send_sticker(call.message.chat.id, file_id)
                            bot.send_message(call.message.chat.id, memory_text)
                    else:
                        bot.send_message(call.message.chat.id, memory_text)
                    
                    bot.edit_message_text("🎁 تم عرض ذكرى عشوائية",
                                          call.message.chat.id,
                                          call.message.message_id,
                                          reply_markup=create_main_keyboard())
                except Exception as e:
                    print(f"خطأ في عرض الذكرى: {e}")
                    bot.edit_message_text("❌ خطأ في عرض الذكرى",
                                          call.message.chat.id,
                                          call.message.message_id,
                                          reply_markup=create_main_keyboard())
            else:
                bot.edit_message_text("📭 لا توجد ذكريات محفوظة",
                                      call.message.chat.id,
                                      call.message.message_id,
                                      reply_markup=create_main_keyboard())

        elif call.data == "love_memory":
            love_text = "💕 ذكرى حبنا 💕\n\n📅 6 تموز 2025\n💫 بداية قصة حبنا\n\n🌸 أحلى ذكرى بحياتنا"
            bot.edit_message_text(
                love_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🔙 رجوع",
                                               callback_data="back_main")))

        elif call.data == "love_counter":
            duration_text = calculate_love_duration()
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("🔄 تحديث",
                                           callback_data="love_counter"))
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع",
                                           callback_data="back_main"))
            bot.edit_message_text(duration_text,
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=markup)

        elif call.data == "love_surprise":
            name = get_user_name(user_id)
            surprise_msg = get_love_message(user_id, surprise=True)
            surprise_text = f"🌟 مفاجأة لـ {name} 🌟\n\n{surprise_msg}"

            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("💕 مفاجأة أخرى",
                                           callback_data="love_surprise"))
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع",
                                           callback_data="back_main"))
            bot.edit_message_text(surprise_text,
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=markup)

        elif call.data == "daily_love":
            name = get_user_name(user_id)
            quote = get_romantic_quote()
            animation = create_love_animation()
            anti_copy = anti_screenshot_protection()
            daily_text = f"💌 رسالة حب يومية لـ {name}{anti_copy}\n\n{quote}\n\n{animation}\n\n📅 {datetime.now().strftime('%d/%m/%Y')}{protection_watermark()}"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("💕 رسالة أخرى", callback_data="daily_love"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
            bot.edit_message_text(daily_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

        elif call.data == "love_song":
            name = get_user_name(user_id)
            song_lyrics = f"🎵 أغنية حبنا الخاصة 🎵\n\n🎼 يا {name} يا حبيبي\n🎶 قلبي بيدق اسمك\n🎵 حبك نور بعيوني\n🎶 وانت أحلى حلم\n\n🎭 كلمات: بوت شغف المحمي\n🎪 اللحن: نبضات القلب{protection_watermark()}"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔄 أغنية أخرى", callback_data="love_song"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
            bot.edit_message_text(song_lyrics, call.message.chat.id, call.message.message_id, reply_markup=markup)

        elif call.data == "digital_roses":
            name = get_user_name(user_id)
            garden = create_digital_rose_garden()
            emoji = get_random_love_emoji()
            roses_text = f"🌹 باقة ورد رقمية لـ {name} 🌹\n\n{garden}\n{emoji} باقة ورود من القلب {emoji}\n\n🎁 هدية خاصة من حبيبك{protection_watermark()}"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🌺 باقة جديدة", callback_data="digital_roses"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
            bot.edit_message_text(roses_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

        elif call.data == "love_palace":
            name = get_user_name(user_id)
            palace_text = f"💎 قصر الحب الخاص بـ {name} 💎\n\n🏰 أهلاً بك في قصر أحلامنا\n👑 هنا حيث يسكن الحب الأبدي\n💫 كل حجر فيه مبني من ذكرياتنا\n🌟 وكل نافذة تطل على مستقبلنا\n\n🗝️ المفتاح في قلبك دائماً{protection_watermark()}"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🚪 جولة في القصر", callback_data="love_palace"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
            bot.edit_message_text(palace_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

        elif call.data == "love_game":
            game_result = love_compatibility_game()
            emoji = get_random_love_emoji()
            game_text = f"{game_result}\n\n{emoji} شكراً لك على اللعب معي {emoji}{protection_watermark()}"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎮 لعب مرة أخرى", callback_data="love_game"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
            bot.edit_message_text(game_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

        elif call.data == "under_stars":
            name = get_user_name(user_id)
            stars = create_starry_night()
            stars_text = f"🌙 ليلة تحت النجوم مع {name} 🌙\n\n{stars}\n💫 في هذه الليلة الساحرة\n🌟 نجلس تحت النجوم المتلألئة\n✨ نحلم بمستقبل مشرق معاً\n🌠 وننظر إلى النجوم ونتمنى\n\n💕 أن يبقى حبنا أبدياً{protection_watermark()}"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🌠 تمني أمنية", callback_data="under_stars"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
            bot.edit_message_text(stars_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

        elif call.data == "hearts_map":
            name = get_user_name(user_id)
            map_display = hearts_map()
            hearts_text = f"💫 خريطة قلوبنا - {name} 💫\n\n{map_display}\n\n🗺️ هذه خريطة رحلة حبنا\n💖 كل قلب يمثل لحظة جميلة\n🧭 والاتجاه دائماً نحو بعضنا{protection_watermark()}"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔄 خريطة جديدة", callback_data="hearts_map"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
            bot.edit_message_text(hearts_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

        elif call.data == "back_main":
            name = get_user_name(user_id)
            love_msg = get_love_message(user_id)
            main_text = f"🤍 أهلاً {name}\n\n{love_msg}\n\nاختر ما تريد:"
            bot.edit_message_text(main_text,
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=create_main_keyboard())

    except Exception as e:
        print(f"خطأ في الاستدعاء: {e}")


def save_memory(message):
    """دالة لحفظ الذكرى من خلال زر إضافة ذكرى"""
    save_automatic_memory(message)
    bot.send_message(message.chat.id,
                     "✅ تم حفظ الذكرى 💝",
                     reply_markup=create_main_keyboard())


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

    save_memory_to_database(user_id, content, file_id, file_type)


# معالج جميع الرسائل العادية (ما عدا الأوامر والضغطات)
@bot.message_handler(content_types=[
    'text', 'photo', 'video', 'document', 'voice', 'video_note', 'sticker'
])
def handle_all_messages(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # فحص الحماية الأمنية
    security_check(user_id, chat_id)

    if not is_authorized(user_id):
        bot.send_message(chat_id, "🚫 هذا البوت محمي ومخصص للمستخدمين المصرح لهم فقط")
        return

    # فحص حماية من التحويل والنسخ
    if anti_forward_protection(message):
        warning_msg = f"🚫 المحتوى محمي من التحويل والنسخ{anti_screenshot_protection()}\n⚠️ يرجى إرسال محتوى أصلي"
        bot.send_message(chat_id, warning_msg)
        print(f"⚠️ محاولة تحويل من المستخدم {user_id}")
        return

    # تجاهل رسالة "بحبك" لأنها معالجة بشكل منفصل
    if message.text == "بحبك ❤️":
        return

    # حفظ تلقائي لأي رسالة ترسل مع التشفير
    name = get_user_name(user_id)
    save_automatic_memory(message)
    anti_copy = anti_screenshot_protection()
    bot.send_message(chat_id,
                     f"✅ تم حفظ الذكرى المحمية {name} 💝{anti_copy}{protection_watermark()}",
                     reply_markup=create_main_keyboard())


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
