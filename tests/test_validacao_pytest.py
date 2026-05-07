import pytest

import validacao


def test_somente_letras_aceita_texto_com_espacos():
    assert validacao.somente_letras('Status Ativo') is True


def test_somente_letras_rejeita_numeros():
    assert validacao.somente_letras('Status1') is False


def test_converter_data_para_ddmmaaaa_sucesso():
    assert validacao.converter_data_para_ddmmaaaa('2026-05-07') == '07/05/2026'


def test_converter_data_para_ddmmaaaa_data_invalida():
    with pytest.raises(ValueError):
        validacao.converter_data_para_ddmmaaaa('07-05-2026')


def test_converter_data_para_yyyymmdd_sucesso():
    assert validacao.converter_data_para_yyyymmdd('07/05/2026') == '2026-05-07'


def test_verificar_se_e_data_retorna_false_para_invalida():
    assert validacao.verificar_se_e_data('2026-13-40') is False
