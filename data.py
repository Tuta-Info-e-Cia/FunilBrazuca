import pandas as pd

# =================================================================
# EDITAR AQUI: Defina as ETAPAS do seu funil e a CONTAGEM de Leads/Clientes
# =================================================================
FUNNEL_DATA = {
    'Etapa': [
        'Visitantes do Site (Topo)',
        'Leads Capturados (Meio)',
        'Propostas Enviadas (Meio)',
        'Vendas Fechadas (Fundo)'
    ],
    'Contagem': [
        10000, # Visitantes
        3500,  # Leads
        450,   # Propostas
        120    # Vendas
    ]
}
# =================================================================

def load_data():
    """Carrega os dados do funil em um DataFrame do Pandas."""
    df = pd.DataFrame(FUNNEL_DATA)
    return df

if __name__ == '__main__':
    # Exemplo de como seus dados ficam
    print("Dados brutos do Funil:")
    print(load_data())