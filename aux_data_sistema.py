from datetime import date, datetime, timedelta


def obter_datas(automatico=0):
    automatico = 0

    if automatico == 0:
        inicio_obj = date.today().replace(day=1)
        fim_obj = date.today()
        inicio = str(inicio_obj)
        fim = str(fim_obj)
    else:
        inicio = '2025-01-01'
        fim = '2026-08-17'

    ano = inicio[0:4]
    mes = inicio[5:7]

    # print(f'Início: {inicio}')
    # print(f'Fim: {fim}')
    
    return {
        'inicio': inicio,
        'fim': fim,
        'ano': ano,
        'mes': mes
    }


if __name__ == '__main__':
    obter_datas()