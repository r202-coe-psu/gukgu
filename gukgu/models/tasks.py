import datetime

import mongoengine as me

# Record status per lab rules: active/inactive only (used for soft delete)
TASK_STATUS_CHOICES = [
    ("active", "ใช้งาน"),
    ("inactive", "ปิดการใช้งาน"),
]


class Task(me.Document):
    meta = {"collection": "tasks", "indexes": ["project", "assignee", "status"]}

    project = me.ReferenceField("Project", dbref=True, required=True)
    title = me.StringField(required=True, max_length=255)
    # Optional; views only accept members of the task's project
    assignee = me.ReferenceField("User", dbref=True)
    is_done = me.BooleanField(default=False)

    # Standard fields every model must have (see docs/04)
    status = me.StringField(
        required=True,
        default="active",
        choices=[s[0] for s in TASK_STATUS_CHOICES],
    )
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    creator = me.ReferenceField("User", dbref=True)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updater = me.ReferenceField("User", dbref=True)

    def display_status(self):
        return dict(TASK_STATUS_CHOICES).get(self.status, self.status)
