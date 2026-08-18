import pandas as pd
from sqlalchemy import text
import sys
import os
# Caminho de conexao
sys.path.append(r'\\192.168.5.15\mis\Funcoes')
import conn
from aux_data_sistema import obter_datas
from sqlalchemy import text

# Configuracao de destino na rede
# PASTA_DESTINO = r"\\192.168.5.15\mis\Pessoal\Lucas\Site_docktech_ligacoes\arquivos_parquet_login_senior"
# Localmente para testes
PASTA_DESTINO = r"C:\Users\lucas.pinto\Desktop\extracao_bases_docktech\arquivos_parquet_login_senior"
os.makedirs(PASTA_DESTINO, exist_ok=True)

# 1. Ler o arquivo Parquet e extrair a lista de matrículas
caminho_parquet = r"C:\Users\lucas.pinto\Desktop\extracao_bases_docktech\arquivo_parquet_quadro_operacional\import_quadro_operacional.parquet"
df_quadro = pd.read_parquet(caminho_parquet)

# Extrai os valores únicos da coluna e remove possíveis nulos
matriculas_unicas = df_quadro['cd_matricula'].dropna().unique().tolist()

# 2. Converte a lista em uma string formatada para o SQL "13005, 14204, 14488, ..."
matriculas_str = ",".join(map(str, matriculas_unicas))

login = conn.dbconnect()

datas = obter_datas()
data_limite = datas['inicio']

def carregar_e_transformar_ponto_senior():
    engine = login.connProVetorh
    
    # Query crua: apenas extracao, sem pivotar
    query_sql = text(f"""
        SELECT
            a.numcra AS cd_matricula,
            a.datacc AS dt_ponto,
            a.horacc,
            LTRIM(RTRIM(UPPER(b.nomfun))) AS tx_funcionario,
            b.datadm AS dt_admissao,
            b.datafa AS dt_afastamento,
            c.nomesc AS tx_escala
        FROM
            r070acc a WITH(NOLOCK)
            JOIN r034fun b WITH(NOLOCK) ON a.numcra = b.numcad
            JOIN r006esc c WITH(NOLOCK) ON b.codesc = c.codesc
        WHERE
            b.numcad IN ({matriculas_str}) 
            AND a.datacc >= :data_inicio
    """)
    
    with engine.connect() as cnxn:
        df_ponto = pd.read_sql(
            query_sql, 
            cnxn, 
            params={"data_inicio": data_limite}
        )
        return df_ponto

    # ==================================================
    # LOGICA DE TRANSFORMACAO
    # ==================================================
    
    # 1. Formatar a hora para o padrão 'HH:MM:SS.0000000'
    def formatar_hora(minutos):
        h = minutos // 60
        m = minutos % 60
        return f"{h:02d}:{m:02d}:00.0000000"

    df['ht_hora_ponto'] = df['horacc'].apply(formatar_hora)
    
    # 2. Criar a sequencia de pontos (equivalente ao ROW_NUMBER)
    df = df.sort_values(['cd_matricula', 'dt_ponto', 'horacc'])
    df['n_ponto'] = df.groupby(['cd_matricula', 'dt_ponto']).cumcount() + 1
    
    # 3. Pivotar a tabela
    pivot_df = df.pivot_table(
        index=['cd_matricula', 'dt_ponto', 'tx_funcionario', 'tx_escala', 'dt_admissao', 'dt_afastamento'],
        columns='n_ponto',
        values='ht_hora_ponto',
        aggfunc='first'
    ).reset_index()

    # 4. Ajustar colunas: garantir que existam de 1 a 8
    for i in range(1, 9):
        if i not in pivot_df.columns:
            pivot_df[i] = None
    
    pivot_df.rename(columns={i: f'HoraPonto{i}' for i in range(1, 9)}, inplace=True)
    
    # 5. Formatar colunas de data para YYYY-MM-DD
    colunas_de_data = ['dt_ponto', 'dt_admissao', 'dt_afastamento']
    for col in colunas_de_data:
        if col in pivot_df.columns:
            # Converte para datetime, extrai o date, e formata como string
            pivot_df[col] = pd.to_datetime(pivot_df[col], errors='coerce').dt.date
            # Se for nulo, mantem como None (vazio no Excel), se nao, formata
            pivot_df[col] = pivot_df[col].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else None)
    
    # 6. Ajustar ordem das colunas
    colunas_finais = ['cd_matricula', 'dt_ponto', 'tx_funcionario', 'tx_escala'] + \
                     [f'HoraPonto{i}' for i in range(1, 9)] + \
                     ['dt_admissao', 'dt_afastamento']
    
    pivot_df = pivot_df[colunas_finais]
    pivot_df['tx_funcionario'] = pivot_df['tx_funcionario'].str.lower()
    
    return pivot_df

def executar_e_salvar_ponto_senior():
    print("Iniciando processo de extracao e transformacao Ponto Senior...")
    try:
        df = carregar_e_transformar_ponto_senior()
        
        caminho_parquet = os.path.join(PASTA_DESTINO, "import_ponto_senior.parquet")
        # caminho_excel = os.path.join(PASTA_DESTINO, "import_tempo_logado_senior.xlsx")
        # df.to_excel(caminho_excel, index=False)
        df.to_parquet(caminho_parquet, index=False, compression='snappy')
        
        # print(f"Arquivo gerado com sucesso: {caminho_parquet}")
        # print(f"Arquivo gerado com sucesso: {caminho_excel}")
        print(f"Total de registros processados: {len(df)}")
    except Exception as e:
        print(f"Erro durante a execucao: {e}")

if __name__ == "__main__":
    executar_e_salvar_ponto_senior()