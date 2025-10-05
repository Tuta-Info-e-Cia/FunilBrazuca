import pandas as pd

def calculate_conversion_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula as taxas de conversão (CRi e CRp) e perdas."""
    df_result = df.copy()

    # Taxa de Conversão da Etapa Anterior (CRp)
    df_result['CR_Anterior (%)'] = (df_result['Contagem'] / df_result['Contagem'].shift(1) * 100).fillna(100).round(2)

    # Taxa de Conversão Total (CRi)
    contagem_topo = df_result['Contagem'].iloc[0]
    df_result['CR_Total (%)'] = (df_result['Contagem'] / contagem_topo * 100).round(2)

    # Perda de Leads
    df_result['Perda'] = df_result['Contagem'].diff().fillna(0).astype(int)
    df_result.loc[0, 'Perda'] = 0 
    df_result['Perda'] = df_result['Perda'].apply(lambda x: abs(x) if x < 0 else 0)

    df_result = df_result[['Etapa', 'Contagem', 'CR_Anterior (%)', 'CR_Total (%)', 'Perda']]
    return df_result