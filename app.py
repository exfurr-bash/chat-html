from flask import Flask, render_template, redirect, url_for, request, flash
from flask_socketio import SocketIO, send
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'uwu-segredinho-kawaii'  # 🔐 escondidinho
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Model fofo de User
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Model cheio de amor de Message
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(500), nullable=False)

# Carregamento do user logado
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
            return redirect(url_for('chat'))
        else:
            flash('Usuário ou senha errados, mana! Tente de novo :c', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Esse nome já tá em uso, bb! Escolhe outro ✨', 'warning')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('chat'))
    return render_template('register.html')

@app.route('/chat')
@login_required
def chat():
    messages = Message.query.all()
    return render_template('chat.html', messages=messages, username=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@socketio.on('message')
def handle_message(msg):
    if current_user.is_authenticated:
        print(f'{current_user.username} diz: {msg}')
        new_message = Message(username=current_user.username, message=msg)
        db.session.add(new_message)
        db.session.commit()
        send(f'{current_user.username}: {msg}', broadcast=True)
    else:
        send("Usuário anônimo tentou enviar msg 😡", broadcast=False)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
