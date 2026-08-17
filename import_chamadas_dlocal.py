import pandas as pd
from sqlalchemy import text
import streamlit as st
import sys
import os
# Adicionando caminho para buscar o modulo de conexao
sys.path.append(r'\\192.168.5.15\mis\Funcoes')
import conn
from aux_data_sistema import obter_datas

# Configuração da pasta de destino na rede
# PASTA_DESTINO = r"\\192.168.5.15\mis\Pessoal\Lucas\Site_docktech_ligacoes\arquivos_parquet_chamadas"
# Pasta local para testes
PASTA_DESTINO = r"C:\Users\lucas.pinto\Desktop\Site_docktech_ligacoes\arquivos_parquet_chamadas"
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
def carregar_chamadas_dlocal():
    # Utiliza a engine vinda do modulo conn
    engine = login.connDbmHAC
    with engine.connect() as cnxn:
        query_sql = f"""
            WITH tbl_dlocal_telefonia_completa AS (
                -- Parte 1: Todas as chamadas NAO ATENDIDAS ou com FALHA
                SELECT 
                    titulo, datahora, data, hora, horaatende, uniqueid, linkedid, direcao, status, ddd, idestado, custo, fila, cadastro, usuario, ura, tabulacao, subtabulacao, iduranome, uranome, uracampos, urahistorico, pesquisa, pesquisaperguntas, pesquisarespostas, pesquisatransfere, pesquisa1, pesquisa2, pesquisa3, 
                    uracampos ->> 'REF10' AS REF10, 
                    uracampos ->> 'REF14' AS REF14, 
                    uracampos ->> 'REF11' AS REF11, 
                    uracampos ->> 'REF12' AS REF12, 
                    clientedesligou, numero, tempototal, tempoespera, tempoatende, todos, atendimento, naoatendimento, ocupado, falhas, entrante, sainte, interna, contareceptivo, contareceptivoatendimento, contareceptivoatendimentoantesns, contareceptivoatendimentoaposns, contareceptivoabandono, contareceptivoabandonoantes10, contareceptivoabandonoantesns, contareceptivoabandonoaposns, contareceptivoforahorario, contaativo, contaativoatendimento, contaativoexternoatendimento, contaativoexternonaoatendimento, contaativointernoatendimento, contaativointernonaoatendimento 
                FROM ligacao_receptivo_abandono WHERE custo LIKE 'DLOCAL%%'
                UNION ALL
                SELECT 
                    titulo, datahora, data, hora, horaatende, uniqueid, linkedid, direcao, status, ddd, idestado, custo, fila, cadastro, usuario, ura, tabulacao, subtabulacao, iduranome, uranome, uracampos, urahistorico, pesquisa, pesquisaperguntas, pesquisarespostas, pesquisatransfere, pesquisa1, pesquisa2, pesquisa3, uracampos ->> 'REF10', uracampos ->> 'REF14', uracampos ->> 'REF11', uracampos ->> 'REF12', clientedesligou, numero, tempototal, tempoespera, tempoatende, todos, atendimento, naoatendimento, ocupado, falhas, entrante, sainte, interna, contareceptivo, contareceptivoatendimento, contareceptivoatendimentoantesns, contareceptivoatendimentoaposns, contareceptivoabandono, contareceptivoabandonoantes10, contareceptivoabandonoantesns, contareceptivoabandonoaposns, contareceptivoforahorario, contaativo, contaativoatendimento, contaativoexternoatendimento, contaativoexternonaoatendimento, contaativointernoatendimento, contaativointernonaoatendimento 
                FROM ligacao_receptivo_desistencia WHERE custo LIKE 'DLOCAL%%'
                UNION ALL
                SELECT 
                    titulo, datahora, data, hora, horaatende, uniqueid, linkedid, direcao, status, ddd, idestado, custo, fila, cadastro, usuario, ura, tabulacao, subtabulacao, iduranome, uranome, uracampos, urahistorico, pesquisa, pesquisaperguntas, pesquisarespostas, pesquisatransfere, pesquisa1, pesquisa2, pesquisa3, uracampos ->> 'REF10', uracampos ->> 'REF14', uracampos ->> 'REF11', uracampos ->> 'REF12', clientedesligou, numero, tempototal, tempoespera, tempoatende, todos, atendimento, naoatendimento, ocupado, falhas, entrante, sainte, interna, contareceptivo, contareceptivoatendimento, contareceptivoatendimentoantesns, contareceptivoatendimentoaposns, contareceptivoabandono, contareceptivoabandonoantes10, contareceptivoabandonoantesns, contareceptivoabandonoaposns, contareceptivoforahorario, contaativo, contaativoatendimento, contaativoexternoatendimento, contaativoexternonaoatendimento, contaativointernoatendimento, contaativointernonaoatendimento 
                FROM ligacao_receptivo_caixapostal WHERE custo LIKE 'DLOCAL%%'
                UNION ALL
                SELECT 
                    titulo, datahora, data, hora, horaatende, uniqueid, linkedid, direcao, status, ddd, idestado, custo, fila, cadastro, usuario, ura, tabulacao, subtabulacao, iduranome, uranome, uracampos, urahistorico, pesquisa, pesquisaperguntas, pesquisarespostas, pesquisatransfere, pesquisa1, pesquisa2, pesquisa3, uracampos ->> 'REF10', uracampos ->> 'REF14', uracampos ->> 'REF11', uracampos ->> 'REF12', clientedesligou, numero, tempototal, tempoespera, tempoatende, todos, atendimento, naoatendimento, ocupado, falhas, entrante, sainte, interna, contareceptivo, contareceptivoatendimento, contareceptivoatendimentoantesns, contareceptivoatendimentoaposns, contareceptivoabandono, contareceptivoabandonoantes10, contareceptivoabandonoantesns, contareceptivoabandonoaposns, contareceptivoforahorario, contaativo, contaativoatendimento, contaativoexternoatendimento, contaativoexternonaoatendimento, contaativointernoatendimento, contaativointernonaoatendimento 
                FROM ligacao_receptivo_forahorario WHERE custo LIKE 'DLOCAL%%'
                UNION ALL
                SELECT 
                    titulo, datahora, data, hora, horaatende, uniqueid, linkedid, direcao, status, ddd, idestado, custo, fila, cadastro, usuario, ura, tabulacao, subtabulacao, iduranome, uranome, uracampos, urahistorico, pesquisa, pesquisaperguntas, pesquisarespostas, pesquisatransfere, pesquisa1, pesquisa2, pesquisa3, uracampos ->> 'REF10', uracampos ->> 'REF14', uracampos ->> 'REF11', uracampos ->> 'REF12', clientedesligou, numero, tempototal, tempoespera, tempoatende, todos, atendimento, naoatendimento, ocupado, falhas, entrante, sainte, interna, contareceptivo, contareceptivoatendimento, contareceptivoatendimentoantesns, contareceptivoatendimentoaposns, contareceptivoabandono, contareceptivoabandonoantes10, contareceptivoabandonoantesns, contareceptivoabandonoaposns, contareceptivoforahorario, contaativo, contaativoatendimento, contaativoexternoatendimento, contaativoexternonaoatendimento, contaativointernoatendimento, contaativointernonaoatendimento 
                FROM ligacao_receptivo_forahorario_hist WHERE custo LIKE 'DLOCAL%%'
                UNION ALL
                SELECT 
                    titulo, datahora, data, hora, horaatende, uniqueid, linkedid, direcao, status, ddd, idestado, custo, fila, cadastro, usuario, ura, tabulacao, subtabulacao, iduranome, uranome, uracampos, urahistorico, pesquisa, pesquisaperguntas, pesquisarespostas, pesquisatransfere, pesquisa1, pesquisa2, pesquisa3, uracampos ->> 'REF10', uracampos ->> 'REF14', uracampos ->> 'REF11', uracampos ->> 'REF12', clientedesligou, numero, tempototal, tempoespera, tempoatende, todos, atendimento, naoatendimento, ocupado, falhas, entrante, sainte, interna, contareceptivo, contareceptivoatendimento, contareceptivoatendimentoantesns, contareceptivoatendimentoaposns, contareceptivoabandono, contareceptivoabandonoantes10, contareceptivoabandonoantesns, contareceptivoabandonoaposns, contareceptivoforahorario, contaativo, contaativoatendimento, contaativoexternoatendimento, contaativoexternonaoatendimento, contaativointernoatendimento, contaativointernonaoatendimento 
                FROM ligacao_receptivofalha_generica WHERE custo LIKE 'DLOCAL%%'
                UNION ALL
                SELECT 
                    titulo, datahora, data, hora, horaatende, uniqueid, linkedid, direcao, status, ddd, idestado, custo, fila, cadastro, usuario, ura, tabulacao, subtabulacao, iduranome, uranome, uracampos, urahistorico, pesquisa, pesquisaperguntas, pesquisarespostas, pesquisatransfere, pesquisa1, pesquisa2, pesquisa3, uracampos ->> 'REF10', uracampos ->> 'REF14', uracampos ->> 'REF11', uracampos ->> 'REF12', clientedesligou, numero, tempototal, tempoespera, tempoatende, todos, atendimento, naoatendimento, ocupado, falhas, entrante, sainte, interna, contareceptivo, contareceptivoatendimento, contareceptivoatendimentoantesns, contareceptivoatendimentoaposns, contareceptivoabandono, contareceptivoabandonoantes10, contareceptivoabandonoantesns, contareceptivoabandonoaposns, contareceptivoforahorario, contaativo, contaativoatendimento, contaativoexternoatendimento, contaativoexternonaoatendimento, contaativointernoatendimento, contaativointernonaoatendimento 
                FROM ligacao_receptivo_timeout WHERE custo LIKE 'DLOCAL%%'
                UNION ALL
                SELECT 
                    titulo, datahora, data, hora, horaatende, uniqueid, linkedid, direcao, status, ddd, idestado, custo, fila, cadastro, usuario, ura, tabulacao, subtabulacao, iduranome, uranome, uracampos, urahistorico, pesquisa, pesquisaperguntas, pesquisarespostas, pesquisatransfere, pesquisa1, pesquisa2, pesquisa3, uracampos ->> 'REF10', uracampos ->> 'REF14', uracampos ->> 'REF11', uracampos ->> 'REF12', clientedesligou, numero, tempototal, tempoespera, tempoatende, todos, atendimento, naoatendimento, ocupado, falhas, entrante, sainte, interna, contareceptivo, contareceptivoatendimento, contareceptivoatendimentoantesns, contareceptivoatendimentoaposns, contareceptivoabandono, contareceptivoabandonoantes10, contareceptivoabandonoantesns, contareceptivoabandonoaposns, contareceptivoforahorario, contaativo, contaativoatendimento, contaativoexternoatendimento, contaativoexternonaoatendimento, contaativointernoatendimento, contaativointernonaoatendimento 
                FROM ligacao_receptivofalha_generica_hist WHERE custo LIKE 'DLOCAL%%'
                UNION ALL
                SELECT 
                    titulo, datahora, data, hora, horaatende, uniqueid, linkedid, direcao, status, ddd, idestado, custo, fila, cadastro, usuario, ura, tabulacao, subtabulacao, iduranome, uranome, uracampos, urahistorico, pesquisa, pesquisaperguntas, pesquisarespostas, pesquisatransfere, pesquisa1, pesquisa2, pesquisa3, uracampos ->> 'REF10', uracampos ->> 'REF14', uracampos ->> 'REF11', uracampos ->> 'REF12', clientedesligou, numero, tempototal, tempoespera, tempoatende, todos, atendimento, naoatendimento, ocupado, falhas, entrante, sainte, interna, contareceptivo, contareceptivoatendimento, contareceptivoatendimentoantesns, contareceptivoatendimentoaposns, contareceptivoabandono, contareceptivoabandonoantes10, contareceptivoabandonoantesns, contareceptivoabandonoaposns, contareceptivoforahorario, contaativo, contaativoatendimento, contaativoexternoatendimento, contaativoexternonaoatendimento, contaativointernoatendimento, contaativointernonaoatendimento 
                FROM ligacao_receptivoura_falha WHERE custo LIKE 'DLOCAL%%'
                UNION ALL
                SELECT 
                    titulo, datahora, data, hora, horaatende, uniqueid, linkedid, direcao, status, ddd, idestado, custo, fila, cadastro, usuario, ura, tabulacao, subtabulacao, iduranome, uranome, uracampos, urahistorico, pesquisa, pesquisaperguntas, pesquisarespostas, pesquisatransfere, pesquisa1, pesquisa2, pesquisa3, uracampos ->> 'REF10', uracampos ->> 'REF14', uracampos ->> 'REF11', uracampos ->> 'REF12', clientedesligou, numero, tempototal, tempoespera, tempoatende, todos, atendimento, naoatendimento, ocupado, falhas, entrante, sainte, interna, contareceptivo, contareceptivoatendimento, contareceptivoatendimentoantesns, contareceptivoatendimentoaposns, contareceptivoabandono, contareceptivoabandonoantes10, contareceptivoabandonoantesns, contareceptivoabandonoaposns, contareceptivoforahorario, contaativo, contaativoatendimento, contaativoexternoatendimento, contaativoexternonaoatendimento, contaativointernoatendimento, contaativointernonaoatendimento 
                FROM ligacao_receptivoura_naotransferido WHERE custo LIKE 'DLOCAL%%'
                UNION ALL
                SELECT titulo, datahora, data, hora, horaatende, uniqueid, linkedid, direcao, status, ddd, idestado, custo, fila, cadastro, usuario, ura, tabulacao, subtabulacao, iduranome, uranome, uracampos, urahistorico, pesquisa, pesquisaperguntas, pesquisarespostas, pesquisatransfere, pesquisa1, pesquisa2, pesquisa3, 
                        uracampos ->> 'REF10' AS REF10, 
                        uracampos ->> 'REF14' AS REF14, 
                        uracampos ->> 'REF11' AS REF11, 
                        uracampos ->> 'REF12' AS REF12, 
                        clientedesligou, numero, tempototal, tempoespera, tempoatende, todos, atendimento, naoatendimento, ocupado, falhas, entrante, sainte, interna, contareceptivo, contareceptivoatendimento, contareceptivoatendimentoantesns, contareceptivoatendimentoaposns, contareceptivoabandono, contareceptivoabandonoantes10, contareceptivoabandonoantesns, contareceptivoabandonoaposns, contareceptivoforahorario, contaativo, contaativoatendimento, contaativoexternoatendimento, contaativoexternonaoatendimento, contaativointernoatendimento, contaativointernonaoatendimento
                FROM ligacao_ativoexterno_atendimento WHERE custo LIKE 'DLOCAL%%'
                UNION ALL
                SELECT titulo, datahora, data, hora, horaatende, uniqueid, linkedid, direcao, status, ddd, idestado, custo, fila, cadastro, usuario, ura, tabulacao, subtabulacao, iduranome, uranome, uracampos, urahistorico, pesquisa, pesquisaperguntas, pesquisarespostas, pesquisatransfere, pesquisa1, pesquisa2, pesquisa3, 
                        uracampos ->> 'REF10' AS REF10, 
                        uracampos ->> 'REF14' AS REF14, 
                        uracampos ->> 'REF11' AS REF11, 
                        uracampos ->> 'REF12' AS REF12, 
                        clientedesligou, numero, tempototal, tempoespera, tempoatende, todos, atendimento, naoatendimento, ocupado, falhas, entrante, sainte, interna, contareceptivo, contareceptivoatendimento, contareceptivoatendimentoantesns, contareceptivoatendimentoaposns, contareceptivoabandono, contareceptivoabandonoantes10, contareceptivoabandonoantesns, contareceptivoabandonoaposns, contareceptivoforahorario, contaativo, contaativoatendimento, contaativoexternoatendimento, contaativoexternonaoatendimento, contaativointernoatendimento, contaativointernonaoatendimento
                FROM ligacao_ativoexterno_naoatendimento WHERE custo LIKE 'DLOCAL%%'
                UNION ALL
                -- Parte 2: Todas as chamadas ATENDIDAS
                SELECT
                    titulo, datahora, data, hora, horaatende, uniqueid, linkedid, direcao, status, ddd, idestado, custo, fila, cadastro, usuario, ura, tabulacao, subtabulacao, iduranome, uranome, uracampos, urahistorico,  pesquisa, pesquisaperguntas, pesquisarespostas, pesquisatransfere, pesquisa1, pesquisa2, pesquisa3,
                    CASE
                        WHEN uranome = 'URA-DLOCAL-307050-clone' THEN uracampos ->> 'REF10'
                        WHEN uranome = 'URA-DLOCAL-PS-453243' THEN
                            COALESCE(uracampos ->> 'AVALIACAOATENDIMENTO', CASE WHEN POSITION('AVALIACAO ATENDIMENTO' IN urahistorico) <> 0 THEN SUBSTRING(urahistorico, POSITION('AVALIACAO ATENDIMENTO' IN urahistorico) + 23, 1) ELSE NULL END)
                    END AS REF10,
                    CASE
                        WHEN uranome = 'URA-DLOCAL-307050-clone' THEN uracampos ->> 'REF14'
                        WHEN uranome = 'URA-DLOCAL-PS-453243' THEN
                            COALESCE(uracampos ->> 'AVALIACAOEXPERIENCIA', CASE WHEN POSITION('AVALIACAO EXPERIENCIA' IN urahistorico) <> 0 THEN SUBSTRING(urahistorico, POSITION('AVALIACAO EXPERIENCIA' IN urahistorico) + 24, 1) ELSE NULL END)
                    END AS REF14,
                    CASE
                        WHEN uranome = 'URA-DLOCAL-307050-clone' THEN uracampos ->> 'REF11'
                        WHEN uranome = 'URA-DLOCAL-PS-453243' THEN
                            COALESCE(uracampos ->> 'AVALIACAORECOMENDACAO', CASE WHEN POSITION('AVALIACAO RECOMENDACAO (' IN urahistorico) <> 0 THEN SUBSTRING(urahistorico, POSITION('AVALIACAO RECOMENDACAO (' IN urahistorico) + 24, 1) ELSE NULL END)
                    END AS REF11,
                    CASE
                        WHEN uranome = 'URA-DLOCAL-307050-clone' THEN uracampos ->> 'REF12'
                        WHEN uranome = 'URA-DLOCAL-PS-453243' THEN
                            COALESCE(uracampos ->> 'AVALIACAOSOLICITACAORESOLVIDA', CASE WHEN POSITION('AVALIACAO SOLICITACAO RESOLVIDA' IN urahistorico) <> 0 THEN SUBSTRING(urahistorico, POSITION('AVALIACAO SOLICITACAO RESOLVIDA' IN urahistorico) + 33, 1) ELSE NULL END)
                    END AS REF12,
                    clientedesligou, numero, tempototal, tempoespera, tempoatende, todos, atendimento, naoatendimento, ocupado, falhas, entrante, sainte, interna, contareceptivo, contareceptivoatendimento, contareceptivoatendimentoantesns, contareceptivoatendimentoaposns, contareceptivoabandono, contareceptivoabandonoantes10, contareceptivoabandonoantesns, contareceptivoabandonoaposns, contareceptivoforahorario, contaativo, contaativoatendimento, contaativoexternoatendimento, contaativoexternonaoatendimento, contaativointernoatendimento, contaativointernonaoatendimento
                FROM 
                    ligacao_receptivo_atendimento 
                WHERE 
                    custo LIKE 'DLOCAL%%'
            )
            SELECT * FROM tbl_dlocal_telefonia_completa
            WHERE datahora >= '{data_inicio}' 
            AND datahora <= '{data_fim}'
            ORDER BY datahora DESC;
        """
        df = pd.read_sql_query(text(query_sql), cnxn)
        return df

# ==============================
# 2. EXECUCAO E EXPORTACAO
# ==============================
def executar_e_salvar_dlocal():
    print("Iniciando processo de extracao e salvamento chamadas Dlocal...")
   
    try:
        df_novo = carregar_chamadas_dlocal()
        if df_novo.empty:
            print("Nenhum dado novo retornado.")
            return
 
        caminho_parquet = os.path.join(PASTA_DESTINO, "import_chamadas_dlocal.parquet")
 
        if os.path.exists(caminho_parquet):
            print("Carregando historico e mesclando registros...")
            df_historico = pd.read_parquet(caminho_parquet)
           
            # Concatena o novo com o histórico
            df_concatenado = pd.concat([df_historico, df_novo], ignore_index=True)
           
            # --- AJUSTE DE LÓGICA ---
            # Removemos duplicatas apenas se for o MESMO operador no MESMO
            # momento de uma MESMA chamada (prevenção contra erro de carga)
            # Mas permitimos que o mesmo linkedid apareça com OPERADORES diferentes.
            df_final = df_concatenado.drop_duplicates(subset=['linkedid', 'datahora', 'usuario'])
           
            # Ordenação cronológica para facilitar a leitura da auditoria
            df_final = df_final.sort_values(by=['linkedid', 'datahora'])
           
        else:
            print("Primeira carga detectada. Criando arquivo novo.")
            # Ordena mesmo na primeira carga
            df_final = df_novo.sort_values(by=['linkedid', 'datahora'])
 
        # Exportação
        # df_final.to_parquet(caminho_parquet, index=False, compression='snappy')
        
        # Exportação Excel
        caminho_excel = os.path.join(PASTA_DESTINO, "import_chamadas_dlocal.xlsx")
        df_final.to_excel(caminho_excel, index=False)
       
        print(f"Processo finalizado. Total de dados armazenados: {len(df_final)}")
 
    except Exception as e:
        print(f"Erro no processamento: {e}")
 
if __name__ == "__main__":
    executar_e_salvar_dlocal()

