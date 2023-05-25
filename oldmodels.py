from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine

SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost/chatapp'
db = SQLAlchemy()
engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_size=10, max_overflow=20)

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    db.init_app(app)

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
    
class Message(db.Model):
    __tablename__ = 'messages'
    msg_id = db.Column(db.Integer, primary_key=True)
    incoming_msg_id = db.Column(db.String(255))
    outgoing_msg_id = db.Column(db.String(255))
    msg = db.Column(db.String(1000))