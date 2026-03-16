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

    @st.cache_data(ttl=3600)
    def carregar_dados(caminho):
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

    df_raw = carregar_dados(CAMINHO_BASE)

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
            chart_adm = alt.Chart(df_adm).mark_line(interpolate='monotone', size=3).encode(
                x=alt.X('DT_ADMISSAO:T', timeUnit='month', title='Mês'),
                y=alt.Y('count():Q', title='Qtd. Admissões'),
                color=alt.Color('DT_ADMISSAO_ANO:N', title='Ano'),
                tooltip=['DT_ADMISSAO_ANO:N', 'month(DT_ADMISSAO):O', 'count()']
            ).properties(height=350)
            st.altair_chart(chart_adm, use_container_width=True)

        with col_dem.container(border=True):
            st.write("### Tendência de Demissões")
            chart_dem = alt.Chart(df_dem).mark_line(interpolate='monotone', size=3, opacity=0.8).encode(
                x=alt.X('DT_DESLIGAMENTO:T', timeUnit='month', title='Mês'),
                y=alt.Y('count():Q', title='Qtd. Demissões'),
                color=alt.Color('DT_DESLIGAMENTO_ANO:N', title='Ano'),
                tooltip=['DT_DESLIGAMENTO_ANO:N', 'month(DT_DESLIGAMENTO):O', 'count()']
            ).properties(height=350)
            st.altair_chart(chart_dem, use_container_width=True)

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

        # ITEM 9: DETALHAMENTO MINIMALISTA POR UNIDADE (Mantido)
        st.write("### Detalhamento por Operação")
        anos_formatados_detalhe = ", ".join(map(str, sorted(selected_years)))
        st.markdown(f"<p style='color: #9CA3AF; margin-top: -15px;'>Análise baseada no período de: {anos_formatados_detalhe}</p>", unsafe_allow_html=True)
        
        df_op_item9 = df_raw[df_raw['DT_DESLIGAMENTO_ANO'].isin(selected_years)].copy()
        
        if not df_op_item9.empty:
            op_data = df_op_item9.groupby('DS_OPERACAO').agg(Qtd=('CD_FUNCIONARIO', 'count'), Tenure=('MESES_CASA', 'mean')).reset_index().sort_values(by='Qtd', ascending=False)
            media_saidas = op_data['Qtd'].mean()
            cols_op = st.columns(4)
            for idx, row in op_data.iterrows():
                col_idx = idx % 4
                color_saida = "#EF4444" if row['Qtd'] > media_saidas else "#10B981"
                status_text = "Acima da média" if row['Qtd'] > media_saidas else "Sob controle"
                badge_bg = "rgba(239, 68, 68, 0.2)" if row['Qtd'] > media_saidas else "rgba(16, 185, 129, 0.2)"
                total_meses = row['Tenure']
                anos = int(total_meses // 12)
                meses_restantes = int(total_meses % 12)
                tempo_str = f"{anos} anos e {meses_restantes} meses" if anos > 0 else f"{meses_restantes} meses"
                
                html_kpi = f"""
                <div class="kpi-container">
                    <div class="kpi-title">{row['DS_OPERACAO']}</div>
                    <div class="kpi-value" style="color: {color_saida};">{int(row['Qtd'])}</div>
                    <div class="kpi-subtitle">Total de Saídas no Período</div>
                    <div class="kpi-subtitle" style="margin-top:10px;"><b>{tempo_str}</b> (Permanência média)</div>
                    <div class="kpi-badge" style="background-color: {badge_bg}; color: {color_saida};">{status_text}</div>
                </div>
                """
                cols_op[col_idx].markdown(html_kpi, unsafe_allow_html=True)
        else:
            st.info("Não há dados operacionais no período selecionado.")

        # ITEM 10: ANÁLISE COMPLEMENTAR (Mantida conforme original)
        st.markdown("---")
        with st.container(border=True):
            st.write("### Análise Complementar: Faixa Etária e Tendência")
            st.info("💡 **Nota:** Valores identificados como 'null' indicam que o motivo não foi preenchido no Directive.")
            lista_ops_comp = ["Todas"] + sorted(df_raw['DS_OPERACAO'].unique().tolist())
            sel_op = st.pills("Unidades:", lista_ops_comp, default="Todas", key="pills_unidades_comp")
            df_filtered = df_raw[df_raw['DT_DESLIGAMENTO_ANO'].isin(selected_years)].copy()
            if sel_op != "Todas":
                df_filtered = df_filtered[df_filtered['DS_OPERACAO'] == sel_op]

            col_g1, col_g2 = st.columns([1.2, 0.8])
            with col_g1:
                st.write("#### Motivos por Faixa Etária")
                chart_etaria = alt.Chart(df_filtered).mark_bar().encode(
                    y=alt.Y('FAIXA_ETARIA:N', title='Faixa Etária'),
                    x=alt.X('count():Q', title='Qtd. Desligamentos'),
                    color=alt.Color('DS_RAZAO_DESLIGAMENTO:N', title='Motivo'),
                    tooltip=['FAIXA_ETARIA', 'DS_RAZAO_DESLIGAMENTO', 'count()']
                ).properties(height=350)
                st.altair_chart(chart_etaria, use_container_width=True)

            with col_g2:
                st.write("#### Comparação Temporal")
                opcoes_tempo = {"1 Mês": 1, "3 Meses": 3, "6 Meses": 6, "1 Ano": 12}
                horizonte = st.pills("Time Horizon:", list(opcoes_tempo.keys()), default="1 Mês", key="pills_horizonte")
                meses_atras = opcoes_tempo[horizonte]
                hoje_ts = pd.Timestamp.now()
                data_limite_atual = hoje_ts - pd.DateOffset(months=meses_atras)
                data_limite_anterior = hoje_ts - pd.DateOffset(months=meses_atras * 2)
                df_atual = df_filtered[df_filtered['DT_DESLIGAMENTO'] >= data_limite_atual]
                df_anterior = df_filtered[(df_filtered['DT_DESLIGAMENTO'] >= data_limite_anterior) & (df_filtered['DT_DESLIGAMENTO'] < data_limite_atual)]
                v1, v2 = len(df_atual), len(df_anterior)
                delta = ((v1 / v2) - 1) * 100 if v2 > 0 else 0
                st.markdown(f"""
                    <div style="background-color: #1F2937; padding: 25px; border-radius: 12px; border: 1px solid #374151; margin-top: 20px;">
                        <div style="color: #9CA3AF; font-size: 14px; text-transform: uppercase;">Vol. {horizonte}</div>
                        <div style="font-size: 44px; font-weight: 800; color: white; margin: 5px 0;">{v1} <span style="font-size: 18px; color: #9CA3AF;">Saídas</span></div>
                        <div style="color: {'#EF4444' if delta > 0 else '#10B981'}; font-weight: bold;">
                            {'↑' if delta > 0 else '↓'} {abs(delta):.1f}% <span style="color: #6B7280; font-weight: normal; font-size: 13px;">vs per. anterior</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            st.write("#### Variação por Motivo")
            if not df_atual.empty:
                motivos_atual = df_atual['DS_RAZAO_DESLIGAMENTO'].value_counts().reset_index()
                motivos_ant = df_anterior['DS_RAZAO_DESLIGAMENTO'].value_counts().reset_index()
                motivos_atual.columns = ['Motivo', 'Atual']
                motivos_ant.columns = ['Motivo', 'Anterior']
                tab_mom = pd.merge(motivos_atual, motivos_ant, on='Motivo', how='outer').fillna(0)
                tab_mom['Tendência'] = tab_mom.apply(lambda row: ((row['Atual']/row['Anterior'])-1)*100 if row['Anterior'] > 0 else 100 if row['Atual'] > 0 else 0, axis=1)
                max_val = tab_mom['Atual'].max()
                html_table = "<table style='width:100%; border-collapse: collapse; color: white;'><tr style='border-bottom: 1px solid #374151; color: #9CA3AF; font-size: 12px;'><th style='text-align:left; padding:10px;'>MOTIVO</th><th style='text-align:center;'>ATUAL</th><th style='text-align:center;'>ANTERIOR</th><th style='text-align:center;'>TENDÊNCIA</th><th style='text-align:left; padding-left:20px;'>INTENSIDADE</th></tr>"
                for _, row in tab_mom.sort_values('Atual', ascending=False).iterrows():
                    color_t = "#EF4444" if row['Tendência'] > 0 else "#10B981"
                    arrow = "↑" if row['Tendência'] > 0 else "↓"
                    pct_bar = (row['Atual'] / max_val * 100) if max_val > 0 else 0
                    html_table += f"<tr style='border-bottom: 1px solid #1F2937;'><td style='padding:12px; font-size:13px;'><b>{row['Motivo']}</b></td><td style='text-align:center;'>{int(row['Atual'])}</td><td style='text-align:center; color:#9CA3AF;'>{int(row['Anterior'])}</td><td style='text-align:center; color:{color_t}; font-size:12px;'>{arrow} {abs(row['Tendência']):.1f}%</td><td style='padding-left:20px;'><div style='background:#374151; width:100px; height:8px; border-radius:4px;'><div style='background:#60A5FA; width:{pct_bar}px; height:8px; border-radius:4px;'></div></div></td></tr>"
                html_table += "</table>"
                st.markdown(html_table, unsafe_allow_html=True)
        
        # ITEM 11: STATUS DE EXPERIÊNCIA E EFETIVAÇÃO (Alinhado visualmente com Unidades)
        st.markdown("---")
        st.write("### Status de Experiência e Efetivação")
        
        anos_formatados_sub = ", ".join(map(str, sorted(selected_years)))
        st.markdown(f"<p style='color: #9CA3AF; margin-top: -15px;'>Análise baseada no período de: {anos_formatados_sub}</p>", unsafe_allow_html=True)
        
        categorias_sub = ['EFETIVADO', 'DESLIGADO APÓS PERÍODO DE EXPERIÊNCIA', 'DESLIGADO NO PERÍODO DE EXPERIÊNCIA', 'EM EXPERIÊNCIA']
        df_sub_filtrado = df_raw[df_raw['DT_ADMISSAO_ANO'].isin(selected_years)].copy()
        df_sub_geral = df_raw.copy()

        cols_sub = st.columns(4)
        for idx, cat in enumerate(categorias_sub):
            qtd_filtrada = len(df_sub_filtrado[df_sub_filtrado['SUB_SITUACAO'].str.upper() == cat])
            qtd_geral = len(df_sub_geral[df_sub_geral['SUB_SITUACAO'].str.upper() == cat])
            is_desligado = "DESLIGADO" in cat
            cor_valor = "#EF4444" if is_desligado else "#10B981"
            badge_bg = "rgba(239, 68, 68, 0.2)" if is_desligado else "rgba(16, 185, 129, 0.2)"
            status_text = "Inativo" if is_desligado else "Ativo/Processo"
            
            html_sub = f"""
            <div class="kpi-container" style="background-color: transparent; padding: 0px; border: none; box-shadow: none;">
                <div class="kpi-title" style="font-size: 11px; min-height: 25px;">{cat}</div>
                <div class="kpi-value" style="color: {cor_valor}; font-size: 38px; margin: 10px 0;">{qtd_filtrada}</div>
                <div class="kpi-subtitle">No período selecionado</div>
                <div class="kpi-subtitle" style="font-size: 12px; color: #9CA3AF; margin-top: 10px;"><b>{qtd_geral}</b> (Geral Histórico)</div>
                <div class="kpi-badge" style="background-color: {badge_bg}; color: {cor_valor}; margin-top: 12px;">{status_text}</div>
            </div>
            """
            cols_sub[idx].markdown(html_sub, unsafe_allow_html=True)

        # ITEM 12: DETALHAMENTO POR OPERAÇÃO (Estilo Barras Item 10)
        st.markdown("---")
        st.write("### Detalhamento por Operação")
        
        anos_formatados_op_det = ", ".join(map(str, sorted(selected_years)))
        st.markdown(f"<p style='color: #9CA3AF; margin-top: -15px;'>Análise baseada no período de: {anos_formatados_op_det}</p>", unsafe_allow_html=True)

        df_op_item12 = df_raw[df_raw['DT_ADMISSAO_ANO'].isin(selected_years)].copy()
        op_summary = df_op_item12.groupby('DS_OPERACAO').agg(
            Total=('SUB_SITUACAO', 'count'),
            Efetivados=('SUB_SITUACAO', lambda x: len(x[x.str.upper() == 'EFETIVADO'])),
            Desligados=('SUB_SITUACAO', lambda x: len(x[x.str.contains('DESLIGADO', case=False, na=False)]))
        ).reset_index().sort_values(by='Total', ascending=False)

        for _, row in op_summary.iterrows():
            perc_efetivado = (row['Efetivados'] / row['Total'] * 100) if row['Total'] > 0 else 0
            html_barra_op = f"""
            <div style="margin-bottom: 20px; padding: 5px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                    <span style="font-size: 14px; font-weight: bold; color: #E5E7EB;">{row['DS_OPERACAO']}</span>
                    <span style="font-size: 12px; color: #9CA3AF;">{row['Total']} Colaboradores</span>
                </div>
                <div style="width: 100%; background-color: #374151; height: 8px; border-radius: 4px; overflow: hidden; display: flex;">
                    <div style="width: {perc_efetivado}%; background-color: #10B981; height: 100%;"></div>
                </div>
                <div style="display: flex; gap: 15px; margin-top: 5px;">
                    <span style="font-size: 11px; color: #10B981;">● {row['Efetivados']} Efetivados ({perc_efetivado:.1f}%)</span>
                    <span style="font-size: 11px; color: #EF4444;">● {row['Desligados']} Desligados</span>
                </div>
            </div>
            """
            st.markdown(html_barra_op, unsafe_allow_html=True)
            
        # ITEM 13: PERFIL GERACIONAL
        st.markdown("---")
        st.subheader("Perfil Geracional por Operação")
        st.markdown(f"<p style='color: #9CA3AF; margin-top: -15px;'>Análise baseada no período de: {anos_formatados_op_det}</p>", unsafe_allow_html=True)
        
        df_f_gen = df_raw[df_raw['DT_ADMISSAO_ANO'].isin(selected_years)].copy()
        op_counts = df_f_gen.groupby(['DS_OPERACAO', 'FAIXA_ETARIA']).size().unstack(fill_value=0)
        cols_gen = st.columns(4)

        for idx, (operacao, row) in enumerate(op_counts.iterrows()):
            with cols_gen[idx % 4]:
                total_op = row.sum()
                st.markdown(f"""
                    <div style='margin-bottom: -10px;'>
                        <p style='color: #9CA3AF; font-size: 11px; font-weight: 600; text-transform: uppercase;'>{operacao}</p>
                        <h2 style='color: white; margin: 0;'>{total_op}</h2>
                        <p style='color: #60A5FA; font-size: 11px; margin-top: -5px;'>Total Headcount</p>
                    </div>
                    <div style='border-top: 1px solid #1F2937; margin: 10px 0;'></div>
                """, unsafe_allow_html=True)
                
                for faixa, qtd in row.items():
                    perc = (qtd / total_op) if total_op > 0 else 0
                    fill_width = int(perc * 100)
                    st.markdown(f"""
                        <div style="margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; font-size: 11px; color: #9CA3AF;">
                                <span>{faixa}</span>
                                <span style="color: white;">{int(qtd)}</span>
                            </div>
                            <div style="width: 100%; background-color: #374151; height: 4px; border-radius: 2px;">
                                <div style="width: {fill_width}%; background-color: #60A5FA; height: 100%; border-radius: 2px;"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

        # ITEM 14: DISTRIBUIÇÃO POR CARGA HORÁRIA
        st.markdown("---")
        st.write("## Distribuição por Carga Horária")
        
        # AJUSTE: Subtítulo informando o período selecionado
        anos_formatados_vagas = ", ".join(map(str, sorted(selected_years)))
        st.markdown(f"<p style='color: #9CA3AF; margin-top: -15px;'>Análise baseada no período de: {anos_formatados_vagas}</p>", unsafe_allow_html=True)

        # Filtros de Operação e Status (Mantidos inalterados)
        col_f1_v, col_f2_v = st.columns(2)

        with col_f1_v:
            lista_ops_vagas = ["Todas"] + sorted(df_raw['DS_OPERACAO'].unique().tolist())
            op_vagas = st.selectbox("Filtrar por Operação:", lista_ops_vagas, key="filtro_op_vagas")

        with col_f2_v:
            status_vagas = st.radio("Status dos Colaboradores:", ["Todos", "Ativos", "Desligados"], horizontal=True, key="filtro_status_vagas")

        # Lógica de Filtragem Segura
        df_vagas = df_raw.copy()

        # AJUSTE: Aplicação do filtro de ano global (selected_years)
        # Filtra por DT_ADMISSAO_ANO para Ativos ou DT_DESLIGAMENTO_ANO para Desligados de forma abrangente
        df_vagas = df_vagas[
            (df_vagas['DT_ADMISSAO_ANO'].isin(selected_years)) | 
            (df_vagas['DT_DESLIGAMENTO_ANO'].isin(selected_years))
        ]

        if op_vagas != "Todas":
            df_vagas = df_vagas[df_vagas['DS_OPERACAO'] == op_vagas]

        if status_vagas == "Ativos":
            df_vagas = df_vagas[df_vagas['DS_SITUACAO'].str.contains('TRABALHANDO|ATIVO|FÉRIAS', case=False, na=False)]
        elif status_vagas == "Desligados":
            df_vagas = df_vagas[df_vagas['DS_SITUACAO'].str.contains('DEMISSÃO|DESLIGADO', case=False, na=False)]

        # Verificação do nome da coluna (TM_CARGA_HORARIA conforme ITEM 3)
        col_busca = 'TM_CARGA_HORARIA' 

        if col_busca in df_vagas.columns:
            dist_carga = df_vagas[col_busca].value_counts().reset_index()
            dist_carga.columns = ['Carga', 'Quantidade']
            total_geral_v = dist_carga['Quantidade'].sum()

            if total_geral_v > 0:
                st.info(f"Exibindo dados para {total_geral_v} colaboradores encontrados.")
                
                cols_vagas = st.columns(4)
                for i, row in dist_carga.iterrows():
                    with cols_vagas[i % 4]:
                        percentual = (row['Quantidade'] / total_geral_v) * 100
                        
                        # HTML Ajustado: Sem background, com margens mínimas e nova cor #00FFB9
                        st.markdown(f"""
                            <div style="margin-bottom: 15px; padding: 5px 0;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                    <span style="font-size: 13px; color: #9CA3AF; font-weight: 500;">{row['Carga']}</span>
                                    <span style="font-size: 16px; font-weight: bold; color: white;">{row['Quantidade']}</span>
                                </div>
                                <div style="width: 100%; background-color: #374151; height: 6px; border-radius: 3px; overflow: hidden;">
                                    <div style="width: {percentual}%; background-color: #00FFB9; height: 100%; border-radius: 3px;"></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("Nenhum dado encontrado para os filtros selecionados.")
        else:
            st.error(f"A coluna '{col_busca}' não foi detectada. Verifique o arquivo de dados.")

        # ITEM 15: DISTRIBUIÇÃO POR JORNADA (MODELO TABELA TÉCNICA)
        st.markdown("---")
        st.write("## Detalhamento de Jornadas (Turnos)")
        
        # AJUSTE: Subtítulo informando o período selecionado
        anos_formatados_jor = ", ".join(map(str, sorted(selected_years)))
        st.markdown(f"<p style='color: #9CA3AF; margin-top: -15px;'>Análise baseada no período de: {anos_formatados_jor}</p>", unsafe_allow_html=True)

        # AJUSTE: Filtro de Status para Jornada
        status_jor = st.radio("Status:", ["Todos", "Ativos", "Desligados"], horizontal=True, key="filtro_status_jor")

        # Aplicação da filtragem de status baseada no df_vagas (que já possui o filtro de ano e operação)
        df_jor_filtrado = df_vagas.copy()

        if status_jor == "Ativos":
            df_jor_filtrado = df_jor_filtrado[df_jor_filtrado['DS_SITUACAO'].str.contains('TRABALHANDO|ATIVO|FÉRIAS', case=False, na=False)]
        elif status_jor == "Desligados":
            df_jor_filtrado = df_jor_filtrado[df_jor_filtrado['DS_SITUACAO'].str.contains('DEMISSÃO|DESLIGADO', case=False, na=False)]

        col_busca_jor = 'JORNADA' 
        if col_busca_jor in df_jor_filtrado.columns:
            # Ordenar pelos turnos com mais pessoas para um visual mais organizado
            dist_jor = df_jor_filtrado[col_busca_jor].value_counts().reset_index()
            dist_jor.columns = ['Jornada', 'Quantidade']
            total_j = dist_jor['Quantidade'].sum()

            if total_j > 0:
                # Cabeçalho da Tabela com alinhamento fixo
                st.markdown(f"""
                <div style="margin-bottom: 10px; border-bottom: 2px solid #374151; padding-bottom: 8px; display: flex; color: #9CA3AF; font-size: 12px; font-weight: bold; text-transform: uppercase;">
                    <div style="flex: 2;">Jornada</div>
                    <div style="flex: 1; text-align: center;">Quantidade</div>
                    <div style="flex: 3; padding-left: 20px;">Intensidade</div>
                </div>
                """, unsafe_allow_html=True)

                for _, row in dist_jor.iterrows():
                    perc_j = (row['Quantidade'] / total_j) * 100
                    
                    # Linha da Tabela - Usando Flexbox para garantir alinhamento do modelo
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #1F2937; color: white;">
                        <div style="flex: 2; font-size: 13px;">{row['Jornada']}</div>
                        <div style="flex: 1; text-align: center; font-weight: bold; font-size: 14px;">{row['Quantidade']}</div>
                        <div style="flex: 3; padding-left: 20px;">
                            <div style="background: #1F2937; width: 100%; height: 8px; border-radius: 4px; overflow: hidden;">
                                <div style="background: #00FFB9; width: {perc_j}%; height: 8px; border-radius: 4px;"></div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Ajuste os filtros para visualizar os dados.")
        else:
            st.error(f"Coluna '{col_busca_jor}' não encontrada na base de dados.")
            
        # ITEM 16: VARIAÇÃO MENSAL DE TURNOVER (% MoM)
        st.markdown("---")
        # st.write("## 📈 Variação Mensal de Turnover (% MoM)")
        # Título com ícone SVG alinhado ao padrão dbm
        col_icon, col_title_to = st.columns([1, 15])
        with col_icon:
             svg_icon_chart = """
             <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-top: 5px;">
             <path d="M21 21H3V3H5V19H21V21ZM17.41 7.41L21 11L19.59 12.41L16 8.83L12 12.83L8 8.83L5.41 11.41L4 10L8 6L12 10L16 6L17.41 7.41Z" fill="#E5E7EB"/>
             </svg>
             """
             st.markdown(svg_icon_chart, unsafe_allow_html=True)
        with col_title_to:
             st.markdown("## Variação Mensal de Turnover (% MoM)")
        
        # 2. MENSAGEM DINÂMICA SIMPLIFICADA (Upgrade 2)
        # Removido "Janeiro a Dezembro" para evitar confusão.
        anos_str = ", ".join(map(str, selected_years))
        st.write(f"Exibindo dados históricos de: **{anos_str}**")

        # 1. FILTRO PADRONIZADO (Upgrade 1 - st.pills no estilo image_0fd4b9.png)
        lista_ops_to = sorted(df_raw['DS_OPERACAO'].unique().tolist())
        st.write("### Filtrar Unidade para o Gráfico:")
        sel_op_to = st.pills(
            "",
            ["Todas"] + lista_ops_to,
            default="Todas",
            key="pills_item16"
        )

        # Filtragem dos dados (Mantido do script original)
        df_to_real = df_raw.copy()
        if sel_op_to != "Todas":
            df_to_real = df_to_real[df_to_real['DS_OPERACAO'] == sel_op_to]
        
        df_to_real = df_to_real[df_to_real['DT_DESLIGAMENTO_ANO'].isin(selected_years)]
        df_to_real = df_to_real.dropna(subset=['DT_DESLIGAMENTO'])

        if not df_to_real.empty:
            # AGRUPAMENTO ESSENCIAL (Mantido do script original)
            df_to_real['MES_NUM'] = df_to_real['DT_DESLIGAMENTO'].dt.month
            df_to_real['MES_NOME'] = df_to_real['DT_DESLIGAMENTO'].dt.strftime('%b')
            
            df_plot = df_to_real.groupby(['MES_NUM', 'MES_NOME']).size().reset_index(name='Qtd')
            df_plot = df_plot.sort_values('MES_NUM')

            valores = df_plot['Qtd'].tolist()
            meses = df_plot['MES_NOME'].tolist()

            # Cálculo de Deltas (Mantido do script original)
            deltas = [0.0]
            for i in range(1, len(valores)):
                v_ant = valores[i-1]
                v_atual = valores[i]
                diff = ((v_atual - v_ant) / v_ant * 100) if v_ant > 0 else 0
                deltas.append(diff)

            # LAYOUT SPLIT (70/30) (Mantido do script original)
            col_chart, col_insight = st.columns([7, 3])

            with col_chart:
                fig_to = go.Figure()

                # Gráfico Spline com formatação MoM (Mantido do script original)
                # Formatação Condicional de Cores: Turnover sobe -> Vermelho (#F87171) / Turnover cai -> Verde (#10B981)
                fig_to.add_trace(go.Scatter(
                    x=meses, 
                    y=valores,
                    mode='lines+markers+text',
                    line=dict(color='#00FFB9', width=3, shape='spline'),
                    fill='tozeroy',
                    fillcolor='rgba(0, 255, 185, 0.05)',
                    marker=dict(size=8, color='#111827', line=dict(width=2, color='#00FFB9')),
                    text=[f"<b>{v}</b><br><span style='color:{'#F87171' if d > 0 else '#10B981'}'>{'▲' if d > 0 else '▼'} {abs(d):.1f}%</span>" 
                          for v, d in zip(valores, deltas)],
                    textposition="top center"
                ))

                fig_to.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=30, b=0),
                    showlegend=False,
                    xaxis=dict(showgrid=False, color='#9CA3AF'),
                    yaxis=dict(showgrid=False, showticklabels=False),
                    height=350 
                )
                st.plotly_chart(fig_to, use_container_width=True)

            with col_insight:
                # 3. VISUAL DO INSIGHT MELHORADO (Upgrade 3)
                # Criando um card HTML customizado para o Insight
                st.markdown("### 💡 Resumo do Storytelling")
                if len(deltas) > 1:
                    maior_queda = min(deltas)
                    maior_alta = max(deltas)
                    mes_queda = meses[deltas.index(maior_queda)]
                    mes_alta = meses[deltas.index(maior_alta)]
                    
                    st.markdown(f"""
                        <div style="background-color: #1F2937; padding: 20px; border-radius: 12px; border: 1px solid #374151;">
                            <p style="color: #9CA3AF; font-size: 14px;"><strong>Ponto Positivo:</strong><br>
                            A maior retenção de equipe ocorreu em <b>{mes_queda}</b>, com uma redução de desligamentos de <span style="color: #10B981;">{abs(maior_queda):.1f}%</span> MoM.</p>
                            <hr style="border-color: #374151;">
                            <p style="color: #9CA3AF; font-size: 14px;"><strong>Ponto de Atenção:</strong><br>
                            O mês de <b>{mes_alta}</b> registrou o maior pico de turnover, com aumento de <span style="color: #F87171;">{maior_alta:.1f}%</span>.</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("Insights insuficientes para calcular a tendência.")

        else:
            st.info("Sem dados de desligamento para os filtros selecionados.")
            
        # --- ITEM 17: RANKING DE TURNOVER POR SUPERVISOR ---
        st.markdown("---")
        
        # Título com ícone SVG
        col_icon_sup, col_title_sup = st.columns([1, 15])
        with col_icon_sup:
            st.markdown("""
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-top: 5px;">
                <path d="M16 11C17.66 11 18.99 9.66 18.99 8C18.99 6.34 17.66 5 16 5C14.34 5 13 6.34 13 8C13 9.66 14.34 11 16 11ZM8 11C9.66 11 10.99 9.66 10.99 8C10.99 6.34 9.66 5 8 5C6.34 5 5 6.34 5 8C5 9.66 6.34 11 8 11ZM8 13C5.67 13 1 14.17 1 16.5V19H15V16.5C15 14.17 10.33 13 8 13ZM16 13C15.71 13 15.38 13.02 15.03 13.05C16.19 13.89 17 15.02 17 16.5V19H23V16.5C23 14.17 18.33 13 16 13Z" fill="#E5E7EB"/>
                </svg>
            """, unsafe_allow_html=True)
        with col_title_sup:
            st.markdown("## Ranking de Turnover por Supervisor")
            anos_formatados_sup = ", ".join(map(str, sorted(selected_years)))
            st.markdown(f"<p style='color: #9CA3AF; margin-top: -15px;'>Exibindo dados históricos de: {anos_formatados_sup}</p>", unsafe_allow_html=True)

        # FILTROS PADRONIZADOS
        col_f_op, col_f_mes = st.columns([1, 1])
        
        with col_f_op:
            lista_ops_sup = ["Todas"] + sorted(df_raw['DS_OPERACAO'].unique().tolist())
            selected_op_sup = st.pills("Filtrar Operação:", lista_ops_sup, default="Todas", key="pills_op_sup")
        
        with col_f_mes:
            meses_nomes = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
            selected_mes_sup = st.multiselect("Filtrar Meses:", options=list(meses_nomes.keys()), format_func=lambda x: meses_nomes[x], key="multi_mes_sup")

        # --- LÓGICA DE FILTRAGEM CORRIGIDA ---
        # 1. Base completa para garantir que Ativos apareçam na tabela
        df_sup_base = df_raw.copy()

        # 2. Flag de Ativo/Desligado (Base Geral)
        df_sup_base['ATIVO'] = df_sup_base['DT_DESLIGAMENTO'].apply(lambda x: 1 if pd.isna(x) else 0)
        df_sup_base['DESLIGADO'] = df_sup_base['DT_DESLIGAMENTO'].apply(lambda x: 1 if pd.notna(x) else 0)

        # 3. Preparação do DataFrame para o Gráfico (Somente Desligados do Período)
        df_ranking = df_sup_base[df_sup_base['DESLIGADO'] == 1].copy()
        df_ranking = df_ranking[df_ranking['DT_DESLIGAMENTO_ANO'].isin(selected_years)]
        
        if selected_op_sup != "Todas":
            df_ranking = df_ranking[df_ranking['DS_OPERACAO'] == selected_op_sup]
        if selected_mes_sup:
            df_ranking = df_ranking[df_ranking['DT_DESLIGAMENTO'].dt.month.isin(selected_mes_sup)]

        # Limpeza de Supervisores no Ranking
        supervisores_excluir = ['ANA CAROLINA', 'FABRICIA SEZERBAN', 'NÃO POSSUI', 'ELIDIANE', 'REBECA FERNANDES', 'NELSON MANFRE', 'PABLO MOLINA', 'DAIANE ZBOROWSKI']
        df_ranking['TX_SUPERVISOR'] = df_ranking['TX_SUPERVISOR'].str.upper().fillna('NÃO INFORMADO')
        df_ranking = df_ranking[~df_ranking['TX_SUPERVISOR'].isin(supervisores_excluir)]

        if not df_ranking.empty:
            # Gráfico de Barras Horizontal
            df_rank_sup = df_ranking.groupby('TX_SUPERVISOR').size().reset_index(name='Qtd_Saidas')
            total_saidas_filtro = df_rank_sup['Qtd_Saidas'].sum()
            df_rank_sup['Perc_TO'] = (df_rank_sup['Qtd_Saidas'] / total_saidas_filtro) * 100
            df_rank_sup = df_rank_sup.sort_values(by='Qtd_Saidas', ascending=False).head(10)

            col_chart_sup, col_insight_sup = st.columns([7, 3])

            with col_chart_sup:
                fig_sup = go.Figure()
                fig_sup.add_trace(go.Bar(
                    x=df_rank_sup['Qtd_Saidas'],
                    y=df_rank_sup['TX_SUPERVISOR'],
                    orientation='h',
                    marker=dict(color=df_rank_sup['Qtd_Saidas'], colorscale=[[0, '#1F2937'], [1, '#EF4444']]),
                    text=df_rank_sup.apply(lambda r: f"{r['Qtd_Saidas']} ({r['Perc_TO']:.1f}%)", axis=1),
                    textposition='auto',
                    textfont=dict(color="white")
                ))
                fig_sup.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=10, b=10),
                    xaxis=dict(showgrid=False, visible=False),
                    yaxis=dict(autorange="reversed", color="#E5E7EB"),
                    height=400
                )
                st.plotly_chart(fig_sup, use_container_width=True)

            with col_insight_sup:
                top_supervisor = df_rank_sup.iloc[0]['TX_SUPERVISOR']
                top_valor = df_rank_sup.iloc[0]['Qtd_Saidas']
                st.markdown(f"""
                    <div style="background-color: #1F2937; padding: 20px; border-radius: 12px; border: 1px solid #374151; margin-top: 20px;">
                        <p style="color: #9CA3AF; font-size: 12px; text-transform: uppercase; font-weight: bold;">⚠️ Maior Volumetria</p>
                        <h3 style="color: #F87171; margin: 5px 0;">{top_supervisor}</h3>
                        <p style="color: #E5E7EB; font-size: 14px;">Concentra <b>{top_valor} desligamentos</b> no período.</p>
                    </div>
                """, unsafe_allow_html=True)

            # --- TABELA DETALHADA (COM LÓGICA DE FILTRO UNIVERSAL) ---
            st.markdown("### Detalhamento Analitico")
            # Filtro da Tabela deve seguir a Operação selecionada para mostrar Ativos daquela Unidade
            df_tabela = df_sup_base.copy()
            if selected_op_sup != "Todas":
                df_tabela = df_tabela[df_tabela['DS_OPERACAO'] == selected_op_sup]

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

            # Ordenação: Supervisores A-Z e Ativos primeiro
            df_tabela_final = df_tabela_final.sort_values(by=['TX_SUPERVISOR', 'ATIVO'], ascending=[True, False])

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
            
            # --- NOVO: BOTÃO DE DOWNLOAD ---
            df_xlsx = to_excel(df_tabela_final)
            st.download_button(
                label="Baixar Tabela em Excel",
                data=df_xlsx,
                file_name='detalhamento_analitico.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        else:
            st.info("Não há dados para os filtros aplicados nesta seção.")
            
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