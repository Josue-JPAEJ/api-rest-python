from datetime import datetime as dt


def somente_letras(texto: str) -> bool:
    if texto.replace(' ', '').isalpha():
        return True
    else:
        return False


def converter_data_para_ddmmaaaa(data: str) -> str:
    try:
        data = dt.strptime(data, '%Y-%m-%d')
        data_formatada = data.strftime('%d/%m/%Y')
        return data_formatada
    except ValueError as e:
        raise ValueError(f"Erro ao converter a data {data}. Erro: {e}")


def converter_data_para_yyyymmdd(data: str) -> str:
    try:
        data = dt.strptime(data, '%d/%m/%Y')
        data_formatada = data.strftime('%Y-%m-%d')
        return data_formatada
    except ValueError as e:
        raise ValueError(f"Erro ao converter a data {data}. Erro: {e}")


def verificar_se_e_data(data: str, formato='%Y-%m-%d') -> bool:
    try:
        dt.strptime(data, formato)
        return True
    except ValueError as e:
        return False
