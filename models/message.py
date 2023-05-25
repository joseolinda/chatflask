from models import db

class Message(db.Model):
    __tablename__ = 'messages'
    msg_id = db.Column(db.Integer, primary_key=True)
    incoming_msg_id = db.Column(db.String(255))
    outgoing_msg_id = db.Column(db.String(255))
    msg = db.Column(db.String(1000))