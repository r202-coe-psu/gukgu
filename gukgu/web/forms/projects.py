from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, TextAreaField, validators

from gukgu.models.projects import PROJECT_SOURCE_CHOICES, PROJECT_STAGE_CHOICES


class ProjectForm(FlaskForm):
    name = StringField(
        "ชื่อโปรเจกต์",
        [validators.InputRequired(), validators.Length(max=255)],
    )
    source = SelectField("มาจาก", choices=PROJECT_SOURCE_CHOICES)
    stage = SelectField("ขั้นของงาน", choices=PROJECT_STAGE_CHOICES)
    description = TextAreaField("รายละเอียด", [validators.Optional()])
    deadline = DateField("กำหนดส่ง", [validators.Optional()])


class SearchProjectForm(FlaskForm):
    class Meta:
        csrf = False

    search = StringField(
        "ค้นหาโปรเจกต์",
        [validators.Optional(), validators.Length(max=64)],
    )
    # Empty value means "all stages"; rendered as filter tabs on the index page
    stage = SelectField(
        "ขั้นของงาน",
        choices=[("", "ทั้งหมด")] + PROJECT_STAGE_CHOICES,
        validators=[validators.Optional()],
    )
