import pandas as pd
from sqlalchemy import text
import sys
import os
import warnings
# Silencia o FutureWarning do pandas durante a concatenação
warnings.simplefilter(action='ignore', category=FutureWarning)
# Adicionando caminho para buscar o modulo de conexao
sys.path.append(r'\\192.168.5.15\mis\Funcoes')
import conn
from aux_data_sistema import obter_datas

# Configuração da pasta de destino na rede
# PASTA_DESTINO = r"\\192.168.5.15\mis\Pessoal\Lucas\Site_docktech_ligacoes\arquivos_parquet_chamadas"
# Pasta local para testes
PASTA_DESTINO = r"C:\Users\lucas.pinto\Desktop\extracao_bases_docktech\arquivos_parquet_chamadas"
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
def carregar_chamadas_cassems():
    # Utiliza a engine vinda do modulo conn (atributo ajustado para sua base Cassems)
    engine = login.connDbmOMNI
    
    with engine.connect() as cnxn:
        query_sql = f"""
        WITH dados AS (
            SELECT
                 ROW_NUMBER () OVER (ORDER BY l.datahora, l.id) AS detalhe,
                 l.id AS idligacao,
                 l.tipo AS tipoligacao,
                 f.id AS idfila,
                 f.name AS fila,
                 f.name AS filames,
                 f.name AS filadia,
                 f.name AS filahora,
                 f.name AS fila30min,
                 l.idusuario AS idusuario,
                 usr.matricula AS matricula,
                 usr.nome AS usuario,
                 ld.nomecampanha AS campanha,
                 ld.idcampanha AS idcampanha,
                 ld.nomemailing AS mailing,
                 ld.campos_json,
                 ld.campos AS campos,
                 l.idmailing AS idmailing,
                 t.obs AS observacao,
                 CASE f.tipofila WHEN 1 THEN 'Receptiva' WHEN 2 THEN 'Discador' WHEN 3 THEN 'Mista' ELSE 'Outras' END AS tipofila,
                 CASE l.idstatus
                     WHEN 303 THEN 'Não Atendido' WHEN 300 THEN 'Falha' WHEN 301 THEN 'Restrição de Contato' WHEN 305 THEN 'Ocupado'
                     WHEN 307 THEN 'Desligamento' WHEN 308 THEN 'Congestionamento' WHEN 366 THEN 'Número Inexistente' WHEN 310 THEN 'Fila Cheia'
                     WHEN 311 THEN 'Sem Agentes Disponíveis' WHEN 312 THEN 'Fila Vazia' WHEN 313 THEN 'Tempo Esgotado' WHEN 315 THEN 'Fora Horário - Antes'
                     WHEN 316 THEN 'Fora Horário - Intervalo' WHEN 317 THEN 'Fora Horário - Depois' WHEN 314 THEN 'Desconexão' WHEN 334 THEN 'Limite de Canais'
                     WHEN 335 THEN 'Sem Rota' WHEN 350 THEN 'Secr. Eletrônica' WHEN 351 THEN 'Msg. Operadora' WHEN 358 THEN 'Falha Operadora'
                     WHEN 399 THEN 'Falha ao Disparar' WHEN 200 THEN 'Atendido' 
                 END AS status,
                 CASE l.idstatusfinal
                     WHEN 314 THEN 'Desconexão' WHEN 201 THEN 'Transferido' WHEN 203 THEN 'Anúncio' WHEN 204 THEN 'Caixa Postal' WHEN 305 THEN 'Transbordo' ELSE '-' 
                 END AS statusfinal,
                 lif.datahorafimespera - l.datahora AS tempoespera,
                 CASE WHEN l.tipo = 'fila' THEN lif.datahorafimespera - l.datahora END AS tempoesperafila,
                 l.tempototal AS tempoduracao,
                 l.tempoatendimento,
                 l.datahora,
                 l.datahoraadd,
                 lif.datahorafimespera AS datahorafimespera,
                 l.datahoraatende,
                 l.datahorafim,
                 l.origem,
                 l.destino,
                 l.idcentrocusto,
                 cc.nome AS centrocusto,
                 l.idstatus,
                 l.idstatusfinal,
                 l.tipo,
                 l.uniqueid,
                 l.linkedid,
                 make_interval (secs => f.servicelevel)::time AS nivelservicofila,
                 lif.nivelservico AS nivelservico,
                 lif.atendeunivelservico AS atendeunivelservico,
                 CASE WHEN l.extra IS NOT NULL THEN
                     CASE l.idstatusfinal
                         WHEN 201 THEN
                             CASE WHEN json_typeof (l.extra->'transferencia') = 'object' THEN
                                     l.extra->'transferencia'->>'tipo' || COALESCE (NULLIF (': ' || COALESCE (l.extra->'transferencia'->>'destino', ''), ': '), '')
                                 ELSE (l.extra->>'transferencia')::text || CASE WHEN l.extra->>'destino' IS NULL THEN '' ELSE ': ' || (l.extra->>'destino')::text END
                             END
                         WHEN 305 THEN 'Destino: ' || (l.extra::json->>'destino')::text
                         ELSE '-'
                     END
                     ELSE NULL
                 END AS textoextra,
                 tbc.nome AS tabulacaocampanha,
                 sc.nome AS subtabulacaocampanha,
                 tf.nome AS tabulacao,
                 s.nome AS subtabulacao,
                 array_to_string (ARRAY[f.campotab1 || ': ' || NULLIF (t.campo1, ''), f.campotab2 || ': ' || NULLIF (t.campo2, ''), f.campotab3 || ': ' || NULLIF (t.campo3, ''), f.campotab4 || ': ' || NULLIF (t.campo4, ''), f.campotab5 || ': ' || NULLIF (t.campo5, ''), f.campotab6 || ': ' || NULLIF (t.campo6, '')], ' - ') AS campostabulacao,
                 CASE WHEN t.id IS NULL THEN tbc.nome ELSE tf.nome END AS filatabulacao,
                 CASE WHEN t.id IS NULL THEN sc.nome ELSE s.nome END AS filasubtabulacao,
                 t.datahoratabulacao,
                 DATE_TRUNC ('SECOND', t.tempotabulando) AS tempotabulando,
                 CASE WHEN (ps.id IS NOT NULL OR l.idstatusfinal = 314) THEN
                     CASE WHEN d.quem = '2' AND l.tipo = 'ramal' THEN 'Contato'
                         WHEN d.quem = '1' AND l.tipo = 'ramal' THEN 'Operador'
                         WHEN d.quem = '2' AND l.tipo IN ('fila', 'atendimento fila') THEN 'Operador'
                         WHEN d.quem = '1' AND l.tipo IN ('fila', 'atendimento fila') THEN 'Contato'
                         WHEN d.quem = '3' THEN 'Supervisor'
                         WHEN d.quem = '4' THEN 'Sistema'
                         WHEN d.quem IS NULL AND ps.id IS NOT NULL THEN 'Sistema'
                     END
                 END AS desligou,
                 CASE WHEN (tps.nome IS NULL OR l.idstatus = 303) THEN '-' ELSE tps.nome END AS pesquisa,
                 tps.id AS pesquisafila,
                 ps.id AS idpesquisa,
                 CASE WHEN ps.id IS NULL THEN CASE WHEN l.idstatusfinal = 314 AND ((d.quem = 1 AND l.tipo IN ('fila','atendimento fila')) OR (d.quem = 2 AND l.tipo = 'ramal')) THEN 'Cliente Desligou' ELSE 'Não Transferido' END ELSE 'Transferido' END AS pesquisatransferida,
                 tps.numperguntas AS numperguntas,
                 NULLIF (tps.txtpergunta1, '') AS pergunta1,
                 NULLIF (tps.txtpergunta2, '') AS pergunta2,
                 NULLIF (tps.txtpergunta3, '') AS pergunta3,
                 NULLIF (tps.txtpergunta4, '') AS pergunta4,
                 NULLIF (tps.txtpergunta5, '') AS pergunta5,
                 (NULLIF (ps.nota, '-1')::int + CASE WHEN tps.respemzero1 = 1 THEN 1 ELSE 0 END)::text AS nota1,
                 (NULLIF (ps.nota2, '-1')::int + CASE WHEN tps.respemzero2 = 1 THEN 1 ELSE 0 END)::text AS nota2,
                 (NULLIF (ps.nota3, '-1')::int + CASE WHEN tps.respemzero3 = 1 THEN 1 ELSE 0 END)::text AS nota3,
                 (NULLIF (ps.nota4, '-1')::int + CASE WHEN tps.respemzero4 = 1 THEN 1 ELSE 0 END)::text AS nota4,
                 (NULLIF (ps.nota5, '-1')::int + CASE WHEN tps.respemzero5 = 1 THEN 1 ELSE 0 END)::text AS nota5,
                 CASE WHEN ps.nota = '-1' THEN 'Não opinou' ELSE split_part (tps.txtrespostas1, ':', ps.nota::int + CASE WHEN tps.respiniciaem0 = 1 THEN 1 ELSE 0 END) END AS resposta1,
                 CASE WHEN ps.nota2 = '-1' AND NULLIF (tps.txtpergunta2, '') IS NOT NULL THEN 'Não opinou' ELSE split_part (NULLIF (tps.txtrespostas2, ''), ':', ps.nota2::int + CASE WHEN tps.respiniciaem0 = 1 THEN 1 ELSE 0 END) END AS resposta2,
                 CASE WHEN ps.nota3 = '-1' AND NULLIF (tps.txtpergunta3, '') IS NOT NULL THEN 'Não opinou' ELSE split_part (NULLIF (tps.txtrespostas3, ''), ':', ps.nota3::int + CASE WHEN tps.respiniciaem0 = 1 THEN 1 ELSE 0 END) END AS resposta3,
                 CASE WHEN ps.nota4 = '-1' AND NULLIF (tps.txtpergunta4, '') IS NOT NULL THEN 'Não opinou' ELSE split_part (NULLIF (tps.txtrespostas4, ''), ':', ps.nota4::int + CASE WHEN tps.respiniciaem0 = 1 THEN 1 ELSE 0 END) END AS resposta4,
                 CASE WHEN ps.nota5 = '-1' AND NULLIF (tps.txtpergunta5, '') IS NOT NULL THEN 'Não opinou' ELSE split_part (NULLIF (tps.txtrespostas5, ''), ':', ps.nota5::int + CASE WHEN tps.respiniciaem0 = 1 THEN 1 ELSE 0 END) END AS resposta5,
                 COALESCE (c.nome, '-') AS nomecontato,
                 l.idligextprincipal AS externo_idligacao,
                 tr.nome AS externo_tronco,
                 lexterna.datahora AS externo_datahora,
                 lexterna.datahoraatende AS externo_datahoraatende,
                 lexterna.datahorafim AS externo_datahorafim,
                 lexterna.tempototal AS externo_tempototal,
                 lexterna.tempoatendimento AS externo_tempoatendimento,
                 lassistentevoz.id AS assistente_idligacao,
                 u.nome AS assistente_nome,
                 lassistentevoz.datahora AS assistente_datahora,
                 lassistentevoz.datahoraatende AS assistente_datahoraatende,
                 lassistentevoz.datahorafim AS assistente_datahorafim,
                 lassistentevoz.tempototal AS assistente_tempototal,
                 lassistentevoz.tempoatendimento AS assistente_tempoatendimento,
                 lt.tempotarifado AS externo_tempotarifado,
                 make_interval (secs => EXTRACT (EPOCH FROM lif.tempototalhold))::time AS hold_tempo_total,
                 make_interval (secs => EXTRACT (EPOCH FROM lif.tempototalmudo))::time AS mudo_tempo_total,
                 lt.valor AS externo_valor
            FROM ligacao l
                 JOIN custo__atz cc ON cc.id = l.idcentrocusto
                 JOIN ligacaointerna li ON li.idligacao = l.id AND l.tipo IN ('fila', 'atendimento fila', 'ramal')
                 JOIN ligacaointernafila lif ON lif.idligacaointerna = li.id
                 JOIN fila f ON f.id = l.idfila AND f.tipofila IN ('1', '2', '3')
                 LEFT JOIN ligacaodiscador ld ON ld.idligacao = l.id
                 LEFT JOIN ligacao ligacaofila on ligacaofila.linkedid = l.linkedid AND CASE WHEN l.datahoraatende IS NULL THEN ligacaofila.idstatusfinal = l.idstatusfinal AND ligacaofila.datahoraatende IS NULL ELSE ligacaofila.datahoraatende = l.datahoraatende END AND l.tipo = 'atendimento fila' AND ligacaofila.tipo = 'fila' AND ligacaofila.id <> l.id
                 LEFT JOIN ligacao lexterna ON lexterna.id = l.idligextprincipal
                 LEFT JOIN ligacao lassistentevoz ON lassistentevoz.id = l.idliganterior AND lassistentevoz.tipo = 'assistente de voz'
                 LEFT JOIN usuario usr ON usr.id = l.idusuario
                 LEFT JOIN ura u ON u.id = lassistentevoz.idassistentevoz
                 LEFT JOIN ligacaotarifacao lt ON lt.idligacao = l.idligextprincipal
                 LEFT JOIN ligacaoexterna le ON le.idligacao = l.idligextprincipal
                 LEFT JOIN tronco tr ON tr.id = le.idtronco
                 LEFT JOIN cc_tabulacao t ON l.id IN (t.idligacaoagente, t.idligacaofila)
                 LEFT JOIN tabulacaofila tf ON tf.id = t.idtipo
                 LEFT JOIN tabulacaocampanha tbc ON tbc.id = t.idtipocampanha
                 LEFT JOIN subtabulacao s ON s.id = t.idsubtipo
                 LEFT JOIN subtabulacaocampanha sc ON sc.id = t.idsubtipocampanha
                 LEFT JOIN templateps tps ON tps.id = lif.idtemplateps
                 LEFT JOIN pesquisasatisfacao ps ON l.idstatusfinal = 201 AND l.id IN (ps.idligacaoagente, ps.idligacaofila) AND lif.idtemplateps IS NOT NULL AND lif.pesquisasatisfacao = true
                 LEFT JOIN desconexao d ON CASE l.tipo WHEN 'atendimento fila' THEN ligacaofila.uniqueid ELSE l.uniqueid END = d.uniqueid
                 LEFT JOIN contatocanal conc ON conc.id = l.idcontatocanal
                 LEFT JOIN contato c ON c.id = conc.idcontato
            WHERE cc.id IS NOT NULL
            AND l.datahora >= '{data_inicio}'
            AND l.datahora <= '{data_fim}'
        ), 
        resultado AS (
            SELECT
                 ROW_NUMBER () OVER (ORDER BY MAX(fila) ASC) AS linha,
                 MAX (idligacao) AS idligacao,
                 COALESCE (SUM (tempoduracao), '00:00'::interval) AS tempoduracao,
                 COALESCE (SUM (tempoatendimento), '00:00'::interval) AS tempoatendimento,
                 COALESCE (SUM (tempoespera), '00:00:00'::interval) AS tempoespera,
                 COALESCE (SUM (CASE WHEN tipoligacao IN ('fila', 'ramal') THEN tempoduracao ELSE NULL END), '00:00'::interval) AS tempoduracaofila,
                 COALESCE (AVG (CASE WHEN tipoligacao IN ('fila', 'ramal') THEN tempoduracao ELSE NULL END), '00:00'::interval) AS tempoduracaofila_avg,
                 COALESCE (SUM (CASE WHEN tipoligacao IN ('fila', 'ramal') THEN tempoatendimento ELSE NULL END), '00:00'::interval) AS tempoatendimentofila,
                 COALESCE (AVG (CASE WHEN tipoligacao IN ('fila', 'ramal') AND idstatus = 200 THEN tempoatendimento ELSE NULL END), '00:00'::interval) AS tempoatendimentofila_avg,
                 COALESCE (SUM (CASE WHEN tipoligacao = 'fila' THEN tempoesperafila ELSE NULL END), '00:00'::interval) AS tempoesperafila,
                 COALESCE (AVG (CASE WHEN tipoligacao = 'fila' THEN tempoesperafila ELSE NULL END), '00:00'::interval) AS tempoesperafila_avg,
                 COALESCE (SUM (CASE WHEN tipoligacao = 'fila' AND idstatus = 200 THEN tempoesperafila ELSE NULL END), '00:00'::interval) AS tempoesperafila_atd,
                 COALESCE (AVG (CASE WHEN tipoligacao = 'fila' AND idstatus = 200 THEN tempoesperafila ELSE NULL END), '00:00'::interval) AS tempoesperafila_atd_avg,
                 COALESCE (SUM (CASE WHEN tipoligacao = 'fila' AND idstatus = 314 THEN tempoesperafila ELSE NULL END), '00:00'::interval) AS tempoesperafila_desc,
                 COALESCE (AVG (CASE WHEN tipoligacao = 'fila' AND idstatus = 314 THEN tempoesperafila ELSE NULL END), '00:00'::interval) AS tempoesperafila_desc_avg,
                 COALESCE (SUM (CASE WHEN tipoligacao = 'ramal' THEN tempoespera ELSE NULL END), '00:00'::interval) AS tempotocaativa,
                 COALESCE (AVG (CASE WHEN tipoligacao = 'ramal' THEN tempoespera ELSE NULL END), '00:00'::interval) AS tempotocaativa_avg,
                 COALESCE (SUM (hold_tempo_total), '00:00'::interval) AS hold_tempo,
                 to_char (COALESCE (AVG (hold_tempo_total), '00:00'::interval), 'HH24:MI:SS') AS hold_tempo_avg,
                 COALESCE (SUM (mudo_tempo_total), '00:00'::interval) AS mudo_tempo,
                 to_char (COALESCE (AVG (mudo_tempo_total), '00:00'::interval), 'HH24:MI:SS') AS mudo_tempo_avg,
                 to_char (MAX (datahora), 'DD/MM/YYYY HH24:MI:SS') AS datahora,
                 to_char (MAX (datahoraadd), 'DD/MM/YYYY HH24:MI:SS') AS datahoraadd,
                 to_char (MAX (datahoraatende), 'DD/MM/YYYY HH24:MI:SS') AS datahoraatende,
                 to_char (MAX (datahorafim), 'DD/MM/YYYY HH24:MI:SS') AS datahorafim,
                 COALESCE (to_char (MAX (datahoratabulacao), 'DD/MM/YYYY HH24:MI:SS'), '-') AS datahoratabulacao,
                 COALESCE (MAX (tempotabulando)::TEXT, '-') AS tempotabulando,
                 MAX (origem) AS origem,
                 MAX (destino) AS destino,
                 MAX (idfila) AS idfila,
                 MAX (fila) AS fila,
                 MAX (filames) AS filames,
                 MAX (filadia) AS filadia,
                 MAX (filahora) AS filahora,
                 MAX (fila30min) AS fila30min,
                 MAX (idusuario) AS idusuario,
                 MAX (matricula) AS matricula,
                 COALESCE (MAX (usuario), '-') AS usuario,
                 COALESCE (MAX (campanha), '-') AS campanha,
                 COALESCE (MAX (idcampanha::TEXT), '-') AS idcampanha,
                 COALESCE (MAX (mailing), '-') AS mailing,
                 COALESCE (MAX (idmailing::TEXT), '-') AS idmailing,
                 MAX (campos_json::text)::jsonb AS campos_json,
                 COALESCE (MAX (campos), '-') AS campos,
                 MAX (tipofila) AS tipofila,
                 COALESCE (MAX (nivelservico), MAX (nivelservicofila)) AS nivelservico,
                 MAX (idstatus) AS idstatus,
                 MAX (centrocusto) AS centrocusto,
                 MAX (status) AS status,
                 MAX (idstatusfinal) AS idstatusfinal,
                 MAX (statusfinal) AS statusfinal,
                 CASE MAX (tipo) WHEN 'fila' THEN 'Fila' WHEN 'ramal' THEN 'Ativa' ELSE 'Atendimento Agente' END AS tipo,
                 MAX (uniqueid) AS uniqueid,
                 MAX (linkedid) AS linkedid,
                 COALESCE (MAX (textoextra), '-') AS extra,
                 COALESCE (SUM (CASE tipoligacao WHEN 'fila' THEN CASE WHEN idstatus = 200 AND datahoraatende IS NOT NULL THEN 1 ELSE 0 END ELSE 0 END), 0) AS quantidadeatendido,
                 COALESCE (MAX (tabulacao), '-') AS tabulacao,
                 MAX (filatabulacao) AS filatabulacao,
                 COALESCE (MAX (subtabulacao), '-') AS subtabulacao,
                 MAX (filasubtabulacao) AS filasubtabulacao,
                 COALESCE (MAX (tabulacaocampanha), '-') AS tabulacaocampanha,
                 COALESCE (MAX (subtabulacaocampanha), '-') AS subtabulacaocampanha,
                 NULLIF (MAX (campostabulacao), '') AS campostabulacao,
                 COALESCE (NULLIF (MAX (observacao), ''), '-') AS observacao,
                 COALESCE (MAX (desligou), '-') AS desligou,
                 SUM (CASE WHEN tipoligacao = 'fila' THEN 1 WHEN tipoligacao = 'ramal' THEN 1 ELSE 0 END) AS total,
                 COALESCE (MAX (pesquisa), '-') AS pesquisa,
                 MAX (pesquisafila) AS pesquisafila,
                 MAX (idpesquisa) AS idpesquisa,
                 COALESCE (MAX (pesquisatransferida), '-') AS pesquisatransferida,
                 MAX (numperguntas) AS numperguntas,
                 COALESCE (MAX (pergunta1), '-') AS pergunta1,
                 COALESCE (MAX (pergunta2), '-') AS pergunta2,
                 COALESCE (MAX (pergunta3), '-') AS pergunta3,
                 COALESCE (MAX (pergunta4), '-') AS pergunta4,
                 COALESCE (MAX (pergunta5), '-') AS pergunta5,
                 COALESCE (MAX (nota1), '-') AS nota1,
                 MAX (nota2) AS nota2,
                 MAX (nota3) AS nota3,
                 MAX (nota4) AS nota4,
                 MAX (nota5) AS nota5,
                 COALESCE (MAX (resposta1), '-') AS resposta1,
                 COALESCE (MAX (resposta2), '-') AS resposta2,
                 COALESCE (MAX (resposta3), '-') AS resposta3,
                 COALESCE (MAX (resposta4), '-') AS resposta4,
                 COALESCE (MAX (resposta5), '-') AS resposta5,
                 MAX (nomecontato) AS nomecontato,
                 COALESCE (MAX (externo_idligacao)::text, '-') AS externo_idligacao,
                 COALESCE (MAX (externo_tronco), '-') AS externo_tronco,
                 to_char (MAX (externo_datahora), 'DD/MM/YYYY HH24:MI:SS') AS externo_datahora,
                 to_char (MAX (externo_datahoraatende), 'DD/MM/YYYY HH24:MI:SS') AS externo_datahoraatende,
                 to_char (MAX (externo_datahorafim), 'DD/MM/YYYY HH24:MI:SS') AS externo_datahorafim,
                 COALESCE (MAX (externo_tempototal), '00:00'::time) AS externo_tempototal,
                 COALESCE (MAX (externo_tempoatendimento), '00:00'::time) AS externo_tempoatendimento,
                 COALESCE (MAX (externo_tempotarifado), '00:00'::time) AS externo_tempotarifado,
                 COALESCE (MAX (externo_valor), 0) AS externo_valor,
                 COALESCE (MAX (assistente_idligacao)::text, '-') AS assistente_idligacao,
                 COALESCE (MAX (assistente_nome), '-') AS assistente_nome,
                 to_char (MAX (assistente_datahora), 'DD/MM/YYYY HH24:MI:SS') AS assistente_datahora,
                 to_char (MAX (assistente_datahoraatende), 'DD/MM/YYYY HH24:MI:SS') AS assistente_datahoraatende,
                 to_char (MAX (assistente_datahorafim), 'DD/MM/YYYY HH24:MI:SS') AS assistente_datahorafim,
                 COALESCE (MAX (assistente_tempototal), '00:00'::time) AS assistente_tempototal,
                 COALESCE (MAX (assistente_tempoatendimento), '00:00'::time) AS assistente_tempoatendimento
            FROM dados
            GROUP BY detalhe
        )
        SELECT
            datahora,
            COALESCE (datahoraatende::text, '-') AS datahoraatende,
            datahorafim,
            origem,
            destino,
            idusuario,
            matricula,
            usuario,
            nomecontato,
            centrocusto,
            status,
            idstatus,
            statusfinal,
            extra,
            fila,
            tipofila,
            tipo,
            idcampanha,
            campanha,
            idmailing,
            mailing,
            campos,
            to_char (tempoduracao, 'HH24:MI:SS') AS tempoduracao,
            to_char (tempoatendimento, 'HH24:MI:SS') AS tempoatendimento,
            to_char (tempoespera, 'HH24:MI:SS') AS tempoespera,
            to_char (hold_tempo, 'HH24:MI:SS') AS hold_tempo_total,
            to_char (mudo_tempo, 'HH24:MI:SS') AS mudo_tempo_total,
            nivelservico::TEXT AS nivelservico,
            datahoratabulacao,
            tempotabulando,
            tabulacao,
            subtabulacao,
            tabulacaocampanha,
            subtabulacaocampanha,
            campostabulacao,
            observacao,
            uniqueid,
            linkedid,
            idligacao,
            desligou,
            pesquisa,
            CASE WHEN (pesquisafila IS NULL OR status = 'Não Atendido') THEN '-' ELSE pesquisatransferida END AS pesquisatransferida,
            CASE WHEN (pesquisafila IS NULL OR status = 'Não Atendido') THEN '-' ELSE pergunta1 END AS pergunta1,
            CASE WHEN (pesquisafila IS NULL OR status = 'Não Atendido') THEN '-' ELSE resposta1 END AS resposta1,
            COALESCE (nota1, '-') AS nota1,
            CASE WHEN (pesquisafila IS NULL OR status = 'Não Atendido') THEN '-' ELSE pergunta2 END AS pergunta2,
            CASE WHEN (pesquisafila IS NULL OR status = 'Não Atendido') THEN '-' ELSE resposta2 END AS resposta2,
            COALESCE (nota2, '-') AS nota2,
            CASE WHEN (pesquisafila IS NULL OR status = 'Não Atendido') THEN '-' ELSE pergunta3 END AS pergunta3,
            CASE WHEN (pesquisafila IS NULL OR status = 'Não Atendido') THEN '-' ELSE resposta3 END AS resposta3,
            COALESCE (nota3, '-') AS nota3,
            CASE WHEN (pesquisafila IS NULL OR status = 'Não Atendido') THEN '-' ELSE pergunta4 END AS pergunta4,
            CASE WHEN (pesquisafila IS NULL OR status = 'Não Atendido') THEN '-' ELSE resposta4 END AS resposta4,
            COALESCE (nota4, '-') AS nota4,
            CASE WHEN (pesquisafila IS NULL OR status = 'Não Atendido') THEN '-' ELSE pergunta5 END AS pergunta5,
            CASE WHEN (pesquisafila IS NULL OR status = 'Não Atendido') THEN '-' ELSE resposta5 END AS resposta5,
            COALESCE (nota5, '-') AS nota5,
            externo_tronco,
            externo_idligacao,
            COALESCE (externo_datahora, '-') AS externo_datahora,
            COALESCE (externo_datahoraatende, '-') AS externo_datahoraatende,
            COALESCE (externo_datahorafim, '-') AS externo_datahorafim,
            to_char (externo_tempototal, 'HH24:MI:SS') AS externo_tempototal,
            to_char (externo_tempoatendimento, 'HH24:MI:SS') AS externo_tempoatendimento,
            to_char (externo_tempotarifado, 'HH24:MI:SS') AS externo_tempotarifado,
            COALESCE (TO_CHAR (externo_valor, 'L999G990D0099'), '-') AS externo_valor,
            campos_json,
            assistente_idligacao,
            assistente_nome,
            assistente_datahora,
            assistente_datahoraatende,
            assistente_datahorafim,
            to_char (assistente_tempototal, 'HH24:MI:SS') AS assistente_tempototal,
            to_char (assistente_tempoatendimento, 'HH24:MI:SS') AS assistente_tempoatendimento
        FROM resultado
        WHERE
            centrocusto LIKE '%%Cassems%%'
            AND tipo IN ('Fila','Ativa');
        """
        df = pd.read_sql_query(text(query_sql), cnxn)
        return df

def executar_e_salvar_cassems():
    print("Iniciando processo de extracao e salvamento Chamadas Cassems...")
    
    try:
        df_novo = carregar_chamadas_cassems()
        if df_novo.empty:
            print("Nenhum dado novo retornado.")
            return

        caminho_parquet = os.path.join(PASTA_DESTINO, "import_chamadas_cassems.parquet")

        if os.path.exists(caminho_parquet):
            print("Carregando historico e mesclando registros...")
            df_historico = pd.read_parquet(caminho_parquet)
            
            # Concatena o novo com o histórico
            df_concatenado = pd.concat([df_historico, df_novo], ignore_index=True)
            
            # Removemos duplicatas apenas se for o MESMO operador no MESMO momento de uma MESMA chamada
            df_final = df_concatenado.drop_duplicates(subset=['linkedid', 'datahora', 'usuario'])
            
            # Ordenação cronológica para facilitar a leitura da auditoria
            df_final = df_final.sort_values(by=['linkedid', 'datahora'])
            
        else:
            print("Primeira carga detectada. Criando arquivo novo.")
            # Ordena mesmo na primeira carga
            df_final = df_novo.sort_values(by=['linkedid', 'datahora'])

        # Exportação
        df_final.to_parquet(caminho_parquet, index=False, compression='snappy')
        
        print(f"Processo finalizado. Total de dados armazenados: {len(df_final)}")

    except Exception as e:
        print(f"Erro no processamento: {e}")

if __name__ == "__main__":
    executar_e_salvar_cassems()