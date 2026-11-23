from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, validators


class TaskForm(FlaskForm):
    title = StringField(
        "ชื่องานย่อย",
        [validators.InputRequired(), validators.Length(max=255)],
    )
    # Choices are set per project in the view; WTForms rejects any other value,
    # so a non-member id fails validation on the server
    assignee = SelectField(
        "คนรับผิดชอบ",
        choices=[("", "ไม่ระบุคนรับผิดชอบ")],
        validators=[validators.Optional()],
    )

    def set_assignee_choices(self, members):
        self.assignee.choices = [("", "ไม่ระบุคนรับผิดชอบ")] + [
            (str(member.id), member.get_fullname()) for member in members
        ]
