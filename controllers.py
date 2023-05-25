from flask import render_template, request, session, redirect, url_for
from werkzeug.utils import secure_filename
from models import engine, db
from models.user import User
from models.message import Message
from sqlalchemy import text
import random, hashlib, time, os

class UserController:
    def get_users():
        if 'unique_id' in session:
            outgoing_id = session['unique_id']
            sql = f"SELECT * FROM users WHERE NOT unique_id = {outgoing_id} ORDER BY status ASC, fname ASC"
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
    
    def login():
        if request.method == 'POST':
            email = request.form["email"]
            password = request.form["password"]
            user = User.query.filter_by(email=email).first()
            if user:
                if user.password == hashlib.md5(password.encode()).hexdigest():
                    session["unique_id"] = user.unique_id
                    status = "Active now"
                    user.status = status
                    db.session.commit()
                    return 'success'
            return 'Email or password is incorrect!'
        else:
            return render_template('login.html')

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
                        img_name = secure_filename(image.filename)
                        img_ext = img_name.split('.')[-1].lower()
                        if img_ext in ["jpeg", 'png', 'jpg']:
                            sname = secure_filename(image.filename)
                            path = os.path.join(app.config['UPLOAD_FOLDER'], sname)
                            image.save(path)
                            image.close()
                            user = User(
                                unique_id=int(time.time()) + random.randint(1, 1000000),
                                fname=fname,
                                lname=lname,
                                email=email,
                                password=hashlib.md5(password.encode()).hexdigest(),
                                img=sname
                            )
                            db.session.add(user)
                            db.session.commit()
                            session["unique_id"] = user.unique_id
                            return 'success'
        return 'All fields are required!'

    def logout():
        if 'unique_id' in session:
            unique_id = session['unique_id']
            userlogged = User.query.filter_by(unique_id=unique_id).first()
            userlogged.status = "Offline now"
            db.session.commit()
            session.pop('unique_id', None)
        return redirect(url_for('index'))

class MessageController:
    def chat():
        if 'unique_id' in session:
            unique_id = session['unique_id']
            user = User.query.filter_by(unique_id=unique_id).first()
            if user:
                users = User.query.filter(User.unique_id != unique_id).all()
                return render_template('chat.html', user=user, users=users)
        return redirect(url_for('index'))

    def chat_with(user_id):
        if 'unique_id' in session:
            unique_id = session['unique_id']
            user = User.query.filter_by(unique_id=unique_id).first()
            if user:
                chat_user = User.query.filter_by(unique_id=user_id).first()
                if chat_user:
                    messages = Message.query.filter(
                        (Message.incoming_msg_id == unique_id) & (Message.outgoing_msg_id == user_id) |
                        (Message.incoming_msg_id == user_id) & (Message.outgoing_msg_id == unique_id)
                    ).order_by(Message.msg_id).all()
                    return render_template('chat_with.html', user=chat_user)
        return redirect(url_for('index'))
    
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

    def send_message():
        if 'unique_id' in session:
            unique_id = session['unique_id']
            user = User.query.filter_by(unique_id=unique_id).first()
            if user:
                message = request.form['message']
                incoming_id = request.form['incoming_id']
                if message and incoming_id:
                    chat_user = User.query.filter_by(unique_id=incoming_id).first()
                    if chat_user:
                        message = Message(
                            outgoing_msg_id=unique_id,
                            incoming_msg_id=incoming_id,
                            msg=message
                        )
                        db.session.add(message)
                        db.session.commit()
                        return 'success'
        return 'Invalid request'