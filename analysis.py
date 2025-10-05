import pandas as pd

def calculate_conversion_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula as taxas de conversão de etapa para etapa e a taxa total.

    :param df: DataFrame com as colunas 'Etapa' e 'Contagem'.
    :return: DataFrame enriquecido com as métricas de conversão.
    """

    df_result = df.copy()

    # 1. Taxa de Conversão da Etapa Anterior (Conversion Rate Previous - CRp)
    # Ex: (Contagem Atual / Contagem Anterior) * 100
    df_result['CR_Anterior (%)'] = (df_result['Contagem'] / df_result['Contagem'].shift(1) * 100).fillna(100).round(2)

    # 2. Taxa de Conversão Total (Conversion Rate Initial - CRi)
    # Ex: (Contagem Atual / Contagem Topo) * 100
    contagem_topo = df_result['Contagem'].iloc[0]
    df_result['CR_Total (%)'] = (df_result['Contagem'] / contagem_topo * 100).round(2)

    # 3. Diferença (Perda de Leads)
    df_result['Perda'] = df_result['Contagem'].diff().fillna(0).astype(int)
    # A perda do topo é sempre 0, mas as perdas subsequentes são negativas (perda)
    df_result.loc[0, 'Perda'] = 0 # Define a primeira perda como 0
    df_result['Perda'] = df_result['Perda'].apply(lambda x: abs(x) if x < 0 else 0)

    # Reordena as colunas para melhor visualização
    df_result = df_result[['Etapa', 'Contagem', 'CR_Anterior (%)', 'CR_Total (%)', 'Perda']]

    return df_result

if __name__ == '__main__':
    from data import load_data
    data_df = load_data()
    analysis_df = calculate_conversion_metrics(data_df)
    print("Análise de Conversão Completa:")
    print(analysis_df)