from flask import Flask, render_template, request, session, redirect, jsonify, url_for
from werkzeug.utils import secure_filename
from models import init_db
from controllers import UserController, MessageController

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'
app.config['UPLOAD_FOLDER'] = "static/images/"

# Instaciar o APP no SQLAlchemy
init_db(app)

@app.route('/')
def index():
    if 'unique_id' in session:
        return redirect('/chat')

    return render_template('index.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    return UserController.login()

@app.route('/signup', methods=["POST"])
def signup():
    return UserController.signup()

@app.route('/logout', methods=['GET'])
def logout():
    return UserController.logout()

@app.route('/chat')
def chat():
    return MessageController.chat()

@app.route('/chat/<int:user_id>', methods=["GET", "POST"])
def chat_with(user_id):
    return MessageController.chat_with(user_id)

@app.route('/send-message', methods=["POST"])
def send_message():
    return MessageController.send_message()

@app.route('/get-chat', methods=["POST"])
def get_chat():
    return MessageController.get_chat()

@app.route('/get-users', methods=['GET'])
def users():
    return UserController.get_users()

@app.route('/search-users', methods=["POST"])
def search_users():
    return UserController.search_users()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')