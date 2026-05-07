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
        response = self.client.post('/status', json={'status': 'abc123'}, headers={'X-Request-ID': 'req-123'})

        self.assertEqual(response.status_code, 422)
        body = response.get_json()
        self.assertEqual(body['code'], 'UNPROCESSABLE_ENTITY')
        self.assertEqual(body['request_id'], 'req-123')
        self.assertNotIn('traceback', body)
        self.assertNotIn('exception', body)


    def test_erro_dominio_retorna_422(self):
        import main

        with patch.object(main.manager, 'select', side_effect=main.DomainValidationError('identificador inválido')):
            response = self.client.get('/status', headers={'X-Request-ID': 'req-422'})

        self.assertEqual(response.status_code, 422)
        body = response.get_json()
        self.assertEqual(body['code'], 'UNPROCESSABLE_ENTITY')
        self.assertEqual(body['request_id'], 'req-422')

    def test_erro_interno_retorna_500_sem_detalhes(self):
        import main

        with patch.object(main.manager, 'select', side_effect=RuntimeError('falha sensivel interna')):
            response = self.client.get('/status', headers={'X-Request-ID': 'req-500'})

        self.assertEqual(response.status_code, 500)
        body = response.get_json()
        self.assertEqual(body['code'], 'INTERNAL_SERVER_ERROR')
        self.assertEqual(body['request_id'], 'req-500')
        self.assertEqual(body['message'], 'Erro interno do servidor')
        self.assertNotIn('traceback', body)
        self.assertNotIn('error', body)


if __name__ == '__main__':
    unittest.main()
