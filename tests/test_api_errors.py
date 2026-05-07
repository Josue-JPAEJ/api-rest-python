import unittest
from unittest.mock import patch


class TestApiErrors(unittest.TestCase):
    def setUp(self):
        conexao_patch = patch('db.ConexaoDB.__init__', return_value=None)
        self.addCleanup(conexao_patch.stop)
        conexao_patch.start()

        import main

        self.app = main.app
        self.client = self.app.test_client()

    def test_validacao_retorna_4xx_sem_traceback(self):
        response = self.client.post('/status', json={'status': 'abc123'}, headers={'X-Request-ID': 'req-123', 'X-User-Id': 'u-1', 'X-User-Role': 'status_editor'})

        self.assertEqual(response.status_code, 422)
        body = response.get_json()
        self.assertEqual(body['code'], 'UNPROCESSABLE_ENTITY')
        self.assertEqual(body['request_id'], 'req-123')
        self.assertNotIn('traceback', body)
        self.assertNotIn('exception', body)


    def test_erro_dominio_retorna_422(self):
        import main

        with patch.object(main.manager, 'select', side_effect=main.DomainValidationError('identificador inválido')):
            response = self.client.get('/status', headers={'X-Request-ID': 'req-422', 'X-User-Id': 'u-1', 'X-User-Role': 'status_reader'})

        self.assertEqual(response.status_code, 422)
        body = response.get_json()
        self.assertEqual(body['code'], 'UNPROCESSABLE_ENTITY')
        self.assertEqual(body['request_id'], 'req-422')

    def test_erro_interno_retorna_500_sem_detalhes(self):
        import main

        with patch.object(main.manager, 'select', side_effect=RuntimeError('falha sensivel interna')):
            response = self.client.get('/status', headers={'X-Request-ID': 'req-500', 'X-User-Id': 'u-1', 'X-User-Role': 'status_reader'})

        self.assertEqual(response.status_code, 500)
        body = response.get_json()
        self.assertEqual(body['code'], 'INTERNAL_SERVER_ERROR')
        self.assertEqual(body['request_id'], 'req-500')
        self.assertEqual(body['message'], 'Erro interno do servidor')
        self.assertNotIn('traceback', body)
        self.assertNotIn('error', body)




    def test_autenticacao_ausente_retorna_401(self):
        response = self.client.get('/status', headers={'X-Request-ID': 'req-401'})

        self.assertEqual(response.status_code, 401)
        body = response.get_json()
        self.assertEqual(body['code'], 'UNAUTHORIZED')

    def test_autorizacao_insuficiente_retorna_403(self):
        response = self.client.post(
            '/status',
            json={'status': 'ATIVO'},
            headers={'X-Request-ID': 'req-403', 'X-User-Id': 'u-2', 'X-User-Role': 'status_reader'},
        )

        self.assertEqual(response.status_code, 403)
        body = response.get_json()
        self.assertEqual(body['code'], 'FORBIDDEN')

    def test_leitura_autorizada_retorna_200(self):
        import main

        with patch.object(main.manager, 'select', return_value=[{'id': 1, 'status': 'ATIVO'}]):
            response = self.client.get(
                '/status',
                headers={'X-Request-ID': 'req-200', 'X-User-Id': 'u-3', 'X-User-Role': 'status_reader'},
            )

        self.assertEqual(response.status_code, 200)

    def test_escrita_autorizada_retorna_201(self):
        import main

        with patch.object(main.manager, 'insert', return_value=1):
            response = self.client.post(
                '/status',
                json={'status': 'ATIVO'},
                headers={'X-Request-ID': 'req-201', 'X-User-Id': 'u-4', 'X-User-Role': 'status_editor'},
            )

        self.assertEqual(response.status_code, 201)


if __name__ == '__main__':
    unittest.main()
