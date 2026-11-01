import datetime

import mongoengine as me

# สถานะตามกฎแล็บ: ใช้แค่เปิด/ปิด (soft delete)
PROJECT_STATUS_CHOICES = [
    ("active", "ใช้งาน"),
    ("inactive", "ปิดการใช้งาน"),
]

# ขั้นของงาน ตามภาพร่างหน้า 2
PROJECT_STAGE_CHOICES = [
    ("open", "เปิดรับ"),
    ("doing", "กำลังทำ"),
    ("done", "เสร็จแล้ว"),
]

# โปรเจกต์มาจากไหน ตามภาพร่างหน้า 5
PROJECT_SOURCE_CHOICES = [
    ("department", "ภาควิชา"),
    ("external", "ภายนอก"),
]


class Project(me.Document):
    meta = {"collection": "projects", "indexes": ["name", "status", "stage"]}

    name = me.StringField(required=True, max_length=255)
    description = me.StringField(default="")
    source = me.StringField(
        default="department", choices=[s[0] for s in PROJECT_SOURCE_CHOICES]
    )
    stage = me.StringField(
        default="open", choices=[s[0] for s in PROJECT_STAGE_CHOICES]
    )
    deadline = me.DateTimeField()
    members = me.ListField(me.ReferenceField("User", dbref=True))

    # ช่องมาตรฐานที่ทุก model ต้องมี (ตาม docs/04)
    status = me.StringField(
        required=True,
        default="active",
        choices=[s[0] for s in PROJECT_STATUS_CHOICES],
    )
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    creator = me.ReferenceField("User", dbref=True)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updater = me.ReferenceField("User", dbref=True)

    def display_status(self):
        return dict(PROJECT_STATUS_CHOICES).get(self.status, self.status)

    def display_stage(self):
        return dict(PROJECT_STAGE_CHOICES).get(self.stage, self.stage)

    def display_source(self):
        return dict(PROJECT_SOURCE_CHOICES).get(self.source, self.source)