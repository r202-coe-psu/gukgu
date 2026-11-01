import datetime

import mongoengine as me

# Record status per lab rules: active/inactive only (used for soft delete)
PROJECT_STATUS_CHOICES = [
    ("active", "ใช้งาน"),
    ("inactive", "ปิดการใช้งาน"),
]

# Work stage, kept separate from status (sketch page 2)
PROJECT_STAGE_CHOICES = [
    ("open", "เปิดรับ"),
    ("doing", "กำลังทำ"),
    ("done", "เสร็จแล้ว"),
]

# Where the project comes from (sketch page 5)
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

    # Standard fields every model must have (see docs/04)
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
