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
PASTA_DESTINO = r"C:\Users\lucas.pinto\Desktop\Site_docktech_ligacoes\arquivos_parquet_tabulacoes"
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
def carregar_tabulacoes_n3_master():
    engine = login.connProDockTech
    with engine.connect() as cnxn:
        # Ajustado para incluir aspas simples nas datas da query
        query_sql = f"""
        SELECT
            'Master' AS Tabulador,
            b.Id,
            b.ClaimID,
            t.DtCadastro AS Tabulacao_DtCadastro,
            b.DtCadastro,
            CONVERT(VARCHAR(19),TRY_CONVERT(DATETIME, b.OriginalTransactionDate, 103),120) AS OriginalTransactionDate,
            d.DsEmissor,
            LTRIM(RTRIM(UPPER(t.Status))) AS Status,
            LTRIM(RTRIM(UPPER(t.MotivoDoStatus))) AS MotivoDoStatus,
            LTRIM(RTRIM(UPPER(p.Nome))) AS Nome
        FROM
            TbaseTabuladorEmissoresMaster b WITH(NOLOCK)
            LEFT JOIN TtbuladorEmissorMaster t WITH(NOLOCK) ON b.Id = t.FkTbaseTabuladorEmissoresMaster
            LEFT JOIN TemissoresDescricaoMaster d WITH(NOLOCK) ON b.FkTipoEmissor = d.Id
            LEFT JOIN Tusuario u WITH(NOLOCK) ON t.FkUsuarioOperador = u.Id
            LEFT JOIN Tpessoa p WITH(NOLOCK) ON u.FkPessoa = p.Id
        WHERE 
            CAST(b.DtCadastro AS DATE) BETWEEN '{data_inicio}' AND '{data_fim}'
        """
        df = pd.read_sql_query(text(query_sql), cnxn)
        return df

# ==============================
# 2. EXECUCAO E EXPORTACAO
# ==============================
def executar_e_salvar_tabulacoes_n3_master():
    print("Iniciando processo de extracao e salvamento Tabulacoes N3 Master...")
    
    try:
        # 1. Obter dados novos do SQL
        df_novo = carregar_tabulacoes_n3_master()
        
        if df_novo.empty:
            print("Nenhum dado novo retornado para o período.")
            return

        caminho_parquet = os.path.join(PASTA_DESTINO, "import_tabulacoes_n3_master.parquet")

        # 2. Lógica de Upsert baseada no ID único do registro
        if os.path.exists(caminho_parquet):
            print("Carregando histórico e mesclando...")
            df_historico = pd.read_parquet(caminho_parquet)
            
            # Concatena o histórico com os novos dados
            df_concatenado = pd.concat([df_historico, df_novo], ignore_index=True)
            
            # Remove duplicatas baseadas no 'Id' do registro. 
            # Como cada status tem um Id diferente, todos os históricos serão mantidos.
            df_final = df_concatenado.drop_duplicates(subset=['Id'], keep='last')
        else:
            print("Primeira carga detectada. Criando arquivo novo.")
            df_final = df_novo

        # 3. Exportação
        df_final.to_parquet(caminho_parquet, index=False, compression='snappy')
        
        print(f"Processo finalizado. Total de linhas no arquivo: {len(df_final)}")

    except Exception as e:
        print(f"Erro durante a execução: {e}")

if __name__ == "__main__":
    executar_e_salvar_tabulacoes_n3_master()