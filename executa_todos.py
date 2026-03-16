from import_chamadas_gerais import executar_e_salvar_chamadas_gerais
from import_chamadas_dlocal import executar_e_salvar_dlocal
from import_chamadas_cassems import executar_e_salvar_cassems
from import_tabulacoes_n2_falcon import executar_e_salvar_tabulacoes_n2_falcon
from import_tabulacoes_n2_jira_prevencao import executar_e_salvar_tabulacoes_n2_jira_prevencao 
from import_tabulacoes_n2_jira import executar_e_salvar_tabulacoes_n2_jira
from import_tabulacoes_n3_emissores import executar_e_salvar_tabulacoes_n3_emissores
from import_tabulacoes_n3_visa import executar_e_salvar_tabulacoes_n3_visa
from import_tabulacoes_n3_jira import executar_e_salvar_tabulacoes_n3_jira
from import_tabulacoes_n3_master import executar_e_salvar_tabulacoes_n3_master
from import_tabulacoes_onboardingBPP import executar_e_salvar_tabulacoes_OnboardingBPP
from import_tabulacoes_onboardingJira import executar_e_salvar_tabulacoes_OnboardingJira
from import_tabulacoes_onboardingPF import executar_e_salvar_tabulacoes_OnboardingPF
from import_tabulacoes_onboardingPJ_Manual import executar_e_salvar_tabulacoes_OnboardingPJ_Manual
from import_tabulacoes_onboardingPJ import executar_e_salvar_tabulacoes_OnboardingPJ
from import_tabulacoes_onboardingPLD import executar_e_salvar_tabulacoes_OnboardingPLD
from import_monitoria import executar_e_salvar_monitoria
from import_quadro_op import executar_e_salvar_quadro_operacional
from import_quadro_directive import executar_e_salvar_quadro_directive
from import_tempo_logado_nexus import executar_e_salvar_tempo_logado_nexus
from import_ponto_senior import executar_e_salvar_ponto_senior

def main():
    print("Iniciando fluxo completo de extração...")
    
    # Lista de tuplas contendo o identificador do processo e a funcao correspondente
    processos = [
        ("Chamadas Gerais", executar_e_salvar_chamadas_gerais),
        ("Chamadas Dlocal", executar_e_salvar_dlocal),
        ("Chamadas Cassems", executar_e_salvar_cassems),
        ("Tabulações N2 Falcon", executar_e_salvar_tabulacoes_n2_falcon),
        ("Tabulações N2 Jira Prevenção", executar_e_salvar_tabulacoes_n2_jira_prevencao),
        ("Tabulações N2 Jira", executar_e_salvar_tabulacoes_n2_jira),
        ("Tabulações N3 Emissores", executar_e_salvar_tabulacoes_n3_emissores),
        ("Tabulações N3 Visa", executar_e_salvar_tabulacoes_n3_visa),
        ("Tabulações N3 Jira", executar_e_salvar_tabulacoes_n3_jira),
        ("Tabulações N3 Master", executar_e_salvar_tabulacoes_n3_master),
        ("Tabulações OnboardingBPP", executar_e_salvar_tabulacoes_OnboardingBPP),
        ("Tabulações OnboardingJira", executar_e_salvar_tabulacoes_OnboardingJira),
        ("Tabulações OnboardingPF", executar_e_salvar_tabulacoes_OnboardingPF),
        ("Tabulações OnboardingPJ_Manual", executar_e_salvar_tabulacoes_OnboardingPJ_Manual),
        ("Tabulações OnboardingPJ", executar_e_salvar_tabulacoes_OnboardingPJ),
        ("Tabulações OnboardingPLD", executar_e_salvar_tabulacoes_OnboardingPLD),
        ("Monitorias Qualidade", executar_e_salvar_monitoria),
        ("Quadro Operacional", executar_e_salvar_quadro_operacional),
        ("Quadro Directive", executar_e_salvar_quadro_directive),
        ("Tempo logado Nexus", executar_e_salvar_tempo_logado_nexus),
        ("Ponto Senior", executar_e_salvar_ponto_senior)
    ]
    
    # Iteracao sobre a lista de processos para execucao sequencial
    for nome, funcao in processos:
        print(f"\n--- Executando: {nome} ---")
        try:
            # Chama a funcao de extracao e salvamento definida em cada modulo
            funcao()
        except Exception as e:
            # Captura erros individuais permitindo que a execucao do restante da fila continue
            print(f"Erro no módulo {nome}: {e}")
    print("\nProcesso finalizado.")

if __name__ == "__main__":
    main()