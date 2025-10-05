from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

db = SQLAlchemy()

class User(db.Model):
    """Modelo para armazenar usuários autorizados."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_hotmart_auth = db.Column(db.Boolean, default=False) # Para proteger o endpoint do Webhook

    def set_password(self, password):
        """Cria um hash seguro da senha."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash."""
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def generate_random_password(length=10):
        """Gera uma senha aleatória para o novo cliente."""
        caracteres = string.ascii_letters + string.digits 
        return ''.join(random.choice(caracteres) for i in range(length))

def init_db(app):
    """Inicializa o banco de dados e cria as tabelas."""
    with app.app_context():
        db.init_app(app)
        db.create_all()

        # Cria um usuário mestre para autenticar o Webhook
        if not User.query.filter_by(email='hotmart_webhook_master').first():
            master_user = User(email='hotmart_webhook_master', is_hotmart_auth=True)
            master_user.set_password('SUA_CHAVE_SECRETA_DA_HOTMART_AQUI') 
            db.session.add(master_user)
            db.session.commit()

# Exemplo de como adicionar um usuário comum (para testes ou manualmente)
def add_user(email, password):
    with db.app_context():
        if not User.query.filter_by(email=email).first():
            new_user = User(email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            print(f"Usuário {email} adicionado ao DB.")
            # Adicione a importação de 'os' no topo se ainda não tiver
import os 
# ...
# ... (código existente) ...

def init_db(app):
    """Inicializa o banco de dados e cria as tabelas."""
    with app.app_context():
        db.init_app(app)
        db.create_all()

        # Lê a chave secreta da Variável de Ambiente
        HOTMART_SECRET = os.getenv('HOTMART_WEBHOOK_SECRET') 

        # Cria um usuário mestre para autenticar o Webhook
        if not User.query.filter_by(email='hotmart_webhook_master').first():
            if HOTMART_SECRET: # Verifica se a chave foi carregada
                master_user = User(email='hotmart_webhook_master', is_hotmart_auth=True)
                master_user.set_password(HOTMART_SECRET)
                db.session.add(master_user)
                db.session.commit()
                print("Usuário mestre do Webhook criado.")
            else:
                 print("AVISO: HOTMART_WEBHOOK_SECRET não encontrada. O Webhook não será protegido!")