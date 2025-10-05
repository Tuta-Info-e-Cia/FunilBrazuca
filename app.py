import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import dash_auth
from flask import request, jsonify
from flask_httpauth import HTTPBasicAuth
from dotenv import load_dotenv
import os

# Importa as funções do projeto
from data import load_data
from analysis import calculate_conversion_metrics 
from models import db, User, init_db # Importa o DB e o Modelo de Usuário

# Carrega variáveis de ambiente (como a chave secreta)
load_dotenv() 

# =================================================================
# VARIÁVEIS DE PERSONALIZAÇÃO
# =================================================================
SITE_URL = "http://www.tutainfo.com.br"
POWERED_BY_TEXT = "Powered By - Tutá Info Tecnlogies - BR"
LOGO_PATH = '/assets/logo.png' 
APP_THEME = dbc.themes.COSMO

# =================================================================
# INICIALIZAÇÃO E CONFIGURAÇÃO
# =================================================================

# Inicializa o Dash/Flask
app = dash.Dash(__name__, external_stylesheets=[APP_THEME], title="Funil Brazuca")
server = app.server # O servidor Flask para o Render e rotas de API

# Configurações do Banco de Dados
# Se estiver no Render, mude para 'postgresql://...'
server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' 
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o DB e cria as tabelas se não existirem
init_db(app)

# =================================================================
# 1. AUTENTICAÇÃO DO DASHBOARD (Acesso do Cliente)
# =================================================================

# Função para buscar todos os usuários autorizados no DB
def get_authorized_users():
    """Busca usuários NÃO-webhook no DB para autenticação Dash."""
    with app.app_context():
        # Filtra para não incluir a credencial do webhook master
        users = User.query.filter_by(is_hotmart_auth=False).all()
        # Retorna o formato esperado pelo dash_auth: {email: password_hash}
        return {u.email: u.password_hash for u in users}

# Classe Customizada para Autenticação que usa o DB
class CustomDashAuth(dash_auth.BasicAuth):
    def get_users(self):
        # Sobrescreve para buscar no DB
        return get_authorized_users()

# Inicializa a autenticação com o DB
auth = CustomDashAuth(app, get_users())

# Função para checar a senha (o dash_auth fará isso automaticamente usando o hash)
# No entanto, a classe customizada acima já resolve o problema de buscar no DB.

# =================================================================
# 2. ROTA DE API PARA WEBOOK (Integração Hotmart)
# =================================================================

auth_webhook = HTTPBasicAuth()

# Define a função de verificação para o endpoint Hotmart
@auth_webhook.verify_password
def verify_hotmart_password(username, password):
    """Verifica se o usuário é o mestre do Webhook (Hotmart) no DB."""
    with app.app_context():
        user = User.query.filter_by(email=username, is_hotmart_auth=True).first()
        if user and user.check_password(password):
            return user
    return None

# Endpoint que a Hotmart irá enviar a notificação (Webhook)
@server.route('/webhook-hotmart', methods=['POST'])
@auth_webhook.login_required # Protege a rota, só a Hotmart com a chave secreta pode acessar
def hotmart_webhook():
    try:
        data = request.json # Dados enviados pela Hotmart (JSON)
        
        # Você deve validar a Hotmart Key no headers ou body para dupla segurança
        # ...

        # 1. Checa o status de pagamento (ex: 'APROVADO' ou 'COMPLETO')
        status = data.get('status')
        if status not in ['APROVADO', 'COMPLETO']:
             return jsonify({'message': 'Status de pagamento pendente ou cancelado.'}), 200

        # 2. Pega o e-mail do comprador
        email_comprador = data.get('email_comprador')
        
        if not email_comprador:
            return jsonify({'message': 'Email do comprador não encontrado.'}), 400

        # 3. Insere o novo usuário no Banco de Dados
        with app.app_context():
            if not User.query.filter_by(email=email_comprador).first():
                
                # Gera uma senha aleatória e segura para o cliente
                senha_gerada = User.generate_random_password()
                
                novo_cliente = User(email=email_comprador, is_hotmart_auth=False)
                novo_cliente.set_password(senha_gerada)
                
                db.session.add(novo_cliente)
                db.session.commit()

                # LOG e AÇÃO DE E-MAIL (Simulação)
                print(f"✅ NOVO CLIENTE CADASTRADO VIA HOTMART: {email_comprador}")
                print(f"   Credenciais: Login: {email_comprador} | Senha: {senha_gerada}")
                # AQUI você integraria um serviço de e-mail (SendGrid, AWS SES)
                # para enviar o email de boas-vindas com as credenciais.

                return jsonify({'message': 'Cliente cadastrado com sucesso e acesso liberado.'}), 200
            else:
                 return jsonify({'message': 'Cliente já estava cadastrado.'}), 200

    except Exception as e:
        print(f"ERRO NO PROCESSAMENTO DO WEBHOOK: {e}")
        return jsonify({'message': 'Erro interno no processamento.'}), 500

# =================================================================
# FUNÇÕES DE LAYOUT (Mantidas)
# =================================================================

# [Mantenha aqui as funções create_funnel_chart, create_kpi_card e create_metric_table]
# [Mantenha aqui as definições de navbar e footer]

# O layout do app permanece o mesmo (apenas omitido por brevidade)
app.layout = html.Div([
    # navbar, 
    # dbc.Container([...]) 
    # footer 
    # ... (Copie o layout completo da resposta anterior) ...
])


# =================================================================
# EXECUÇÃO
# =================================================================
if __name__ == '__main__':
    # Cria o usuário mestre e a tabela se não existirem
    print("--- ⚙️ Inicializando Banco de Dados e Usuários Mestres ---")
    init_db(app) 
    
    # Exemplo de usuário para testar o acesso ao Dashboard
    User.add_user('teste@funilbrazuca.com', '123456') 
    
    print("--- 🌐 Funil Brazuca - Dashboard Web Iniciado 🌐 ---")
    print(f"Abra no seu navegador: http://127.0.0.1:8050/")
    app.run(debug=True)