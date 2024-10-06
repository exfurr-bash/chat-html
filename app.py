from flask import Flask, render_template, redirect, url_for, request
from flask_socketio import SocketIO, send
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Tabela de usuários
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Tabela de mensagens
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(500), nullable=False)

# Carregar usuário
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rota para página inicial
@app.route('/')
def index():
    return redirect(url_for('login'))  # Redireciona para a página de login

# Rota para página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('chat'))
    return render_template('login.html')

# Rota para página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('chat'))
    return render_template('register.html')

# Rota para página de chat
@app.route('/chat')
@login_required
def chat():
    messages = Message.query.all()  # Recupera todas as mensagens do banco de dados
    return render_template('chat.html', messages=messages, username=current_user.username)

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Função para lidar com novas mensagens enviadas
@socketio.on('message')
@login_required
def handle_message(msg):
    print(f'{current_user.username} says: {msg}')
    # Salva a mensagem no banco de dados
    new_message = Message(username=current_user.username, message=msg)
    db.session.add(new_message)
    db.session.commit()

    send(f'{current_user.username}: {msg}', broadcast=True)

# Iniciar o servidor
if __name__ == '__main__':
    with app.app_context():  # Criar um contexto de aplicativo
        db.create_all()  # Cria as tabelas no banco de dados se não existirem
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)  # Mude debug=True para debug=False

