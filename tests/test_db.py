import os
import unittest

from db import ConexaoDB, DatabaseConfigError


class TestConexaoDBConfig(unittest.TestCase):
    def test_falha_quando_secret_obrigatorio_ausente(self):
        backup = {key: os.environ.get(key) for key in ('DB_SERVER', 'DB_NAME', 'DB_USER', 'DB_PASSWORD')}
        try:
            os.environ['DB_SERVER'] = 'tcp:server.database.windows.net,1433'
            os.environ['DB_NAME'] = 'db_teste'
            os.environ['DB_USER'] = 'usuario_teste'
            os.environ.pop('DB_PASSWORD', None)

            with self.assertRaises(DatabaseConfigError) as exc:
                ConexaoDB()

            self.assertIn('DB_PASSWORD', str(exc.exception))
        finally:
            for key, value in backup.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == '__main__':
    unittest.main()
