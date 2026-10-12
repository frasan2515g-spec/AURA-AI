import os
import base64
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aura_ai_secret_key_super_secure_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aura_users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configuración del cliente GroqCloud con tu API Key
groq_client = Groq(api_key="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")

SYSTEM_INSTRUCTION = (
    "Eres AURA AI, un asistente virtual inteligente, cercano, informal y directo. "
    "Responde siempre en español fluido y natural, usando un tono amigable, humano y al grano. "
    "No utilices títulos grandes con hashtags (#) ni tablas. "
    "Organiza tus respuestas con viñetas limpias y preguntas cortas al final."
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    plan = db.Column(db.String(50), default='Gratis')
    chats = db.relationship('ChatSession', backref='user', lazy=True, cascade="all, delete-orphan")

class ChatSession(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), default='Nueva conversación')
    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade="all, delete-orphan")

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), db.ForeignKey('chat_session.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False) 
    content = db.Column(db.Text, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if not current_user.is_authenticated:
        guest_user = User.query.filter_by(username='Invitado').first()
        if not guest_user:
            guest_user = User(username='Invitado', password=generate_password_hash('guest123'))
            db.session.add(guest_user)
            db.session.commit()
        login_user(guest_user)
    return render_template('index.html', username=current_user.username, plan=current_user.plan)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            error = "Usuario o contraseña incorrectos."
            
    return f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Iniciar Sesión - AURA AI</title>
        <style>
            body {{ background: #0b0f19; color: #f3f4f6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .card {{ background: #111827; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 350px; border: 1px solid #1f2937; text-align: center; }}
            h2 {{ color: #a8c7fa; margin-bottom: 24px; }}
            input {{ width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #374151; background: #1f2937; color: #fff; box-sizing: border-box; font-size: 14px; }}
            input:focus {{ outline: none; border-color: #a8c7fa; }}
            button {{ width: 100%; padding: 12px; background: linear-gradient(135deg, #6366f1, #a855f7); color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 15px; font-size: 15px; transition: opacity 0.2s; }}
            button:hover {{ opacity: 0.9; }}
            .error {{ color: #ef4444; font-size: 13px; margin-bottom: 10px; }}
            a {{ color: #a8c7fa; text-decoration: none; font-size: 14px; }}
            a:hover {{ text-decoration: underline; }}
            .footer-links {{ margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Iniciar Sesión en AURA AI</h2>
            {f'<div class="error">{error}</div>' if error else ''}
            <form method="POST">
                <input type="text" name="username" placeholder="Usuario" required autocomplete="off">
                <input type="password" name="password" placeholder="Contraseña" required>
                <button type="submit">Entrar</button>
            </form>
            <div class="footer-links">
                <p>¿No tenés una cuenta? <a href="/register">Registrate</a></p>
                <p><a href="/">← Volver al chat</a></p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = ""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            error = "El nombre de usuario ya está en uso."
        else:
            new_user = User(username=username, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('index'))
            
    return f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Registro - AURA AI</title>
        <style>
            body {{ background: #0b0f19; color: #f3f4f6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .card {{ background: #111827; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 350px; border: 1px solid #1f2937; text-align: center; }}
            h2 {{ color: #a8c7fa; margin-bottom: 24px; }}
            input {{ width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #374151; background: #1f2937; color: #fff; box-sizing: border-box; font-size: 14px; }}
            input:focus {{ outline: none; border-color: #a8c7fa; }}
            button {{ width: 100%; padding: 12px; background: linear-gradient(135deg, #6366f1, #a855f7); color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 15px; font-size: 15px; transition: opacity 0.2s; }}
            button:hover {{ opacity: 0.9; }}
            .error {{ color: #ef4444; font-size: 13px; margin-bottom: 10px; }}
            a {{ color: #a8c7fa; text-decoration: none; font-size: 14px; }}
            a:hover {{ text-decoration: underline; }}
            .footer-links {{ margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Crear Cuenta en AURA AI</h2>
            {f'<div class="error">{error}</div>' if error else ''}
            <form method="POST">
                <input type="text" name="username" placeholder="Elige tu Usuario" required autocomplete="off">
                <input type="password" name="password" placeholder="Elige tu Contraseña" required>
                <button type="submit">Registrarse</button>
            </form>
            <div class="footer-links">
                <p>¿Ya tenés cuenta? <a href="/login">Iniciá sesión</a></p>
                <p><a href="/">← Volver al chat</a></p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/update-plan', methods=['POST'])
@login_required
def update_plan():
    data = request.get_json()
    new_plan = data.get('plan', 'Gratis')
    current_user.plan = new_plan
    db.session.commit()
    return jsonify({'success': True, 'message': f'¡Plan {new_plan} activado correctamente!', 'plan': new_plan})

@app.route('/api/history', methods=['GET'])
@login_required
def get_history():
    user_chats = ChatSession.query.filter_by(user_id=current_user.id).all()
    history_data = {}
    for session_obj in user_chats:
        history_data[session_obj.id] = {
            'title': session_obj.title,
            'messages': [{'role': msg.role, 'content': msg.content} for msg in session_obj.messages]
        }
    return jsonify(history_data)

@app.route('/api/chat/delete', methods=['POST'])
@login_required
def delete_chat():
    data = request.get_json()
    session_id = data.get('session_id')
    chat = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if chat:
        db.session.delete(chat)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Chat no encontrado'}), 404

@app.route('/api/chat', methods=['POST'])
@login_required
def chat_api():
    data = request.get_json()
    session_id = data.get('session_id')
    history = data.get('history', [])
    image_data = data.get('image_data')
    
    chat_session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not chat_session:
        first_prompt = history[-1]['content'] if history else "Nueva conversación"
        title_summary = (first_prompt[:25] + '...') if len(first_prompt) > 25 else first_prompt
        chat_session = ChatSession(id=session_id, user_id=current_user.id, title=title_summary)
        db.session.add(chat_session)
        db.session.commit()

    last_user_msg = history[-1]['content'] if history else ''
    db.session.add(ChatMessage(session_id=session_id, role='user', content=last_user_msg))
    db.session.commit()

    # Usamos modelo de visión si hay foto, o tu modelo favorito openAI si es solo texto
    model_to_use = "llama-3.2-11b-vision-preview" if image_data else "openai/gpt-oss-120b"
    
    content_payload = last_user_msg
    if image_data:
        content_payload = [
            {"type": "text", "text": last_user_msg if last_user_msg and not last_user_msg.startswith('[') else "Analiza esta imagen."},
            {"type": "image_url", "image_url": {"url": image_data}}
        ]

    groq_messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
    for i, msg in enumerate(history):
        role = "assistant" if msg["role"] == "bot" else "user"
        if i == len(history) - 1 and image_data:
            groq_messages.append({"role": role, "content": content_payload})
        else:
            groq_messages.append({"role": role, "content": msg["content"]})

    try:
        completion = groq_client.chat.completions.create(
            model=model_to_use,
            messages=groq_messages,
            temperature=0.7,
            max_tokens=1024
        )
        bot_response = completion.choices[0].message.content
        bot_response = bot_response.replace('**', '').replace('*', '')
    except Exception as e:
        bot_response = f"Lo siento, ocurrió un error al procesar tu solicitud: {str(e)}"

    db.session.add(ChatMessage(session_id=session_id, role='bot', content=bot_response))
    db.session.commit()

    return jsonify({'response': bot_response})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)