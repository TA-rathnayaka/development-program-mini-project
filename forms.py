from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, EmailField, FloatField
from wtforms.validators import DataRequired, EqualTo


class LoginForm(FlaskForm):
    username = StringField(label="Username", validators=[DataRequired(message="Please enter your username")])
    password = PasswordField(label="Password", validators=[DataRequired(message="Please enter your password")])
    submit = SubmitField(label="Login")


class ComplaintForm(FlaskForm):
    latitude = FloatField(label="Latitude", default=0)
    longitude = FloatField(label="Longitude", default=0)
    image = FileField(label="Select Image")
    submit = SubmitField(label="Submit")


class RegistrationForm(FlaskForm):
    username = StringField(label="Username", validators=[DataRequired(message="Please enter your username")])
    email = EmailField(label="Email", validators=[DataRequired(message="Please enter your email")])
    password = PasswordField(label="Password", validators=[DataRequired(message="Please enter your password")])
    confirm_password = PasswordField(label="Confirm Password",
                                     validators=[EqualTo('password', message="Password must match")])
    submit = SubmitField(label="Create an Account")


class MunicipalForm(FlaskForm):
    municipal_council = StringField(label="Municipal Council name",
                                    validators=[DataRequired(message="Please enter your username")])
    email = EmailField(label="Email", validators=[DataRequired(message="Please enter your email")])
    latitude = FloatField(label="Latitude", validators=[DataRequired(message="Please enter your Latitude")])
    longitude = FloatField(label="Longitude", validators=[DataRequired(message="Please enter your Longitude")])
    submit = SubmitField(label="Add to Database")


class DeleteUserForm(FlaskForm):
    username = StringField(label="Username", validators=[DataRequired(message="Please enter your username")])
    submit = SubmitField(label="Remove from Database")


class DeleteMunicipalCouncilForm(FlaskForm):
    username = StringField(label="Municipal Council Name",
                           validators=[DataRequired(message="Please enter Municipal Council")])
    submit = SubmitField(label="Remove from Database")
