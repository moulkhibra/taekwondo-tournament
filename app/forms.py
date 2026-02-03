from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SelectField, DateField, SubmitField, TextAreaField, PasswordField, BooleanField, DateTimeField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError, Email, EqualTo
from app.models import Player, Tournament, TournamentType, Gender, AgeGroup, WeightCategory, User
from datetime import date

class TournamentForm(FlaskForm):
    name = StringField('Tournament Name', validators=[DataRequired(), Length(min=3, max=100)])
    date = DateField('Tournament Date', validators=[DataRequired()], default=date.today)
    location = StringField('Location', validators=[DataRequired(), Length(min=3, max=200)])
    tournament_type = SelectField('Tournament Type', choices=[
        (TournamentType.KYOURGI.value, 'Kyourgi (Fighting)'),
        (TournamentType.POOMSAE.value, 'Poomsae (Forms)')
    ], validators=[DataRequired()])
    submit = SubmitField('Create Tournament')

class PlayerForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    club = StringField('Club', validators=[DataRequired(), Length(min=2, max=100)])
    gender = SelectField('Gender', choices=[
        (Gender.MALE.value, 'Male'),
        (Gender.FEMALE.value, 'Female')
    ], validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=10, max=80)])
    weight = FloatField('Weight (kg)', validators=[NumberRange(min=20, max=150)])
    tournament_id = SelectField('Tournament', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Player')

    def __init__(self, *args, **kwargs):
        super(PlayerForm, self).__init__(*args, **kwargs)
        self.tournament_id.choices = [(t.id, t.name) for t in Tournament.query.order_by(Tournament.name).all()]

class CategoryFilterForm(FlaskForm):
    gender = SelectField('Gender', choices=[
        ('', 'All Genders'),
        (Gender.MALE.value, 'Male'),
        (Gender.FEMALE.value, 'Female')
    ])
    age_group = SelectField('Age Group', choices=[
        ('', 'All Age Groups'),
        (AgeGroup.CADET.value, 'Cadet (14-17)'),
        (AgeGroup.JUNIOR.value, 'Junior (18-34)'),
        (AgeGroup.SENIOR.value, 'Senior (35+)')
    ])
    weight_category = SelectField('Weight Category', choices=[
        ('', 'All Weights'),
        (WeightCategory.LIGHT.value, 'Light (-68kg)'),
        (WeightCategory.MIDDLE.value, 'Middle (68-80kg)'),
        (WeightCategory.HEAVY.value, 'Heavy (+80kg)')
    ])
    submit = SubmitField('Filter Players')

class DrawForm(FlaskForm):
    tournament_id = SelectField('Tournament', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Generate Draw')

    def __init__(self, *args, **kwargs):
        super(DrawForm, self).__init__(*args, **kwargs)
        self.tournament_id.choices = [(t.id, f"{t.name} ({t.tournament_type.value.title()})") 
                                     for t in Tournament.query.order_by(Tournament.name).all()]

# Authentication Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    role = SelectField('Role', choices=[
        ('spectator', 'Spectator'),
        ('staff', 'Staff'),
        ('referee', 'Referee'),
        ('admin', 'Administrator')
    ], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class UserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    role = SelectField('Role', choices=[
        ('spectator', 'Spectator'),
        ('staff', 'Staff'),
        ('referee', 'Referee'),
        ('admin', 'Administrator')
    ], validators=[DataRequired()])
    is_active_user = BooleanField('Active')
    submit = SubmitField('Update User')

# Scoring Forms
class KyourgiScoreForm(FlaskForm):
    player1_points = IntegerField('Player 1 Points', validators=[NumberRange(min=0)], default=0)
    player1_warnings = IntegerField('Player 1 Warnings', validators=[NumberRange(min=0)], default=0)
    player1_deductions = IntegerField('Player 1 Deductions', validators=[NumberRange(min=0)], default=0)
    
    player2_points = IntegerField('Player 2 Points', validators=[NumberRange(min=0)], default=0)
    player2_warnings = IntegerField('Player 2 Warnings', validators=[NumberRange(min=0)], default=0)
    player2_deductions = IntegerField('Player 2 Deductions', validators=[NumberRange(min=0)], default=0)
    
    submit = SubmitField('Update Score')

class PoomsaeScoreForm(FlaskForm):
    player1_accuracy = FloatField('Player 1 Accuracy Score', validators=[NumberRange(min=0, max=10)], default=0.0)
    player1_presentation = FloatField('Player 1 Presentation Score', validators=[NumberRange(min=0, max=10)], default=0.0)
    
    player2_accuracy = FloatField('Player 2 Accuracy Score', validators=[NumberRange(min=0, max=10)], default=0.0)
    player2_presentation = FloatField('Player 2 Presentation Score', validators=[NumberRange(min=0, max=10)], default=0.0)
    
    submit = SubmitField('Update Score')

# Scheduling Forms
class MatchScheduleForm(FlaskForm):
    scheduled_time = DateTimeField('Scheduled Time', validators=[DataRequired()], format='%Y-%m-%d %H:%M')
    ring_number = IntegerField('Ring Number', validators=[NumberRange(min=1)])
    referee_id = SelectField('Referee', coerce=int)
    estimated_duration = IntegerField('Duration (minutes)', validators=[NumberRange(min=5, max=60)], default=15)
    submit = SubmitField('Schedule Match')

    def __init__(self, *args, **kwargs):
        super(MatchScheduleForm, self).__init__(*args, **kwargs)
        from app.models import User, UserRole
        self.referee_id.choices = [(0, 'No Referee')] + [(u.id, u.full_name) 
                                   for u in User.query.filter_by(role=UserRole.REFEREE.value).filter_by(is_active_user=True).all()]