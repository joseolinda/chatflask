from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine

SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost/chatapp'
db = SQLAlchemy()
engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_size=10, max_overflow=20)

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    db.init_app(app)