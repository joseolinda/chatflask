from models import db

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(255), unique=True)
    fname = db.Column(db.String(255))
    lname = db.Column(db.String(255))
    email = db.Column(db.String(255))
    password = db.Column(db.String(255))
    img = db.Column(db.Text())
    status = db.Column(db.String(255))