import pandas as pd
from sqlalchemy import text
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
def carregar_chamadas_gerais():
    engine = login.connProMIS
    with engine.connect() as cnxn:
        query_sql = f"""
            SELECT
                tbl.uniqueid AS t_uniqueid,
                tbl.Chamada AS t_Chamada,
                tbl.Data AS t_Data,
                tbl.Hora AS t_Hora,
                tbl.Pais AS t_Pais,
                tbl.DDD AS t_DDD,
                tbl.Numero AS t_Numero,
                tbl.Fila AS t_Fila,
                tbl."Tempo na ura" AS t_Tempo_na_ura,
                tbl."Tempo de espera" AS t_Tempo_de_espera,
                tbl."Tempo falado" AS t_Tempo_falado,
                tbl."Tempo Satisfacao" AS t_Tempo_Satisfacao,
                tbl."Tempo Total" AS t_Tempo_Total,
                tbl.Desconexão AS t_Desconexao,
                tbl."Telefone Entrada" AS t_Telefone_Entrada,
                tbl."Id ligação" AS t_Id_ligacao,
                tbl.Submissor AS t_Submissor,
                tbl.Final_URA AS t_Final_URA,
                tbl.Nota AS t_Nota,
                tbl.RespPesquisa AS t_RespPesquisa,
                tbl.Tabulacao AS t_Tabulacao,
                tbl.SubTabulacao AS t_SubTabulacao,
                tbl."Tipo Contato" AS t_Tipo_Contato,
                tbl.Operador AS t_Operador,
                tbl.FilaNexus AS t_FilaNexus,
                tbl.DataHora AS t_DataHora,
                tbl.RespPesquisa2 AS t_RespPesquisa2,
                tbl.Nota2 AS t_Nota2,
                tbl.linkedidSemPonto AS t_linkedidSemPonto,
                tbl.status_ligacao AS t_status_ligacao,
                tbl.desconexao_sistema AS t_desconexao_sistema,
                tbl.cpf_cnpj AS t_cpf_cnpj,
                dim.Chamada AS d_Chamada,
                dim.Numero AS d_Numero,
                dim.Fila AS d_Fila,
                dim.Desconexão AS d_Desconexao,
                dim.Telefone_Entrada AS d_Telefone_Entrada,
                dim.linkedid AS d_linkedid,
                dim.Submissor AS d_Submissor,
                dim.RespPesquisa AS d_RespPesquisa,
                dim.Tabulacao AS d_Tabulacao,
                dim.SubTabulacao AS d_SubTabulacao,
                dim.Tipo_Contato AS d_Tipo_Contato,
                dim.Operador AS d_Operador,
                dim.tx_subemissor_jira,
                dim.tx_fila,
                dim.tx_prioridade,
                dim.tx_categoria,
                dim.tx_motivo,
                dim.tx_submotivo,
                dim.OP,
                dim.visao,
                dim.TotalChamadas,
                dim.RetidaEmUra,
                dim.Atendidas,
                dim.Abandonadas,
                dim.Recebidas,
                dim.Atendidos10Seg,
                dim.Atendidos15Seg,
                dim.ShortCall,
                dim.FCR,
                dim.RECHAMADA,
                dim.tempoEsperaSeg,
                dim.tempoFaladoSeg,
                dim.tempoURASeg,
                dim.encaminhado_Csat,
                dim.Resp_CSAT,
                dim.Csat0,
                dim.Csat1,
                dim.Csat2,
                dim.Csat3,
                dim.Csat4,
                dim.Csat5,
                dim.CsatDetrator,
                dim.CsatNeutro,
                dim.CsatPromotor,
                dim.EncaminhadoCSATDetrator,
                dim.Detrator_informacaoNaoFoiClara,
                dim.Detrator_NaoForamEsclarecidas,
                dim.Detrator_NaoFoiEducado,
                dim.CALLBACK,
                dim.Entrou_em_URA,
                dim.PrimeiraTentativaCPF_URA,
                dim.ClienteNaoConsta_URA,
                dim.Perda_URA,
                dim.Roubo_URA,
                dim.Saldo_extrato_URA,
                dim.Desbloquear_cartao_URA,
                dim.Senha_incorreta_URA,
                dim.Perda_Roubo_URA,
                dim.Primeira_Mensagem_URA,
                dim.HoraTravada,
                dim.DataHora AS d_DataHora,
                dim.tx_status,
                dim.tx_item,
                dim.tx_jira_aberto,
                dim.tx_jira_fechado,
                dim.tx_jira_pendente,
                dim.dt_cadastro_jira,
                dim.dt_data_resolucao,
                dim.dias_atraso_BKO,
                dim.ToCALLBACK,
                dim.ToCALLBACKQueda,
                dim.tx_transacao_cartao,
                dim.TransferenciaOgea_URA,
                dim.TransferenciaAssai_URA,
                dim.desconexao_tronco,
                dim.cpf_cnpj AS d_cpf_cnpj,
                dim.tx_cpf_cnpj_jira,
                dim.fora_de_horario
            FROM
                tbl_000_Telefonia_Nexus_Docktech tbl WITH(NOLOCK)
                LEFT JOIN dim_pbi_000_Docktech_telefonia dim WITH(NOLOCK) ON tbl.uniqueid = dim.linkedid
            WHERE
                dim.OP IN ('N2','SAC')
                AND CAST(tbl.DataHora AS DATE) BETWEEN '{data_inicio}' AND '{data_fim}'
        """
        df = pd.read_sql_query(text(query_sql), cnxn)
        return df

# ==============================
# 2. EXECUCAO E EXPORTACAO
# ==============================
def executar_e_salvar_chamadas_gerais():
    print("Iniciando processo de extracao e salvamento Chamadas Gerais...")
   
    try:
        df_novo = carregar_chamadas_gerais()
        if df_novo.empty:
            print("Nenhum dado novo retornado.")
            return
        # Chamadas gerais incluem todas chamadas de SAC
        caminho_parquet = os.path.join(PASTA_DESTINO, "import_chamadas_gerais.parquet")
 
        if os.path.exists(caminho_parquet):
            print("Carregando historico e mesclando registros...")
            df_historico = pd.read_parquet(caminho_parquet)
           
            # Concatena o novo com o histórico
            df_concatenado = pd.concat([df_historico, df_novo], ignore_index=True)
           
            # --- AJUSTE DE LÓGICA ---
            # Removemos duplicatas apenas se for o MESMO operador no MESMO
            # momento de uma MESMA chamada (prevenção contra erro de carga)
            # Mas permitimos que o mesmo linkedid apareça com OPERADORES diferentes.
            df_final = df_concatenado.drop_duplicates(subset=['t_Id_ligacao', 't_Data', 't_Operador'])
           
            # Ordenação cronológica para facilitar a leitura da auditoria
            df_final = df_final.sort_values(by=['t_Id_ligacao', 't_Data'])
           
        else:
            print("Primeira carga detectada. Criando arquivo novo.")
            # Ordena mesmo na primeira carga
            df_final = df_novo.sort_values(by=['t_Id_ligacao', 't_Data'])
 
        # Exportação
        df_final.to_parquet(caminho_parquet, index=False, compression='snappy')
       
        print(f"Processo finalizado. Total de dados armazenados: {len(df_final)}")
 
    except Exception as e:
        print(f"Erro no processamento: {e}")
 
if __name__ == "__main__":
    executar_e_salvar_chamadas_gerais()
