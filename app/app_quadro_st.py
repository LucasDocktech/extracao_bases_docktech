import streamlit as st
import pandas as pd
import os
import datetime
import altair as alt
import plotly.graph_objects as go 
from plotly.subplots import make_subplots
import io
import pytz

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

def run_headcount_dashboard():
    # ITEM 1: CONFIGURAÇÃO DA PÁGINA
    # Configuração centralizada no main_app.py. Mantido aqui como referência.

    # ITEM 2: CSS PARA CARDS (Mantido conforme original)
    st.markdown("""
        <style>
        .main { background-color: #0E1117; }
        div[data-testid="stMetric"] {
            background-color: #1F2937;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #374151;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        div[data-testid="stMetricValue"] > div { font-size: 28px !important; font-weight: 700 !important; }
        hr { border-color: #374151; }
        .custom-metric-card {
            background-color: #1F2937;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #374151;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            color: #FFFFFF;
            min-height: 220px; /* Garante que todos os cards tenham a mesma altura */
        }
        .metric-label { font-size: 14px; color: #9CA3AF; margin-bottom: 5px; }
        .metric-value { font-size: 28px; font-weight: 700; }
        .metric-delta { font-size: 14px; font-weight: 500; margin: 5px 0; }
        .metric-comparison { font-size: 12px; color: #E5E7EB; margin-top: 5px; }
        
        /* CSS NOVO PARA O ITEM 9 - ESTILO KPI MINIMALISTA */
        .kpi-container { margin-bottom: 25px; padding: 10px; }
        .kpi-title { font-size: 14px; color: #9CA3AF; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
        .kpi-value { font-size: 42px; font-weight: 800; margin: 5px 0; }
        .kpi-subtitle { font-size: 13px; color: #E5E7EB; opacity: 0.8; }
        .kpi-badge { 
            display: inline-block; 
            padding: 2px 10px; 
            border-radius: 20px; 
            font-size: 11px; 
            font-weight: 700; 
            margin-top: 8px;
        }
        </style>
        """, unsafe_allow_html=True)

    # ITEM 3: CARREGAMENTO E PROCESSAMENTO
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CAMINHO_BASE = os.path.join(
    BASE_DIR,
    "..",
    "nivel_dois_bases_app",
    "Arquivos_parquet_nv_2",
    "quadro_geral.parquet"
    )
    
    CAMINHO_BASE = os.path.abspath(CAMINHO_BASE)
    
    # CAMINHO_BASE = r'\\192.168.5.15\mis\Pessoal\Lucas\Site_docktech_ligacoes\nivel_dois_bases_app\Arquivos_parquet_nv_2\quadro_geral.parquet'

    @st.cache_data
    def carregar_dados(caminho, mtime):
        if os.path.exists(caminho):
            df = pd.read_parquet(caminho)
            df.columns = [str(col).upper() for col in df.columns] 
            df['DT_ADMISSAO'] = pd.to_datetime(df['DT_ADMISSAO'], dayfirst=True, errors='coerce')
            df['DT_DESLIGAMENTO'] = pd.to_datetime(df['DT_DESLIGAMENTO'], dayfirst=True, errors='coerce')
            hoje = pd.Timestamp(datetime.date.today())
            df['DATA_REF_TEMPO'] = df['DT_DESLIGAMENTO'].fillna(hoje)
            df['DIAS_CASA'] = (df['DATA_REF_TEMPO'] - df['DT_ADMISSAO']).dt.days
            df['MESES_CASA'] = df['DIAS_CASA'] / 30.44
            df['DT_ADMISSAO_ANO'] = df['DT_ADMISSAO'].dt.year
            df['DT_DESLIGAMENTO_ANO'] = df['DT_DESLIGAMENTO'].dt.year
            return df
        return None

    # Pega a data/hora de última modificação do arquivo em disco
    mtime = os.path.getmtime(CAMINHO_BASE) if os.path.exists(CAMINHO_BASE) else 0
    df_raw = carregar_dados(CAMINHO_BASE, mtime)

    if df_raw is not None:
        # ITEM 4: INTERFACE E FILTROS
        col_logo, col_titulo = st.columns([1, 8])
        with col_logo:
            svg_logo = """
            <svg width="120" height="120" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="display: block; margin-top: -10px;">
              <rect width="100%" height="100%" fill="#0a0e14"/>
              <circle cx="50" cy="50" r="45" fill="none" stroke="white" stroke-width="6"/>
              <text x="50" y="52" dominant-baseline="middle" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="26" fill="white" font-weight="bold">dbm</text>
            </svg>
            """
            st.markdown(svg_logo, unsafe_allow_html=True)
            
        with col_titulo:
            st.title("Headcount & Turnover")

        anos_disponiveis = sorted(df_raw['DT_ADMISSAO_ANO'].dropna().unique().astype(int), reverse=True)
        st.write("### People Analytics")
        selected_years = st.pills("Selecione os anos para os gráficos e cards:", anos_disponiveis, default=[anos_disponiveis[0]], selection_mode="multi")

        if not selected_years:
            st.warning("Selecione ao menos um ano para visualizar os dados.")
            st.stop()

        # ITEM 5: LÓGICA DE CÁLCULO DE MÉTRICAS (Mantido)
        def get_stats(years_list):
            df_f = df_raw[(df_raw['DT_ADMISSAO_ANO'].isin(years_list)) | (df_raw['DT_DESLIGAMENTO_ANO'].isin(years_list))]
            total = len(df_f)
            ativos = len(df_f[df_f['DS_SITUACAO'].str.upper().isin(['TRABALHANDO', 'FÉRIAS', 'ATESTADO MÉDICO INTEGRAL'])])
            df_desl = df_f[df_f['DS_SITUACAO'].str.contains('DEMISSÃO', case=False, na=False)].copy()
            saidas = len(df_desl)
            to = (saidas / total * 100) if total > 0 else 0
            evasao = (len(df_desl[df_desl['DIAS_CASA'] <= 90]) / saidas * 100) if saidas > 0 else 0
            media_casa = df_f['MESES_CASA'].mean() if total > 0 else 0
            return [total, ativos, saidas, to, evasao, media_casa]

        stats_atual = get_stats(selected_years)
        offset = len(selected_years)
        past_years = [y - offset for y in selected_years]
        stats_past = get_stats(past_years)
        
        # ITEM 6: EXIBIÇÃO DOS CARDS (Incrementado com pílulas para alinhamento)
        cols = st.columns(6)
        labels = ["Volume Colaboradores", "Efetivo Ativo", "Saídas Totais", "% Índice Turnover", "% Evasão Exp.", "Média Tempo Casa"]
        
        # Cálculo de Inventário Real e Metas para as Pílulas
        ativo_real_hoje = len(df_raw[df_raw['DT_DESLIGAMENTO'].isna()])
        total_historico = len(df_raw)
        
        # Definição dos conteúdos das pílulas para cada card
        conteudos_badges = [
            f"Base: {total_historico}",         # Volume Colaboradores
            f"Ativos: {ativo_real_hoje}",      # Efetivo Ativo
            f"Acumulado",                       # Saídas Totais
            "Meta: ??",                         # Turnover
            "Ref: 90 dias",                    # Evasão
            "Target: ??"                        # Tempo Casa
        ]

        for i in range(6):
            val, old = stats_atual[i], stats_past[i]
            diff = val - old
            
            if i in [3, 4]: display, d_str = f"{val:.1f}%", f"{diff:+.1f}%"
            elif i == 5: display, d_str = f"{val:.1f} meses", f"{diff:+.1f}"
            else: display, d_str = f"{val}", f"{int(diff):+d}"
            
            is_bad = i in [2, 3, 4]
            color = "#EF4444" if (diff > 0 and is_bad) or (diff < 0 and not is_bad) else "#10B981"
            arrow = "↓" if diff < 0 else "↑"
            
            # Badge padronizada e alinhada à esquerda (0px padding-left)
            badge_html = f'<div style="margin-top: 15px; display: flex; justify-content: flex-start; padding-left: 0px;"><div style="border: 1.5px solid #00DDDD; border-radius: 20px; padding: 2px 12px; color: #00DDDD; font-weight: bold; font-size: 11px; background: rgba(75, 68, 202, 0.1);">{conteudos_badges[i]}</div></div>'

            html_card = f'<div class="custom-metric-card"><div class="metric-label">{labels[i]}</div><div class="metric-value">{display}</div><div class="metric-delta" style="color: {color};">{arrow} {d_str}</div><div class="metric-comparison">vs {", ".join(map(str, sorted(past_years)))}</div>{badge_html}</div>'
            
            cols[i].markdown(html_card, unsafe_allow_html=True)

        st.markdown("---")

        # ITEM 7: GRÁFICOS DE TENDÊNCIA (Mantido)
        df_adm = df_raw[df_raw['DT_ADMISSAO_ANO'].isin(selected_years)].copy()
        df_dem = df_raw[df_raw['DT_DESLIGAMENTO_ANO'].isin(selected_years)].copy()

        col_adm, col_dem = st.columns(2)
        with col_adm.container(border=True):
            st.write("### Tendência de Admissões")

        with col_dem.container(border=True):
            st.write("### Tendência de Demissões")

        # ITEM 8: ANÁLISE DE CAUSA RAIZ (PARETO) com Filtro de Origem Alinhado à Direita
        with st.container(border=True):
            col_titulo_p, col_espaco_p, col_filtro_p = st.columns([1.5, 0.5, 1])
            
            with col_titulo_p:
                st.write("### Causa Raiz: Pareto de Desligamentos")
                anos_formatados = ", ".join(map(str, sorted(selected_years)))
                st.markdown(f"<p style='color: #9CA3AF; margin-top: -15px;'>Análise baseada no período de: {anos_formatados}</p>", unsafe_allow_html=True)
            
            with col_filtro_p:
                opcoes_origem = ["Todas"] + sorted(df_raw['ORIGEM_DESLIGAMENTO'].dropna().unique().tolist())
                sel_origem = st.pills("Origem do Desligamento:", opcoes_origem, default="Todas", key="pills_origem")

            df_p = df_raw[df_raw['DT_DESLIGAMENTO_ANO'].isin(selected_years)].copy()
            if sel_origem != "Todas":
                df_p = df_p[df_p['ORIGEM_DESLIGAMENTO'] == sel_origem]
            
            if not df_p.empty and 'DS_RAZAO_DESLIGAMENTO' in df_p.columns:
                pareto_df = df_p['DS_RAZAO_DESLIGAMENTO'].value_counts().reset_index()
                pareto_df.columns = ['Motivo', 'Qtd']
                pareto_df = pareto_df.sort_values(by='Qtd', ascending=False)
                pareto_df['Acumulado_%'] = (pareto_df['Qtd'].cumsum() / pareto_df['Qtd'].sum()) * 100
                
                col_grafico, col_insight = st.columns([2, 1])
                
                with col_grafico:
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    fig.add_trace(go.Bar(x=pareto_df['Motivo'], y=pareto_df['Qtd'], name="Qtd Saídas", marker_color='#EEFF88'), secondary_y=False)
                    fig.add_trace(go.Scatter(x=pareto_df['Motivo'], y=pareto_df['Acumulado_%'], name="% Acumulada", mode="lines+markers", line=dict(color='#00D8D8', width=3)), secondary_y=True)
                    fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), showlegend=False)
                    fig.update_yaxes(title_text="Frequência", secondary_y=False, gridcolor='#374151')
                    fig.update_yaxes(title_text="% Acumulada", secondary_y=True, range=[0, 105], showgrid=False)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col_insight:
                    st.write("#### Insight Inteligente")
                    ofensores_80 = pareto_df[pareto_df['Acumulado_%'] <= 85]['Motivo'].tolist()
                    st.markdown(f"""
                        <div style="background-color: #1F2937; padding: 20px; border-radius: 10px; border-left: 5px solid #052E2B;">
                            <p style="font-size: 14px; color: #E5E7EB;">
                                <b>Análise Estratégica:</b><br><br>
                                Os motivos <span style="color: #60A5FA; font-weight: bold;">{', '.join(ofensores_80)}</span> 
                                representam a maior concentração das saídas para a origem <b>{sel_origem}</b>. 
                                <br><br>
                                Atuar diretamente sobre essas categorias pode reduzir o turnover em até 80%.
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info(f"Sem dados de desligamento para a origem '{sel_origem}' neste período.")


            # --- TABELA DETALHADA (COM LÓGICA DE FILTRO UNIVERSAL) ---
            st.markdown("### Detalhamento Analítico")
            
            # Utiliza o df_raw diretamente (substituindo o df_sup_base que foi removido)
            df_tabela = df_raw.copy()

            # Seleção de colunas incluindo os novos campos solicitados
            colunas_exibir = [
                'TX_SUPERVISOR', 'NO_FUNCIONARIO', 'ATIVO', 'DESLIGADO', 
                'DT_ADMISSAO', 'DT_DESLIGAMENTO', 'DS_OPERACAO',
                'OB_DESLIGAMENTO', 'OB_DESLIGAMENTO2', 'ORIGEM_DESLIGAMENTO',
                'DS_MOTIVO_DESLIGAMENTO', 'DS_RAZAO_DESLIGAMENTO', 
                'SUB_SITUACAO', 'DIAS_CASA_ATE_DESLIGAMENTO'
            ]
            
            # Filtrar apenas colunas que existem no df_raw para evitar erro
            colunas_finais = [c for c in colunas_exibir if c in df_tabela.columns]
            df_tabela_final = df_tabela[colunas_finais].copy()

            if not df_tabela_final.empty:
                # Ordenação se as colunas existirem
                cols_ordem = [c for c in ['TX_SUPERVISOR', 'ATIVO'] if c in df_tabela_final.columns]
                if cols_ordem:
                    df_tabela_final = df_tabela_final.sort_values(by=cols_ordem, ascending=[True, False][:len(cols_ordem)])

                st.dataframe(
                    df_tabela_final,
                    column_config={
                        "TX_SUPERVISOR": "Supervisor",
                        "NO_FUNCIONARIO": "Funcionário",
                        "ATIVO": st.column_config.NumberColumn("Ativo", format="%d 👤"),
                        "DESLIGADO": st.column_config.NumberColumn("Desligado", format="%d ❌"),
                        "DT_ADMISSAO": st.column_config.DateColumn("Admissão", format="DD/MM/YYYY"),
                        "DT_DESLIGAMENTO": st.column_config.DateColumn("Data Deslig.", format="DD/MM/YYYY"),
                        "DS_OPERACAO": "Operação",
                        "DS_MOTIVO_DESLIGAMENTO": "Motivo",
                        "DIAS_CASA_ATE_DESLIGAMENTO": "Dias de Casa",
                        "SUB_SITUACAO": "Situação"
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # --- BOTÃO DE DOWNLOAD ---
                df_xlsx = to_excel(df_tabela_final)
                st.download_button(
                    label="Baixar Tabela em Excel",
                    data=df_xlsx,
                    file_name='detalhamento_analitico.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            else:
                st.info("Não há dados para exibir no detalhamento analítico.")
            
        # --- ITEM 18: RODAPÉ DINÂMICO (AJUSTADO PARA FUSO BRASÍLIA) ---
        try:
            if os.path.exists(CAMINHO_BASE):
                # Define o fuso horário de Brasília
                fuso_br = pytz.timezone('America/Sao_Paulo')
                
                # Pega o timestamp do arquivo
                timestamp = os.path.getmtime(CAMINHO_BASE)
                
                # Converte o timestamp para datetime ciente do fuso horário de Brasília
                dt_utc = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
                data_sincro = dt_utc.astimezone(fuso_br)
                
                data_atualizacao = data_sincro.strftime('%d/%m/%Y %H:%M')
            else:
                data_atualizacao = "Arquivo não encontrado"
        except Exception:
            # Caso falhe, pega a hora atual no fuso de Brasília
            fuso_br = pytz.timezone('America/Sao_Paulo')
            data_atualizacao = datetime.datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M')

        st.markdown("---")
        col_f1, col_f2, col_f3 = st.columns([2, 1, 1])

        with col_f1:
            st.caption(" **Notas Metodológicas**")
            st.markdown(f"<p style='color: #9CA3AF; font-size: 12px;'>• Turnover: Lorem ipsum.<br>• Fonte: {CAMINHO_BASE.split('/')[-1].split('\\')[-1]}</p>", unsafe_allow_html=True)

        with col_f2:
            st.caption(" **Sincronização Parque**")
            st.write(f"**{data_atualizacao}**")
            st.caption("Status: 🟢 Conectado")

        with col_f3:
            st.caption(" **business intelligence / MIS**")
            st.markdown("<p style='color: #E5E7EB; font-size: 13px;'>Analista: <b>Lucas</b></p>", unsafe_allow_html=True)

# Execucao
if __name__ == "__main__":
    run_headcount_dashboard()