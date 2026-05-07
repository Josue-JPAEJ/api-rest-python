from unittest.mock import patch


def test_emite_evento_status_update_no_post(app_module, auth_editor_headers):
    socket_client = app_module.socketio.test_client(app_module.app, flask_test_client=app_module.app.test_client())

    with patch.object(app_module.manager, 'insert', return_value=1):
        response = app_module.app.test_client().post('/status', json={'status': 'ATIVO'}, headers=auth_editor_headers)

    assert response.status_code == 201

    events = socket_client.get_received()
    event_names = [event['name'] for event in events]
    assert 'status update' in event_names
