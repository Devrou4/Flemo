from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flemo.models import User
from flask import flash
from flask_login import current_user
from flask_wtf.file import FileAllowed, FileRequired
from flask_ckeditor import CKEditorField


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(4, 12)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            flash('Username Taken!', 'danger')
            raise ValidationError('Username Taken')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            flash('Email Taken!', 'danger')
            raise ValidationError('Email Taken')


class LoginForm(FlaskForm):

    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

    submit = SubmitField('Login')


class TaskForm(FlaskForm):

    task = StringField('Task', validators=[DataRequired()])

    add = SubmitField('Add')


class UpdateAccount(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(4, 12)])
    email = StringField('Email', validators=[DataRequired(), Email()])

    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                flash('Username Taken!', 'danger')
                raise ValidationError('Username Taken')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                flash('Email Taken!', 'danger')
                raise ValidationError('Email Taken')


class NoteField(FlaskForm):

    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Note', validators=[DataRequired()])
    # content = CKEditorField('Note')
    submit = SubmitField('Save')


class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


class PhotoForm(FlaskForm):
    file = FileField('Upload File', validators=[FileRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Submit')
