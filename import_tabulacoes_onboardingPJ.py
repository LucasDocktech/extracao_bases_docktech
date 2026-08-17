import pandas as pd
from sqlalchemy import text
import sys
import os
# Adicionando caminho para buscar o modulo de conexao
sys.path.append(r'\\192.168.5.15\mis\Funcoes')
import conn
from aux_data_sistema import obter_datas

# Configuração da pasta de destino
# PASTA_DESTINO = r"\\192.168.5.15\mis\Pessoal\Lucas\Site_docktech_ligacoes\arquivos_parquet_tabulacoes"
# Pasta para testes locais
PASTA_DESTINO = r"C:\Users\lucas.pinto\Desktop\extracao_bases_docktech\arquivos_parquet_tabulacoes"
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
def carregar_tabulacoes_OnboardingPJ():
    engine = login.connProDockTech
    with engine.connect() as cnxn:
        query_sql = f"""
        SELECT
            'OnboardingPJ' AS Tabulador,
            t.DtCadastro AS Tabulacao_DtCadastro,
            t.DataDaEntrada,
            t.DataInicio,
            t.IdEmissor AS Emissor,
            t.Cnpj AS CNPJ,
            LTRIM(RTRIM(UPPER(t.Empressa))) AS Empressa,
            t.Porte,
            LTRIM(RTRIM(UPPER(t.Status))) AS Tabulacao_Status,
            LTRIM(RTRIM(UPPER(t.MotivoDoStatus))) AS Tabulacao_MotivoDoStatus,
            --t.Observacao,
            LTRIM(RTRIM(UPPER(p.Nome))) AS Analista_dbm
        FROM 
            TtbuladorOnboardingPJ t WITH(NOLOCK)
            LEFT JOIN Tusuario u WITH(NOLOCK) ON t.FkUsuarioOperador = u.Id
            LEFT JOIN Tpessoa p WITH(NOLOCK) ON u.FkPessoa = p.Id
        WHERE
            p.Nome IS NOT NULL
        """
        df = pd.read_sql_query(text(query_sql), cnxn)
        return df

# ==============================
# 2. EXECUCAO E EXPORTACAO
# ==============================
def executar_e_salvar_tabulacoes_OnboardingPJ():
    print("Iniciando processo de extracao Tabulacoes OnboardingPJ...")
    
    try:
        # Carrega os dados
        df = carregar_tabulacoes_OnboardingPJ()

        if df.empty:
            print("A consulta nao retornou dados para o periodo informando no arquivo de aux_data_sistema.py")
        else:
            # Caminhos com subpasta
            caminho_parquet = os.path.join(PASTA_DESTINO, "import_tabulacoes_OnboardingPJ.parquet")
            # caminho_excel = os.path.join(PASTA_DESTINO, "import_tabulacoes_OnboardingPJ.xlsx")

            # Exportação
            df.to_parquet(caminho_parquet, index=False, compression='snappy')
            # df.to_excel(caminho_excel, index=False)
            
            # print(f"Arquivo '{caminho_parquet}'")
            # print(f"Arquivo '{caminho_excel}'")
            print(f"Total de registros: {len(df)}")

    except Exception as e:
        print(f"Erro durante a execucao: {e}")

if __name__ == "__main__":
    executar_e_salvar_tabulacoes_OnboardingPJ()