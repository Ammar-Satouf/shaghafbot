
from pymongo import MongoClient
from datetime import datetime
from config import MONGO_URI, DB_NAME, COLLECTION_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
memories = db[COLLECTION_NAME]


def add_memory(user_id, year, content):
    memory = {
        "user_id": user_id,
        "year": year,
        "content": content,
        "timestamp": datetime.utcnow()
    }
    memories.insert_one(memory)


def get_memories_by_year(user_id, year):
    return list(memories.find({"user_id": user_id, "year": year}))


def get_memories_by_month(user_id, year, month):
    """جلب الذكريات حسب الشهر"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    return list(memories.find({
        "user_id": user_id,
        "timestamp": {
            "$gte": start_date,
            "$lt": end_date
        }
    }).sort("timestamp", 1))


def get_memories_by_day(user_id, year, month, day):
    """جلب الذكريات حسب اليوم"""
    start_date = datetime(year, month, day)
    end_date = datetime(year, month, day, 23, 59, 59)
    
    return list(memories.find({
        "user_id": user_id,
        "timestamp": {
            "$gte": start_date,
            "$lte": end_date
        }
    }).sort("timestamp", 1))


def get_months_with_memories(user_id, year):
    """جلب الأشهر التي تحتوي على ذكريات في سنة معينة"""
    pipeline = [
        {"$match": {"user_id": user_id, "year": year}},
        {"$group": {
            "_id": {"$month": "$timestamp"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    return list(memories.aggregate(pipeline))


def get_days_with_memories(user_id, year, month):
    """جلب الأيام التي تحتوي على ذكريات في شهر معين"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    pipeline = [
        {"$match": {
            "user_id": user_id,
            "timestamp": {
                "$gte": start_date,
                "$lt": end_date
            }
        }},
        {"$group": {
            "_id": {"$dayOfMonth": "$timestamp"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    return list(memories.aggregate(pipeline))


def get_random_memory(user_id):
    pipeline = [{"$match": {"user_id": user_id}}, {"$sample": {"size": 1}}]
    result = list(memories.aggregate(pipeline))
    return result[0] if result else None


def add_special_memory(user_id, year, month, day, content, memory_type="special"):
    """إضافة ذكرى خاصة مع تاريخ محدد"""
    special_date = datetime(year, month, day)
    memory = {
        "user_id": user_id,
        "year": year,
        "content": content,
        "timestamp": special_date,
        "memory_type": memory_type,
        "is_special": True
    }
    # تحقق من وجود الذكرى لتجنب التكرار
    existing = memories.find_one({
        "user_id": user_id, 
        "memory_type": memory_type,
        "year": year,
        "timestamp": special_date
    })
    if not existing:
        memories.insert_one(memory)
        

def get_special_memories(user_id, memory_type=None):
    """جلب الذكريات الخاصة"""
    query = {"user_id": user_id, "is_special": True}
    if memory_type:
        query["memory_type"] = memory_type
    return list(memories.find(query).sort("timestamp", -1))
