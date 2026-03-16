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
PASTA_DESTINO = r"C:\Users\lucas.pinto\Desktop\Site_docktech_ligacoes\arquivo_parquet_quadro_operacional"
os.makedirs(PASTA_DESTINO, exist_ok=True)

# Inicializa conexao atraves do modulo externo
login = conn.dbconnect()

# ==============================
# 1. FUNCAO DE CARREGAMENTO
# ==============================
def carregar_quadro_directive():
    
    engine = login.connProDirective
    with engine.connect() as cnxn:
        query_sql = f"""
        SELECT 
            CD_FUNCIONARIO,
            NO_FUNCIONARIO,
            DT_NASCIMENTO,
            DS_LOCAL,
            DS_OPERACAO,
            DS_FUNCAO,
            UPPER(DS_SITUACAO) AS DS_SITUACAO,
            DT_ADMISSAO,
            DT_EXPERIENCIA_FIM,
            DT_EXPERIENCIA_PRORROGACAO,
            DT_DESLIGAMENTO,
            UPPER(OB_DESLIGAMENTO) AS OB_DESLIGAMENTO,
            UPPER(OB_DESLIGAMENTO2) AS OB_DESLIGAMENTO2,
            ORIGEM_DESLIGAMENTO,
            UPPER(DS_MOTIVO_DESLIGAMENTO) AS DS_MOTIVO_DESLIGAMENTO,
            DS_RAZAO_DESLIGAMENTO,
            cached_at AS DT_ATUALIZACAO_DIRECTIVE
        FROM 
            CACHE_FUNCIONARIO WITH(NOLOCK)
        WHERE
            DS_OPERACAO LIKE '%DOCK%'
            --AND CD_FUNCIONARIO = 21989
        """
        df = pd.read_sql_query(text(query_sql), cnxn)
        return df
    
# ==============================
# 2. EXECUCAO E EXPORTACAO
# ==============================
def executar_e_salvar_quadro_directive():
    print("Iniciando processo de extracao Quadro Directive...")
    
    try:
        # Carrega os dados
        df = carregar_quadro_directive()

        if df.empty:
            print("A consulta nao retornou dados para o periodo.")
        else:
            # Caminhos com subpasta
            caminho_parquet = os.path.join(PASTA_DESTINO, "import_quadro_directive.parquet")
            # caminho_excel = os.path.join(PASTA_DESTINO, "import_quadro_directive.xlsx")

            # Exportação
            df.to_parquet(caminho_parquet, index=False, compression='snappy')
            # df.to_excel(caminho_excel, index=False)
            
            # print(f"Arquivo '{caminho_parquet}'")
            # print(f"Arquivo '{caminho_excel}'")
            print(f"Total de registros: {len(df)}")

    except Exception as e:
        print(f"Erro durante a execucao: {e}")

if __name__ == "__main__":
    executar_e_salvar_quadro_directive()