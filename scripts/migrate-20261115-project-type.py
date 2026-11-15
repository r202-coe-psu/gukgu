from gukgu import models
from gukgu.web.config import get_settings

models.init_mongoengine(get_settings())
collection = models.Project._get_collection()

# แปลงเฉพาะ document ที่ยังเป็นชื่อเก่า รันซ้ำแล้วจะไม่ทำอะไรเพิ่ม
result = collection.update_many(
    {"Type": {"$exists": True}, "project_type": {"$exists": False}},
    {"$rename": {"Type": "project_type"}},
)
print(f"เปลี่ยนชื่อ field แล้ว {result.modified_count} document")

if "Type_1" in collection.index_information():
    collection.drop_index("Type_1")
    print("ลบ index Type_1 แล้ว")