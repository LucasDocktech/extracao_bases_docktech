import os
import pandas as pd

# ==============================
# 1. DEFINIR CAMINHOS
# ==============================

# Caminho da raiz do projeto (onde o script está)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pasta onde está o parquet (exemplo: /dados/arquivo.parquet)
caminho_parquet = os.path.join(BASE_DIR, "nivel_dois_bases_app","Arquivos_parquet_nv_2", "quadro_geral.parquet")

# Caminho de saída do Excel
caminho_excel = r"C:\Users\lucas.pinto\Desktop\Arquivos Excel RPA Dock\quadro_geral.xlsx"

# ==============================
# 2. LEITURA DO PARQUET
# ==============================

df = pd.read_parquet(caminho_parquet)

print("Arquivo Parquet lido com sucesso!")
print(f"Total de registros: {len(df)}")

# ==============================
# 3. EXPORTAR PARA EXCEL
# ==============================

df.to_excel(caminho_excel, index=False)

print("Arquivo exportado para Excel com sucesso!")
print(f"Local do arquivo: {caminho_excel}")




