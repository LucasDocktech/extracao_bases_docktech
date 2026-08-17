import pandas as pd
from sqlalchemy import text
import sys
import os
# Adicionando caminho para buscar o modulo de conexao
sys.path.append(r'\\192.168.5.15\mis\Funcoes')
import conn
from aux_data_sistema import obter_datas

# Configuração da pasta de destino na rede
# PASTA_DESTINO = r"\\192.168.5.15\mis\Pessoal\Lucas\Site_docktech_ligacoes\arquivo_parquet_quadro_operacional"
# Localmente para testes
PASTA_DESTINO = r"C:\Users\lucas.pinto\Desktop\extracao_bases_docktech\arquivo_parquet_quadro_operacional"
os.makedirs(PASTA_DESTINO, exist_ok=True)

# Inicializa conexao atraves do modulo externo
login = conn.dbconnect()

# ==============================
# 1. FUNCAO DE CARREGAMENTO
# ==============================
def carregar_quadro_operacional():
    
    engine = login.connProMIS
    with engine.connect() as cnxn:
        query_sql = f"""
        SELECT DISTINCT
            cd_matricula,
            LTRIM(RTRIM(UPPER(tx_nome))) AS tx_nome,
            tm_entrada,
            tm_saida,
            tm_carga_horaria,
            LTRIM(RTRIM(UPPER(tx_cargo))) AS tx_cargo,
            LTRIM(RTRIM(UPPER(tx_staff))) AS tx_staff,
            LTRIM(RTRIM(UPPER(tx_escala))) AS tx_escala,
            cd_cpf,
            LTRIM(RTRIM(UPPER(tx_escala_semanal))) AS tx_escala_semanal,
            LTRIM(RTRIM(UPPER(tx_supervisor))) AS tx_supervisor,
            LTRIM(RTRIM(UPPER(tx_funcao))) AS tx_funcao,
            LTRIM(RTRIM(UPPER(quartil))) AS quartil,
            dt_quadro_dia
        FROM 
            dbo.tbl_gsheet_quadro_dock WITH(NOLOCK)
        WHERE
            cd_cpf <> 0
            AND cd_cpf IS NOT NULL
            AND cd_cpf NOT IN (20270,20453,20270)
            AND dt_quadro_dia = (
                SELECT MAX(dt_quadro_dia)
                FROM dbo.tbl_gsheet_quadro_dock WITH(NOLOCK)
            )
        """
        df = pd.read_sql_query(text(query_sql), cnxn)
        return df
    
# ==============================
# 2. EXECUCAO E EXPORTACAO
# ==============================
def executar_e_salvar_quadro_operacional():
    print("Iniciando processo de extracao Quadro Operacional...")
    
    try:
        # Carrega os dados
        df = carregar_quadro_operacional()

        if df.empty:
            print("A consulta nao retornou dados para o periodo.")
        else:
            # Caminhos com subpasta
            caminho_parquet = os.path.join(PASTA_DESTINO, "import_quadro_operacional.parquet")
            # caminho_excel = os.path.join(PASTA_DESTINO, "import_quadro_operacional.xlsx")

            # Exportação
            df.to_parquet(caminho_parquet, index=False, compression='snappy')
            # df.to_excel(caminho_excel, index=False)
            
            # print(f"Arquivo '{caminho_parquet}'")
            # print(f"Arquivo '{caminho_excel}'")
            print(f"Total de registros: {len(df)}")

    except Exception as e:
        print(f"Erro durante a execucao: {e}")

if __name__ == "__main__":
    executar_e_salvar_quadro_operacional()