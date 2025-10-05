import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import dash_auth
from flask import request, jsonify
from flask_httpauth import HTTPBasicAuth
from dotenv import load_dotenv
import os
import pandas as pd
import plotly.graph_objects as go
from werkzeug.security import check_password_hash

# Importa os módulos locais
from data import load_data
from analysis import calculate_conversion_metrics 
from models import db, User, init_db, add_user 

# Carrega variáveis de ambiente (crucial para testes locais via .env)
load_dotenv() 

# =================================================================
# VARIÁVEIS DE CONFIGURAÇÃO (EDITE AQUI!)
# =================================================================
SITE_URL = "http://www.tutainfo.com.br"
POWERED_BY_TEXT = "Powered By - Tutá Info Tecnlogies - BR"
LOGO_PATH = '/assets/logo.png' 
APP_THEME = dbc.themes.COSMO 

# Configura o URI do Banco de Dados: Usa DATABASE_URL do Render (PostgreSQL) ou SQLite (local)
DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///users.db') 

# =================================================================
# INICIALIZAÇÃO E CONFIGURAÇÃO DO DASH/FLASK
# =================================================================

app = dash.Dash(__name__, external_stylesheets=[APP_THEME], title="Funil Brazuca")
server = app.server 

server.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
init_db(app) # Inicializa o DB e cria o usuário mestre

# =================================================================
# 1. AUTENTICAÇÃO DO DASHBOARD (Acesso do Cliente ao Funil)
# =================================================================

def get_authorized_users():
    """Busca usuários NÃO-webhook no DB para autenticação Dash."""
    with app.app_context():
        users = User.query.filter_by(is_hotmart_auth=False).all()
        return {u.email: u.password_hash for u in users}

class CustomDashAuth(dash_auth.BasicAuth):
    def get_users(self):
        return get_authorized_users()
    
    def check_auth(self, username, password):
        users = self.get_users()
        if username in users:
            return check_password_hash(users[username], password)
        return False

auth = CustomDashAuth(app, get_authorized_users())

# =================================================================
# 2. ROTA DE API PARA WEBOOK (Integração Hotmart)
# =================================================================

auth_webhook = HTTPBasicAuth()

@auth_webhook.verify_password
def verify_hotmart_password(username, password):
    """Verifica se o usuário é o mestre do Webhook."""
    with app.app_context():
        user = User.query.filter_by(email='hotmart_webhook_master', is_hotmart_auth=True).first()
        if user and user.check_password(password):
            return user
    return None

@server.route('/webhook-hotmart', methods=['POST'])
@auth_webhook.login_required 
def hotmart_webhook():
    try:
        data = request.json
        event = data.get('event')
        status = data.get('h_status')

        if event == 'PURCHASE' and status == 'APPROVED':
            email_comprador = data.get('buyer', {}).get('email')

            if not email_comprador:
                return jsonify({'message': 'Email do comprador não encontrado.'}), 400

            senha_gerada = User.generate_random_password(length=12)
            
            if add_user(email_comprador, senha_gerada):
                # >> AQUI ENTRA O CÓDIGO DE ENVIO DE EMAIL (Ação necessária) <<
                print(f"✅ NOVO CLIENTE CADASTRADO: {email_comprador}. Senha: {senha_gerada}")
                return jsonify({'message': 'Cliente cadastrado e acesso liberado.'}), 200
            else:
                 return jsonify({'message': 'Cliente já estava cadastrado.'}), 200

        return jsonify({'message': f'Evento {event} ignorado.'}), 200

    except Exception as e:
        print(f"!!! ERRO FATAL NO WEBHOOK: {e}")
        return jsonify({'message': 'Erro interno no processamento.'}), 500

# =================================================================
# 3. FUNÇÕES DE VISUALIZAÇÃO E LAYOUT
# =================================================================

def create_funnel_chart(df: pd.DataFrame) -> go.Figure:
    cores = ['#003f5c', '#58508d', '#bc5090', '#ff6361']
    text_data = []
    for index, row in df.iterrows():
        cr_prev = row['CR_Anterior (%)']
        cr_total = row['CR_Total (%)']
        perda = row['Perda']
        text = f"Total: {row['Contagem']:,}" if index == 0 else (
            f"Conv. Anterior: {cr_prev:.2f}%<br>"
            f"Conv. Total: {cr_total:.2f}%<br>"
            f"Perda da Etapa: {perda:,} Leads"
        )
        text_data.append(text)
    
    fig = go.Figure(go.Funnel(
        y = df['Etapa'], x = df['Contagem'],
        textinfo = "value+percent initial", marker = dict(color=cores),
        hovertemplate = "<b>%{y}</b><br>Contagem: %{x:,}<br>%{text}<extra></extra>", text = text_data
    ))
    fig.update_layout(title_text="Funil de Vendas Interativo", margin=dict(l=20, r=20, t=60, b=20), funnelmode="stack", height=500)
    return fig

def create_kpi_card(title, value, unit="", color="primary"):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-subtitle text-muted"),
            html.H3(f"{value}{unit}", className=f"card-title text-{color}"),
        ]), className="text-center shadow-sm h-100"
    )

def create_metric_table(df: pd.DataFrame) -> dbc.Table:
    def format_metric(row, col):
        value = row[col]
        if col == 'CR_Anterior (%)':
            color = 'success' if value >= 30 else ('warning' if value >= 10 else 'danger')
            return html.Td(f"{value}%", className=f'text-{color} fw-bold')
        if col == 'Perda' and value > 0:
             return html.Td(f"-{value:,}", className='text-danger fw-bold')
        return html.Td(f"{value:,}")

    header = [html.Thead(html.Tr([html.Th(col) for col in df.columns]))]
    body = [html.Tbody([
        html.Tr([
            html.Td(row['Etapa']),
            html.Td(f"{row['Contagem']:,}"),
            format_metric(row, 'CR_Anterior (%)'),
            format_metric(row, 'CR_Total (%)'),
            format_metric(row, 'Perda'),
        ]) for index, row in df.iterrows()
    ])]
    return dbc.Table(header + body, striped=True, bordered=True, hover=True, responsive=True, className="mt-3")

# --- NAVAR E FOOTER ---

navbar = dbc.Navbar(
    dbc.Container([
        html.A(
            html.Img(src=LOGO_PATH, height="30px", className="me-2"),
            href=SITE_URL, style={"textDecoration": "none"}),
        dbc.NavbarBrand("Funil Brazuca", className="ms-2 fw-bold text-light"),
        dbc.Nav([
                dbc.NavItem(dbc.NavLink(html.A("Tutá Info", href=SITE_URL, target="_blank", className="text-light"))),
                dbc.NavItem(dbc.NavLink(html.A("Dashboard", href="#", className="text-light"))),
            ], className="ms-auto", navbar=True
        ),
    ]), color="primary", dark=True, sticky="top", className="shadow-sm"
)

footer = html.Footer(
    dbc.Container([
        dbc.Row(dbc.Col(html.Hr(), width=12)),
        dbc.Row(
            dbc.Col(
                html.P([
                    POWERED_BY_TEXT, 
                    html.A(" - " + SITE_URL.replace('http://', '').replace('www.', ''), href=SITE_URL, target="_blank", className="ms-1 text-decoration-none text-muted")
                ], className="text-center text-muted m-0 p-3")
            , width=12)
        )
    ]), style={"marginTop": "50px", "borderTop": "1px solid #dee2e6"}
)

# --- CARREGAMENTO DE DADOS PARA O LAYOUT ---
data_df = load_data()
analysis_df = calculate_conversion_metrics(data_df)
funnel_fig = create_funnel_chart(analysis_df)

total_vendas = analysis_df['Contagem'].iloc[-1]
total_leads = analysis_df['Contagem'].iloc[0]
cr_final = analysis_df['CR_Total (%)'].iloc[-1]
perda_meio_fundo = analysis_df['Perda'].iloc[2:].sum()

# =================================================================
# 4. LAYOUT FINAL
# =================================================================

app.layout = html.Div([
    navbar, 
    dbc.Container([
        dbc.Row(dbc.Col(html.H1("Funil Brazuca: Análise de Conversão", 
                               className="text-center my-4 text-primary"))),
        dbc.Row([
            dbc.Col(create_kpi_card("Vendas Fechadas", total_vendas, color="success"), md=6, lg=3, className="mb-4"),
            dbc.Col(create_kpi_card("Taxa de Conversão Total", cr_final, "%", color="info"), md=6, lg=3, className="mb-4"),
            dbc.Col(create_kpi_card("Total de Leads", total_leads, color="dark"), md=6, lg=3, className="mb-4"),
            dbc.Col(create_kpi_card("Perda Pós-Proposta", perda_meio_fundo, color="danger"), md=6, lg=3, className="mb-4"),
        ], className="g-4"),
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.H5("Jornada do Cliente", className="card-title text-center"),
                        dcc.Graph(id='funnel-chart', figure=funnel_fig)
                    ]), className="shadow-lg border-0"), md=12, lg=8, className="mb-4"
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.H5("Insight Rápido", className="card-title text-center text-warning"),
                        html.P(f"A maior taxa de abandono ocorre na transição de **Leads** para **Propostas**.", className="card-text"),
                        html.Ul([
                            html.Li(f"Leads no Topo: {total_leads:,}"),
                            html.Li(f"Perda no 1º passo: -{analysis_df['Perda'].iloc[1]:,}"),
                        ], className="list-unstyled mt-3"),
                        dbc.Button("Ver Detalhes", color="warning", className="mt-3 w-100"),
                    ]), className="shadow-lg border-0 h-100"), md=12, lg=4, className="mb-4"
            ),
        ], className="g-4"),
        dbc.Row(dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5("Tabela de Conversão e Perdas por Etapa", className="card-title text-center"),
                    create_metric_table(analysis_df)
                ]), className="shadow-lg border-0 mb-4"
            ), width=12
        )),
    ], fluid=True), 
    footer
])

# =================================================================
# EXECUÇÃO DO APLICATIVO
# =================================================================
if __name__ == '__main__':
    # Adiciona um usuário de teste (se ainda não existir)
    with server.app_context():
        add_user('teste@funilbrazuca.com', '123456') 
    
    print("--- 🌐 Funil Brazuca - Dashboard Web Iniciado 🌐 ---")
    print(f"Abra o Dashboard: http://127.0.0.1:8050/ (Login: teste@funilbrazuca.com / Senha: 123456)")
    app.run(debug=True)