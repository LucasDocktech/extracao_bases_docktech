import pandas as pd
from sqlalchemy import text
import sys
import os
# Adicionando caminho para buscar o modulo de conexao
sys.path.append(r'\\192.168.5.15\mis\Funcoes')
import conn
from aux_data_sistema import obter_datas

# Configuracao da pasta de destino na rede
# PASTA_DESTINO = r"\\192.168.5.15\mis\Pessoal\Lucas\Site_docktech_ligacoes\arquivos_parquet_monitoria"
# Localmente para testes
PASTA_DESTINO = r"C:\Users\lucas.pinto\Desktop\Site_docktech_ligacoes\arquivos_parquet_monitoria"
os.makedirs(PASTA_DESTINO, exist_ok=True)

# Inicializa conexao atraves do modulo externo
login = conn.dbconnect()

# Obter as datas do modulo aux_data_sistema.py
datas = obter_datas()
data_inicio = f"{datas['inicio']}" # Data para o filtro @_DATAI
data_fim = f"{datas['fim']}"       # Data para o filtro @_DATAF

# ==============================
# 1. FUNCAO DE CARREGAMENTO
# ==============================
def carregar_monitoria():
    # Utiliza a engine correspondente ao banco de Qualidade
    engine = login.connQualidade
    with engine.connect() as cnxn:
        query_sql = f"""
        WITH CTE AS (
            SELECT
                ROW_NUMBER() OVER (PARTITION BY MONITORIA ORDER BY DATAMONITORIA) AS RN,
                LTRIM(RTRIM(UPPER(MONITOR))) AS MONITOR,
                MONITORIA,
                MEDIA,
                LTRIM(RTRIM(UPPER(OPERADOR))) AS OPERADOR,
                DIADALIGACAO,
                CAST(DIADALIGACAO AS DATE) AS DIADALIGACAO_SHORTDATE,
                DATAMONITORIA,
                DATEPART(WEEKDAY, DATAMONITORIA) AS DATAMONITORIA_DIA_SEMANA_NUM,
                DATENAME(YEAR, DATAMONITORIA) AS ANO_DATAMONITORIA,
                LOWER(LEFT(DATENAME(MONTH, DATAMONITORIA),3)) AS DATAMONITORIA_MES,
                DATEPART(MONTH, DATAMONITORIA) AS DATAMONITORIA_NUM,
                CAST(DATAMONITORIA AS DATE) AS DATAMONITORIA_SHORTDATE,
                DATAFEEDBACK,
                CAST(DATAFEEDBACK AS DATE) AS DATAFEEDBACK_SHORTDATE,
                REPLACE(PERGUNTA, 'MICRO TEMA - ', '') AS PERGUNTA,
                CLASSIFICACAO,
                QUESTIONARIO,
                CASE
                    WHEN DATEDIFF(DAY, DATAMONITORIA, DATAFEEDBACK) <= 5 THEN 1
                    ELSE 0
                END AS DentroSLA,
                STATUS,
                RESPOSTA,
                OPERACAO,
                PERGUNTAGRUPO
            FROM
                [QUALIDADE_DBM].[dbo].[POWER_BI] WITH (NOLOCK)
            WHERE
                (PERGUNTA NOT LIKE '%%macro%%' 
                     AND PERGUNTA NOT IN (
                        'Arquivo ','Código','Data e hora do atendimento',
                        'Desconectou a ligação sem atender a solicitação',
                        'Emissor','Emissor (escrever em letras maiúsculas).',
                        'Resumo e apontamentos'
                     ))
                AND CAST(DATAMONITORIA AS DATE) BETWEEN '{data_inicio}' AND '{data_fim}'
        )
        SELECT * FROM CTE WHERE RN = 1
        """
        df = pd.read_sql_query(text(query_sql), cnxn)
        return df

# ==============================
# 2. EXECUCAO E EXPORTACAO
# ==============================
def executar_e_salvar_monitoria():
    print("Iniciando processo de extracao e salvamento Monitoria...")
   
    try:
        df_novo = carregar_monitoria()
        if df_novo.empty:
            print("Nenhum dado novo retornado.")
            return
        # Chamadas gerais incluem todas chamadas de SAC
        caminho_parquet = os.path.join(PASTA_DESTINO, "import_monitoria.parquet")
 
        if os.path.exists(caminho_parquet):
            print("Carregando historico e mesclando registros...")
            df_historico = pd.read_parquet(caminho_parquet)
           
            # Concatena o novo com o histórico
            df_concatenado = pd.concat([df_historico, df_novo], ignore_index=True)
           
            # --- AJUSTE DE LÓGICA ---
            # Removemos duplicatas apenas se for o MESMO operador no MESMO
            # momento de uma MESMA chamada (prevenção contra erro de carga)
            # Mas permitimos que o mesmo linkedid apareça com OPERADORES diferentes.
            df_final = df_concatenado.drop_duplicates(subset=['MONITORIA', 'DATAMONITORIA', 'OPERADOR'])
           
            # Ordenação cronológica para facilitar a leitura da auditoria
            df_final = df_final.sort_values(by=['MONITORIA', 'DATAMONITORIA'])
           
        else:
            print("Primeira carga detectada. Criando arquivo novo.")
            # Ordena mesmo na primeira carga
            df_final = df_novo.sort_values(by=['MONITORIA', 'DATAMONITORIA'])
 
        # Exportação
        df_final.to_parquet(caminho_parquet, index=False, compression='snappy')
       
        print(f"Processo finalizado. Total de dados armazenados: {len(df_final)}")
 
    except Exception as e:
        print(f"Erro no processamento: {e}")
 
if __name__ == "__main__":
    executar_e_salvar_monitoria()
