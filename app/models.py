from .extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user")                    #for user's roles
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<User {self.email}>"
    
class SkillCategory(db.Model):
    __tablename__ = "skill_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("skill_categories.id"), nullable=False)
    weight = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.relationship("SkillCategory", backref="skills")



class UserSkill(db.Model):
    __tablename__ = "user_skills"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"))

    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    user = db.relationship("User", backref="user_skills")
    skill = db.relationship("Skill")

class Goal(db.Model):
    __tablename__ = "goals"

    goal_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)

    target_hours_per_week = db.Column(db.Integer, nullable=False)

    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    status = db.Column(db.String(20), default="active")

    user = db.relationship("User", backref="goals")
    skill = db.relationship("Skill")

class Progress(db.Model):
    __tablename__ = "progress"
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'))

    hours_spent = db.Column(db.Float)

    date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')
    skill = db.relationship('Skill')