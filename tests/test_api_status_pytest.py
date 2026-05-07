from unittest.mock import patch


def test_get_status_happy_path(client, app_module, auth_reader_headers):
    with patch.object(app_module.manager, 'select', return_value=[{'id': 1, 'status': 'ATIVO'}]):
        response = client.get('/status', headers=auth_reader_headers)

    assert response.status_code == 200
    assert response.get_json() == {'status': [{'id': 1, 'status': 'ATIVO'}]}


def test_post_status_happy_path(client, app_module, auth_editor_headers):
    with patch.object(app_module.manager, 'insert', return_value=1):
        response = client.post('/status', json={'status': 'ativo'}, headers=auth_editor_headers)

    assert response.status_code == 201
    assert response.get_json()['message'] == 'Status criado com sucesso'


def test_put_status_happy_path(client, app_module, auth_editor_headers):
    with patch.object(app_module.manager, 'update', return_value=1):
        response = client.put('/status/1', json={'status': 'inativo'}, headers=auth_editor_headers)

    assert response.status_code == 200
    assert response.get_json()['message'] == 'Status atualizado com sucesso'


def test_post_status_payload_invalido_retorna_422(client, auth_editor_headers):
    response = client.post('/status', json={'status': 'ATIVO-1'}, headers=auth_editor_headers)

    assert response.status_code == 422
    assert response.get_json()['code'] == 'UNPROCESSABLE_ENTITY'


def test_put_status_nao_encontrado_retorna_404(client, app_module, auth_editor_headers):
    with patch.object(app_module.manager, 'update', return_value=0):
        response = client.put('/status/99', json={'status': 'ATIVO'}, headers=auth_editor_headers)

    assert response.status_code == 404
    assert response.get_json()['code'] == 'NOT_FOUND'
