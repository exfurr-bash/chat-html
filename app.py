import uuid
import os
import requests
import json
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_socketio import SocketIO, send
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Filtro customizado para regex_replace
def regex_replace(value, pattern, replacement):
    return re.sub(pattern, replacement, value)

# Configuração do Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'uwu-segredinho-kawaii'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Registrando o filtro customizado
app.jinja_env.filters['regex_replace'] = regex_replace

# Inicializações mágicas
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models lindinhos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(500), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Função para gerar resposta do Gemini
def gerar_resposta_gemini_flash(mensagens):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    prompt_base = (
        "Você é Kokoro-chan, uma IA fofa e debochada :3 "
        "Fale como um bot furry, com gírias e energia positiva UwU. "
        "Essas são as últimas mensagens do chat, com IDs ocultos, só pra você saber quem é quem lembre-se que o usuario Kokoro-chan è voce mesmo, tente evitar responder a si mesmo:\n\n"
    )

    contexto = "\n".join([
    f"[{m.username}]: {m.message}" for m in mensagens
])

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt_base + contexto}]
            }
        ]
    }

    params = {"key": os.getenv("GEMINI_API_KEY")}
    response = requests.post(url, headers=headers, params=params, data=json.dumps(body))

    if response.ok:
        try:
            content = response.json()
            return content['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return "Kokoro-chan travou de tanta fofura... AAAAAA!"
    else:
        print("Erro com Gemini:", response.text)
        return "Kokoro-chan explodiu... mas em glitter!"

# Roteando o amor
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            session['username'] = username
            session['user_id'] = str(uuid.uuid4())  # ID exclusivo pro bot ver
            return redirect(url_for('chat'))
        else:
            flash('Usuário ou senha errados, bb :c', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Esse nome já é de alguém, maninha! Escolhe outro UwU', 'warning')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        session['username'] = username
        session['user_id'] = str(uuid.uuid4())
        return redirect(url_for('chat'))
    return render_template('register.html')

@app.route('/chat')
@login_required
def chat():
    messages = Message.query.order_by(Message.id.desc()).limit(50).all()[::-1]
    return render_template('chat.html', messages=messages, username=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Chat mágicooooooo
@socketio.on('message')
def handle_message(msg):
    if current_user.is_authenticated:
        user_id = session.get('user_id', 'desconhecido')
        msg_com_id = f"{current_user.username} (id:{user_id}): {msg}"

        new_message = Message(username=current_user.username, message=msg_com_id)
        db.session.add(new_message)
        db.session.commit()

        msg_visual = f"{current_user.username}: {msg}"  # sem ID pro front
        send(msg_visual, broadcast=True)

        if '@kokoro' in msg.lower():
            ultimas = Message.query.order_by(Message.id.desc()).limit(25).all()[::-1]
            resposta = gerar_resposta_gemini_flash(ultimas)

            resposta_formatada = f'Kokoro-chan (IA): {resposta}'

            # Salvar resposta no banco como se fosse uma mensagem da Kokoro-chan
            resposta_bot = Message(username='Kokoro-chan', message=resposta_formatada)
            db.session.add(resposta_bot)
            db.session.commit()

            send(resposta_formatada, broadcast=True)
#        else:
#            send("Anônimo tentando trollar, sai fora fi", broadcast=False)
# Roda esse trem cheio de glitter!
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
