import streamlit as st
from app_quadro_st import run_headcount_dashboard
# from app.app_quadro_st import run_headcount_dashboard

st.set_page_config(page_title="Dashboard", layout="wide", page_icon="")

#
with st.sidebar:
    st.title("Menu de Navegação")
    
    pagina = st.radio(
        "Navegação", 
        ["Dashboard", "CX Monitoria", "Headcount & Turnover", "Analytics", "Reports"]
    )

if pagina == "Dashboard":
    st.title("Dashboard")
    st.write("Bem-vindo ao painel principal.")

elif pagina == "CX Monitoria":
    st.title("CX Monitoria")
    st.write("Módulo em construção.")

elif pagina == "Headcount & Turnover":

    run_headcount_dashboard()

elif pagina == "Analytics":
    st.title("Analytics")
    st.write("Módulo em construção.")

elif pagina == "Reports":
    st.title("Reports")
    st.write("Módulo em construção.")