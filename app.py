from flask import Flask, render_template, request, session, redirect, jsonify, url_for
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine
import random, base64, hashlib, time, os

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

app.config['UPLOAD_FOLDER'] = "static/images/"
# Configure a conexão com o banco de dados
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://root@localhost/chatapp'
db = SQLAlchemy(app)
engine = create_engine("mysql+pymysql://root@localhost/chatapp", pool_size=10, max_overflow=20)

@app.route('/')
def index():
    if 'unique_id' in session:
        return redirect('/chat')
    
    return render_template('index.html')
    
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user:
            if user.password == hashlib.md5(password.encode()).hexdigest():
                session["unique_id"] = user.unique_id
                status = "Active now"
                sql = f"UPDATE users SET status = '{status}' WHERE unique_id = {user.unique_id}"
                with engine.connect() as conn:
                    conn.execute(text(sql))
                    conn.close()
                return 'success'
        return 'Email or password is incorrect!'
    else:
        return render_template('login.html')

@app.route('/signup', methods=["POST"])
def signup():    
    fname = request.form["fname"]
    lname = request.form["lname"]
    email = request.form["email"]
    password = request.form["password"]

    if fname and lname and email and password:
        if '@' in email:  # Verifica se o email é válido (pode ser aprimorado)
            user = User.query.filter_by(email=email).first()
            if user:
                return f"{email} - This email already exists!"
            else:
                image = request.files["image"]
                if image:
                    img_name = image.filename
                    img_ext = img_name.split('.')[-1].lower()
                    if img_ext in ["jpeg", 'png', 'jpg']:
                        sname = secure_filename(image.filename)
                        path = os.path.join(app.config['UPLOAD_FOLDER'], sname)
                        image.save(path)
                        image.close()   
                        user = User(
                            unique_id=int(time.time())+random.randint(1, 1000000),
                            fname=fname,
                            lname=lname,
                            email=email,
                            password=hashlib.md5(password.encode()).hexdigest(),
                            img=sname,
                            status='Active now'
                        )
                        try:
                            db.session.add(user)
                            db.session.commit()
                            session["unique_id"] = user.unique_id
                            db.session.close()
                            return 'success'
                        except Exception as e:
                            print('Failed to upload to ftp: '+ str(e))
                            return 'Falha ao salvar o usuário no banco de dados!\n'+str(e)
                    else:
                        return 'Please upload an image file - jpeg, png, jpg'
                else:
                    return 'Please upload an image file'
        else:
            return f"{email} is not a valid email!"
    else:
        return 'All input fields are required!'

@app.route('/logout', methods=['GET'])
def logout():
    if 'unique_id' in session:
        logout_id = request.args.get('logout_id')
        if logout_id:
            status = "Offline now"
            sql = f"UPDATE users SET status = '{status}' WHERE unique_id = {logout_id}"
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.close()
    return redirect(url_for('login'))

@app.route('/chat')
def chat():
    if 'unique_id' not in session:
        return redirect('/login')
    
    # Lógica para buscar os detalhes do usuário no banco de dados
    unique_id = session["unique_id"]
    user = User.query.filter_by(unique_id=unique_id).first()

    return render_template('chat.html', user=user)

@app.route('/chat/<int:user_id>', methods=["GET", "POST"])
def chat_with(user_id):
    if 'unique_id' not in session:
        return redirect('login')

    sql = f"SELECT * FROM users WHERE unique_id = {user_id}"
    with engine.connect() as conn:
        query = conn.execute(text(sql))
        conn.close()
    row = query.fetchone()

    if not row:
        return redirect('chat')

    return render_template('chat_with.html', user=row)

@app.route('/send-message', methods=["POST"])
def send_message():
    if 'unique_id' in session:
        outgoing_id = session['unique_id']
        incoming_id = request.form.get('incoming_id')
        message = request.form.get('message')
        if message:
            try:
                conn = engine.connect()
                sql = "INSERT INTO messages (incoming_msg_id, outgoing_msg_id, msg) VALUES (:incoming_id, :outgoing_id, :message)"
                conn.execute(text(sql), {"incoming_id": incoming_id, "outgoing_id": outgoing_id, "message": message})
                conn.commit()
                conn.close()
                return "Mensagem enviada com sucesso!"
            except Exception as e:
                return 'Falha ao enviar a mensagem!\n' + str(e)
                
        return "Não foi possível enviar a mensagem!"
                
    else:
        return redirect('/login')

@app.route('/get-chat', methods=["POST"])
def get_chat():
    if 'unique_id' in session:
        outgoing_id = int(session["unique_id"])
        incoming_id = request.form["incoming_id"]
        output = ""
        sql = f"SELECT * FROM messages LEFT JOIN users ON users.unique_id = messages.outgoing_msg_id \
                WHERE (outgoing_msg_id = {outgoing_id} AND incoming_msg_id = {incoming_id}) \
                OR (outgoing_msg_id = {incoming_id} AND incoming_msg_id = {outgoing_id}) ORDER BY msg_id"
        with engine.connect() as conn:
            query = conn.execute(text(sql)).mappings()
            conn.close()
        if query is not None:
            rows = query.all()
            for row in rows:
                print(row)
                if row["outgoing_msg_id"] == outgoing_id:
                    output += f'<div class="chat outgoing"> \
                                <img src="/static/images/{row["img"]}" alt=""> \
                                <div class="details"> \
                                    <p>{row["msg"]}</p> \
                                </div> \
                                </div>'
                else:
                    output += f'<div class="chat incoming"> \
                                <img src="/static/images/{row["img"]}" alt=""> \
                                <div class="details"> \
                                    <p>{row["msg"]}</p> \
                                </div> \
                                </div>'
        else:
            output += '<div class="text">No messages are available. Once you send message they will appear here.</div>'
        return output
    else:
        return redirect(url_for('login'))

@app.route('/get-users', methods=['GET'])
def users():
    if 'unique_id' in session:
        outgoing_id = session['unique_id']
        sql = f"SELECT * FROM users WHERE NOT unique_id = {outgoing_id} ORDER BY user_id DESC"
        with engine.connect() as conn:
            query = conn.execute(text(sql)).mappings()
            conn.close()
        output = ""
        if query is None:
            output += "No users are available to chat"
        else:
            while row := query.fetchone():
                sql2 = f"SELECT * FROM messages WHERE (incoming_msg_id = {row['unique_id']} OR outgoing_msg_id = {row['unique_id']}) AND (outgoing_msg_id = {outgoing_id} OR incoming_msg_id = {outgoing_id}) ORDER BY msg_id DESC LIMIT 1"
                with engine.connect() as conn2:
                    query2 = conn2.execute(text(sql2)).mappings()
                    conn2.close()
                row2 = query2.fetchone()
                if row2 is None:
                    result = "Empty message"
                else:
                    result = row2['msg']
                msg = result[:28] + '...' if len(result) > 28 else result
                you = "You: " if row2 and outgoing_id == row2['outgoing_msg_id'] else ""
                offline = "offline" if row['status'] == "Offline now" else ""
                hid_me = "hide" if outgoing_id == row['unique_id'] else ""
                output += f'<a href="/chat/{row["unique_id"]}">'
                output += '<div class="content">'
                output += f'<img src="/static/images/{row["img"]}" alt="">'
                output += '<div class="details">'
                output += f'<span>{row["fname"]} {row["lname"]}</span>'
                output += f'<p>{you}{msg}</p>'
                output += '</div>'
                output += '</div>'
                output += f'<div class="status-dot {offline}"><i class="fas fa-circle"></i></div>'
                output += '</a>'

        return output
    else:
        return redirect(url_for('login'))
    
@app.route('/search-users', methods=["POST"])
def search_users():
    if 'unique_id' in session:
        outgoing_id = session['unique_id']
        search_term = request.form.get('searchTerm')
        
        sql = f"SELECT * FROM users WHERE NOT unique_id = {outgoing_id} AND (fname LIKE '%{search_term}%' OR lname LIKE '%{search_term}%')"
        with engine.connect() as conn:
            query = conn.execute(text(sql)).mappings()
            conn.close()
        
        output = ""
        if query is None:
            output += "No users are available to chat"
        else:
            while row := query.fetchone():
                sql2 = f"SELECT * FROM messages WHERE (incoming_msg_id = {row['unique_id']} OR outgoing_msg_id = {row['unique_id']}) AND (outgoing_msg_id = {outgoing_id} OR incoming_msg_id = {outgoing_id}) ORDER BY msg_id DESC LIMIT 1"
                with engine.connect() as conn2:
                    query2 = conn2.execute(text(sql2)).mappings()
                    conn2.close()
                row2 = query2.fetchone()
                if row2 is None:
                    result = "Empty message"
                else:
                    result = row2['msg']
                msg = result[:28] + '...' if len(result) > 28 else result
                you = "You: " if row2 and outgoing_id == row2['outgoing_msg_id'] else ""
                offline = "offline" if row['status'] == "Offline now" else ""
                hid_me = "hide" if outgoing_id == row['unique_id'] else ""
                output += f'<a href="/chat/{row["unique_id"]}">'
                output += '<div class="content">'
                output += f'<img src="/static/images/{row["img"]}" alt="">'
                output += '<div class="details">'
                output += f'<span>{row["fname"]} {row["lname"]}</span>'
                output += f'<p>{you}{msg}</p>'
                output += '</div>'
                output += '</div>'
                output += f'<div class="status-dot {offline}"><i class="fas fa-circle"></i></div>'
                output += '</a>'

        return output
    else:
        return redirect('/login')


## Models
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')