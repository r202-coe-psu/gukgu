from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    FieldList,
    HiddenField,
    SelectField,
    StringField,
    TextAreaField,
    validators,
)

from gukgu.models import PROJECT_SOURCE_CHOICES, PROJECT_STAGE_CHOICES


class ProjectForm(FlaskForm):
    name = StringField(
        "ชื่อโปรเจกต์",
        [validators.InputRequired(), validators.Length(max=255)],
    )
    advisor = StringField(
        "อาจารย์ที่ปรึกษา",
        [validators.Optional(), validators.Length(max=255)],
    )
    source = SelectField(
        "ที่มา", [validators.InputRequired()], choices=PROJECT_SOURCE_CHOICES
    )
    stage = SelectField(
        "สถานะ", [validators.InputRequired()], choices=PROJECT_STAGE_CHOICES
    )
    description = TextAreaField("รายละเอียด", [validators.Optional()])
    members = FieldList(
        StringField("ชื่อสมาชิก", [validators.Optional(), validators.Length(max=255)]),
        label="สมาชิก",
        min_entries=1,
    )
    deadline = DateField("กำหนดเสร็จ", [validators.Optional()])
    


class SearchProjectForm(FlaskForm):
    class Meta:
        csrf = False

    search = StringField("ค้นหา", [validators.Optional(), validators.Length(max=64)])
    source = SelectField(
        "ที่มา",
        [validators.Optional()],
        choices=[("", "ที่มา: ทุกแหล่งที่มา")]
        + [(value, f"ที่มา: {label}") for value, label in PROJECT_SOURCE_CHOICES],
    )
    stage = HiddenField("สถานะ", [validators.Optional()])