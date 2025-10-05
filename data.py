import pandas as pd

FUNNEL_DATA = {
    'Etapa': [
        'Visitantes do Site (Topo)',
        'Leads Capturados (Meio)',
        'Propostas Enviadas (Meio)',
        'Vendas Fechadas (Fundo)'
    ],
    'Contagem': [
        10000, 
        3500,  
        450,   
        120    
    ]
}

def load_data():
    """Carrega os dados do funil em um DataFrame do Pandas."""
    df = pd.DataFrame(FUNNEL_DATA)
    return df