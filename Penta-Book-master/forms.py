from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm = PasswordField('Confirm Password',
                            validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    dob = StringField('Date of Birth', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    buyer_address = StringField('Address', validators=[DataRequired()])
    submit = SubmitField('Register')


class ShopRegisterForm(FlaskForm):
    shop_name = StringField('Shop Name', validators=[DataRequired(), Length(min=2, max=20)])
    owner_name = StringField('Owner Name', validators=[DataRequired(), Length(min=2, max=20)])
    shop_phone = StringField('Shop Phone', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    shop_address = StringField('Shop Address', validators=[DataRequired()])
    shop_email = StringField('Email', validators=[DataRequired(), Email()])
    shop_description = StringField('Description', validators=[DataRequired()])
    submit = SubmitField('Register as Shop')

class ShopLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')