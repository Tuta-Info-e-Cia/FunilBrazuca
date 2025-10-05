from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import random
import string
import os

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_hotmart_auth = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    @staticmethod
    def generate_random_password(length=12):
        """Gera uma senha forte para o cliente."""
        caracteres = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(caracteres) for _ in range(length))

def init_db(app):
    """Inicializa o DB, cria tabelas e o usuário mestre do Webhook."""
    with app.app_context():
        db.init_app(app)
        db.create_all() 

        HOTMART_SECRET = os.getenv('HOTMART_WEBHOOK_SECRET') 

        if not User.query.filter_by(email='hotmart_webhook_master').first():
            if HOTMART_SECRET:
                master_user = User(email='hotmart_webhook_master', is_hotmart_auth=True)
                master_user.set_password(HOTMART_SECRET)
                db.session.add(master_user)
                db.session.commit()
                print(">>> [DB] Usuário mestre do Webhook criado/verificado.")
            else:
                 print("!!! [DB] ERRO: HOTMART_WEBHOOK_SECRET não configurada. Webhook DESPROTEGIDO!")

def add_user(email, password):
    """Adiciona um novo usuário (cliente) ao banco de dados."""
    with db.app_context():
        if not User.query.filter_by(email=email).first():
            new_user = User(email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            return True
        return False