import pandas as pd
import numpy as np
import os
from dateutil.relativedelta import relativedelta

# Configuração dos caminhos na rede
# BASE_PATH = r"\\192.168.5.15\mis\Pessoal\Lucas\Site_docktech_ligacoes"
# Localmente para testes
BASE_PATH = r"C:\Users\lucas.pinto\Desktop\extracao_bases_docktech"
PASTA_ENTRADA = os.path.join(BASE_PATH, "arquivo_parquet_quadro_operacional")

caminho_op = os.path.join(PASTA_ENTRADA, "import_quadro_operacional.parquet")
caminho_dir = os.path.join(PASTA_ENTRADA, "import_quadro_directive.parquet")


def formatar_carga_horaria(td):
    segundos = int(td.total_seconds())
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60

    return f"{horas}H" if minutos == 0 else f"{horas}H:{minutos:02d}"


def formatar_jornada_item(td):
    segundos = int(td.total_seconds())
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60

    return f"{horas:02d}H" if minutos == 0 else f"{horas:02d}H:{minutos:02d}"


# NOVA FUNÇÃO PARA CALCULAR ANOS E MESES
def calcular_tempo_empresa(row):
    if pd.notna(row['DT_ADMISSAO']):
        data_final = row['DT_DESLIGAMENTO'] if pd.notna(row['DT_DESLIGAMENTO']) else row['DT_ATUAL']
        diff = relativedelta(data_final, row['DT_ADMISSAO'])

        return f"{diff.years} anos {diff.months} meses"

    return None


def processar_quadro_geral():

    print("Iniciando a consolidação do Quadro Geral...")

    try:

        df_op = pd.read_parquet(caminho_op)
        df_dir = pd.read_parquet(caminho_dir)

        df_op['cd_matricula'] = df_op['cd_matricula'].astype(str)
        df_dir['CD_FUNCIONARIO'] = df_dir['CD_FUNCIONARIO'].astype(str)

        df = pd.merge(
            df_op,
            df_dir,
            left_on='cd_matricula',
            right_on='CD_FUNCIONARIO',
            how='inner'
        )

        # 1. Conversão para datetime para cálculos matemáticos
        cols_data = [
            'DT_ADMISSAO',
            'DT_NASCIMENTO',
            'DT_EXPERIENCIA_FIM',
            'DT_EXPERIENCIA_PRORROGACAO',
            'DT_DESLIGAMENTO'
        ]

        for col in cols_data:
            df[col] = pd.to_datetime(df[col], errors='coerce')

        # 2. Criar DT_ATUAL (Data de hoje sem o horário)
        df['DT_ATUAL'] = pd.Timestamp.now().normalize()

        # 3. Calcular IDADE
        nasc = df['DT_NASCIMENTO']

        df['IDADE'] = df['DT_ATUAL'].dt.year - nasc.dt.year - (
            (df['DT_ATUAL'].dt.month < nasc.dt.month) |
            (
                (df['DT_ATUAL'].dt.month == nasc.dt.month) &
                (df['DT_ATUAL'].dt.day < nasc.dt.day)
            )
        )

        # 4. FAIXA_ETARIA
        bins = [0, 18, 25, 35, 45, 150]
        labels = ["Menor de 18", "18 - 25", "25 - 35", "35 - 45", "45+"]

        df['FAIXA_ETARIA'] = pd.cut(
            df['IDADE'],
            bins=bins,
            labels=labels,
            right=False
        )

        # 5. SUB_SITUACAO
        df['DT_REF'] = df['DT_EXPERIENCIA_PRORROGACAO'].fillna(df['DT_EXPERIENCIA_FIM'])

        df['SUB_SITUACAO'] = np.where(
            df['DT_DESLIGAMENTO'].notna(),
            np.where(
                df['DT_DESLIGAMENTO'] <= df['DT_REF'],
                "Desligado no período de experiência",
                "Desligado após período de experiência"
            ),
            np.where(
                df['DT_ATUAL'] > df['DT_REF'],
                "Efetivado",
                "Em Experiência"
            )
        )

        # Flag de Mortalidade Onboarding (<= 90 dias)
        df['DIAS_CASA_ATE_DESLIGAMENTO'] = (
            df['DT_DESLIGAMENTO'] - df['DT_ADMISSAO']
        ).dt.days

        df['MORTALIDADE_<_90_DIAS'] = df['DIAS_CASA_ATE_DESLIGAMENTO'] <= 90

        # NOVA COLUNA COM ANOS E MESES
        df['TEMPO_EMPRESA'] = df.apply(calcular_tempo_empresa, axis=1)
        df['MES_ADMISSAO'] = df['DT_ADMISSAO'].dt.strftime('%b')
        df['ANO_ADMISSAO'] = df['DT_ADMISSAO'].dt.year
        df['MES_DESLIGAMENTO'] = df['DT_DESLIGAMENTO'].dt.strftime('%b')
        df['ANO_DESLIGAMENTO'] = df['DT_DESLIGAMENTO'].dt.year
        
        # 6. Formatação das colunas de tempo e jornada
        df.drop(columns=['tx_escala', 'cd_cpf'], errors='ignore', inplace=True)

        for col in ['tm_entrada', 'tm_saida', 'tm_carga_horaria']:
            df[col] = pd.to_timedelta(df[col].astype(str))

        df['Jornada'] = df.apply(
            lambda row: f"{formatar_jornada_item(row['tm_entrada'])} - {formatar_jornada_item(row['tm_saida'])}",
            axis=1
        )

        df['tm_carga_horaria'] = df['tm_carga_horaria'].apply(formatar_carga_horaria)

        df['tm_entrada'] = df['tm_entrada'].dt.components.apply(
            lambda x: f"{x['hours']:02d}:{x['minutes']:02d}:00",
            axis=1
        )

        df['tm_saida'] = df['tm_saida'].dt.components.apply(
            lambda x: f"{x['hours']:02d}:{x['minutes']:02d}:00",
            axis=1
        )

        # 7. Formatando todas as datas para string DD/MM/AAAA (último passo)
        for col in cols_data + ['DT_ATUAL']:
            df[col] = df[col].dt.strftime('%d/%m/%Y')

        df.drop(columns=['DT_REF'], errors='ignore', inplace=True)

        # --- Bloco de exportação para Excel ---
        # caminho_excel = r"C:\Users\lucas.pinto\Desktop\Arquivos Excel RPA Dock\validacao_quadro_geral_formato_v2.xlsx"
        # --- Bloco de exportação para Parquet ---
        # Caminho para rede
        # caminho_parquet = r"\\192.168.5.15\mis\Pessoal\Lucas\Site_docktech_ligacoes\nivel_dois_bases_app\Arquivos_parquet_nv_2\quadro_geral.parquet"
        # Pasta local para testes
        caminho_parquet = r"C:\Users\lucas.pinto\Desktop\extracao_bases_docktech\nivel_dois_bases_app\Arquivos_parquet_nv_2\quadro_geral.parquet"
        
        os.makedirs(os.path.dirname(caminho_parquet), exist_ok=True)
        df.to_parquet(caminho_parquet, index=False)

        print(f"\n[VALIDAÇÃO] Arquivo exportado com sucesso: {caminho_parquet}")

        # --------------------------------------

        print("\n--- Consolidação Finalizada ---")
        print(f"Total de registros: {len(df)}")

        print("\nVerificação das novas colunas (Primeiras 5 linhas):")

        print(
            df[
                ['cd_matricula', 'IDADE', 'FAIXA_ETARIA', 'SUB_SITUACAO', 'TEMPO_EMPRESA']
            ].head().to_string()
        )

    except Exception as e:
        print(f"Erro durante a consolidação: {e}")


if __name__ == "__main__":
    processar_quadro_geral()