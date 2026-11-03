import datetime

import mongoengine as me

PROJECT_STATUS_CHOICES = [
    ("active", "ใช้งาน"),
    ("inactive", "ปิดการใช้งาน"),
]

PROJECT_STAGE_CHOICES = [
    ("open", "เปิดรับ"),
    ("in_progress", "กำลังทำ"),
    ("done", "เสร็จ"),
    ("stay", "พักไว้"),
]

PROJECT_SOURCE_CHOICES = [
    ("department", "ภาควิชา"),
    ("external", "ภายนอก"),
    ("grant", "ทุนวิจัย"),
]

PROJECT_TYPE_CHOICES = [
    ("AI/LLM", "Ai/LLM"),
    ("Cybersecurity", "Cybersecurity"),
    ("IOT", "IOT"),
    ("DevOps", "DevOps")
]



class Project(me.Document):
    meta = {
        "collection": "projects",
        "indexes": ["name", "status", "stage", "source", "Type"],
    }

    name = me.StringField(required=True, max_length=255)
    advisor = me.StringField(default="", max_length=255)
    description = me.StringField(default="")

    source = me.StringField(
        required=True,
        default="department",
        choices=[source[0] for source in PROJECT_SOURCE_CHOICES],
    )
    stage = me.StringField(
        required=True,
        default="open",
        choices=[stage[0] for stage in PROJECT_STAGE_CHOICES],
    )
    Type = me.StringField(
        required=True,
        default="type",
        choices=[stage[0] for stage in PROJECT_TYPE_CHOICES],
    )
    progress = me.IntField(required=True, default=0, min_value=0, max_value=100)
    deadline = me.DateField()
    members = me.ListField(me.StringField(max_length=255))

    status = me.StringField(
        required=True,
        default="active",
        choices=[status[0] for status in PROJECT_STATUS_CHOICES],
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
    
    def display_type(self):
        return dict(PROJECT_TYPE_CHOICES).get(self.Type, self.Type)