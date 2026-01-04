from extensions import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    age = db.Column(db.Integer)
    condition = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    user = db.relationship("User", backref=db.backref("profile", uselist=False))


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    nctid = db.Column(db.String(50), nullable=False)
    __table_args__ = (
        db.UniqueConstraint("user_id", "nctid", name="unique_user_trial"),
    )


class ClinicalTrial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nctid = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(300))
    condition = db.Column(db.String(200))
    phase = db.Column(db.String(50))
    status = db.Column(db.String(50))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    summary = db.Column(db.Text)
