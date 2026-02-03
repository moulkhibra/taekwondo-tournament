from app import db
from datetime import datetime
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class TournamentType(Enum):
    KYOURGI = "kyourgi"
    POOMSAE = "poomsae"

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"

class AgeGroup(Enum):
    CADET = "cadet"      # 14-17 years
    JUNIOR = "junior"    # 18-34 years  
    SENIOR = "senior"    # 35+ years

class WeightCategory(Enum):
    LIGHT = "light"      # -68kg
    MIDDLE = "middle"    # 68-80kg
    HEAVY = "heavy"      # +80kg

class UserRole(Enum):
    ADMIN = "admin"
    REFEREE = "referee"
    STAFF = "staff"
    SPECTATOR = "spectator"

class MatchStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    tournament_type = db.Column(db.Enum(TournamentType), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    players = db.relationship('Player', backref='tournament', lazy=True, cascade='all, delete-orphan')
    matches = db.relationship('Match', backref='tournament', lazy=True, cascade='all, delete-orphan')

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    club = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.Enum(Gender), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float)  # Only for Kyourgi
    age_group = db.Column(db.Enum(AgeGroup), nullable=False)
    weight_category = db.Column(db.Enum(WeightCategory))
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    matches_as_player1 = db.relationship('Match', foreign_keys='Match.player1_id', backref='player1', lazy=True)
    matches_as_player2 = db.relationship('Match', foreign_keys='Match.player2_id', backref='player2', lazy=True)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_number = db.Column(db.Integer, nullable=False)
    match_number = db.Column(db.Integer, nullable=False)
    player1_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)
    player2_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)
    is_bye = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    category_key = db.Column(db.String(100), nullable=False)  # Computed category for grouping
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Utility method to get category key for player
    @staticmethod
    def get_category_key(player, tournament_type):
        if tournament_type == TournamentType.KYOURGI:
            return f"{player.gender.value}_{player.age_group.value}_{player.weight_category.value}"
        else:  # POOMSAE
            return f"{player.gender.value}_{player.age_group.value}"

    # Method to get the opponent player
    def get_opponent(self, player):
        if self.player1_id == player.id:
            from app import db
            return db.session.get(Player, self.player2_id) if self.player2_id else None
        elif self.player2_id == player.id:
            from app import db
            return db.session.get(Player, self.player1_id) if self.player1_id else None
        return None

    # Method to determine if player has a bye
    def has_bye(self, player):
        return self.is_bye and (self.player1_id == player.id or self.player2_id == player.id)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.SPECTATOR)
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    matches_refereed = db.relationship('MatchSchedule', backref='referee', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def is_referee(self):
        return self.role == UserRole.REFEREE
    
    def can_manage_tournaments(self):
        return self.role in [UserRole.ADMIN, UserRole.STAFF]
    
    def can_score_matches(self):
        return self.role in [UserRole.ADMIN, UserRole.REFEREE]
    
    def is_user_active(self):
        return self.is_active_user

class MatchSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    referee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    scheduled_time = db.Column(db.DateTime, nullable=True)
    ring_number = db.Column(db.Integer, nullable=True)
    estimated_duration = db.Column(db.Integer, default=15)  # minutes
    status = db.Column(db.Enum(MatchStatus), default=MatchStatus.SCHEDULED)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    match = db.relationship('Match', backref=db.backref('schedule', uselist=False))

class JudgeScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_score_id = db.Column(db.Integer, db.ForeignKey('match_score.id'), nullable=False)
    judge_number = db.Column(db.Integer, nullable=False)  # 1-5
    accuracy = db.Column(db.Float, default=0.0)  # Accuracy score
    presentation = db.Column(db.Float, default=0.0)  # Presentation score
    total = db.Column(db.Float, default=0.0)  # Total score for this judge
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    match_score = db.relationship('MatchScore', back_populates='judge_scores', lazy=True)
    
    def calculate(self):
        """Calculate total score for this judge"""
        self.total = self.accuracy + self.presentation
        return self.total

class MatchScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    
    # Scoring for Kyourgi
    points = db.Column(db.Integer, default=0)
    warnings = db.Column(db.Integer, default=0)
    deductions = db.Column(db.Integer, default=0)
    
    # Scoring for Poomsae
    accuracy_score = db.Column(db.Float, default=0.0)
    presentation_score = db.Column(db.Float, default=0.0)
    total_score = db.Column(db.Float, default=0.0)
    
    # Metadata
    scored_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    judge_scores = db.relationship(
        'JudgeScore',
        back_populates='match_score',
        lazy=True,
        cascade="all, delete-orphan"
    )
    match = db.relationship('Match', backref=db.backref('scores', lazy=True))
    player = db.relationship('Player', backref=db.backref('match_scores', lazy=True))
    scorer = db.relationship('User', backref=db.backref('scores_recorded', lazy=True))
    
    def calculate_total_score(self):
        """Calculate total score for Poomsae (legacy method)"""
        if self.match.tournament.tournament_type == TournamentType.POOMSAE:
            self.total_score = self.accuracy_score + self.presentation_score
        return self.total_score
    
    def calculate_final_poomsae_score(self):
        """Calculate final Poomsae score using WT 5-judge system"""
        if len(self.judge_scores) != 5:
            raise ValueError("Need exactly 5 judge scores for WT calculation")
        
        # Calculate each judge's total
        for judge_score in self.judge_scores:
            judge_score.calculate()
        
        # Get all judge totals
        totals = [j.total for j in self.judge_scores]
        
        # Remove highest and lowest scores
        if len(totals) >= 3:
            sorted_totals = sorted(totals)
            middle_three = sorted_totals[1:4]  # Remove highest (last) and lowest (first)
            final_avg = sum(middle_three) / 3
            self.total_score = round(final_avg, 2)
        else:
            # Fallback if less than 3 scores
            self.total_score = round(sum(totals) / len(totals), 2) if totals else 0.0
        
        return self.total_score