import pandas as pd
from sqlalchemy import text
import sys
import os
# Adicionando caminho para buscar o modulo de conexao
sys.path.append(r'\\192.168.5.15\mis\Funcoes')
import conn
from aux_data_sistema import obter_datas

# Configuração da pasta de destino
# PASTA_DESTINO = r"\\192.168.5.15\mis\Pessoal\Lucas\Site_docktech_ligacoes\arquivos_parquet_tempo_logado_nexus"
# Pasta para testes locais
PASTA_DESTINO = r"C:\Users\lucas.pinto\Desktop\Site_docktech_ligacoes\arquivos_parquet_tempo_logado_nexus"
os.makedirs(PASTA_DESTINO, exist_ok=True)

# Inicializa conexao atraves do modulo externo
login = conn.dbconnect()

# Obter as datas do modulo aux_data_sistema.py
datas = obter_datas()
data_inicio = f"{datas['inicio']} 00:00:00"
data_fim = f"{datas['fim']} 23:59:59"

# ==============================
# 1. FUNCAO DE CARREGAMENTO
# ==============================
def carregar_tempo_logado_nexus():
    engine = login.connProMIS
    with engine.connect() as cnxn:
        query_sql = f"""
                SELECT
                    t.dthr_inicio_login,
                    t.dthr_fim_login,
                    t.cd_ramal,
                    t.cd_login,
                    b.cd_matricula,
                    LTRIM(RTRIM(UPPER(b.tx_usuario))) AS tx_usuario,
                    t.tp_duracao_login,
                    t.tp_duracao_pausas,
                    t.tp_estouro_pausas,
                    t.tp_duracao_disponivel,
                    t.tp_duracao_outros,
                    t.tx_fila,
                    LTRIM(RTRIM(UPPER(t.tx_custo))) AS tx_custo
                FROM 
                    dim_tb_000_logins_docktech t WITH(NOLOCK)
                    JOIN dim_tb_000_usuarios_matricula_docktech b WITH(NOLOCK) ON t.tx_user = b.tx_user
                WHERE
                    CAST(t.dthr_inicio_login AS DATE) BETWEEN '{data_inicio}' AND '{data_fim}'
        """
        df = pd.read_sql_query(text(query_sql), cnxn)
        return df

# ==============================
# 2. EXECUCAO E EXPORTACAO
# ==============================
def executar_e_salvar_tempo_logado_nexus():
    print("Iniciando processo de extracao Tempo Logado Nexus...")
    
    try:
        # Carrega os dados
        df = carregar_tempo_logado_nexus()

        if df.empty:
            print("A consulta nao retornou dados para o periodo.")
        else:
            # Caminhos com subpasta
            caminho_parquet = os.path.join(PASTA_DESTINO, "import_tempo_logado_nexus.parquet")
            # caminho_excel = os.path.join(PASTA_DESTINO, "import_tempo_logado_nexus.xlsx")

            # Exportação
            df.to_parquet(caminho_parquet, index=False, compression='snappy')
            # df.to_excel(caminho_excel, index=False)
            
            # print(f"Arquivo '{caminho_parquet}'")
            # print(f"Arquivo '{caminho_excel}'")
            print(f"Total de registros: {len(df)}")

    except Exception as e:
        print(f"Erro durante a execucao: {e}")

if __name__ == "__main__":
    executar_e_salvar_tempo_logado_nexus()