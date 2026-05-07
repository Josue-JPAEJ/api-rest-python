import os
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from db import ConexaoDB, DatabaseConfigError, DatabaseManager, DomainValidationError


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


class TestDatabaseManagerDelete(unittest.TestCase):
    def test_delete_usa_sql_parametrizada(self):
        manager = DatabaseManager(conex=object())

        with patch.object(manager, 'execute', return_value=1) as execute_mock:
            manager.delete('status', 10)

        execute_mock.assert_called_once_with(
            'UPDATE status SET status = :status WHERE id = :id',
            {'status': 4, 'id': 10},
        )

    def test_delete_altera_apenas_uma_linha_para_id_valido(self):
        class SqliteConexao:
            def __init__(self):
                self.engine = create_engine('sqlite:///:memory:')
                self.Session = sessionmaker(bind=self.engine)

            @contextmanager
            def conexao(self):
                session = self.Session()
                try:
                    yield session
                    session.commit()
                except Exception:
                    session.rollback()
                    raise
                finally:
                    session.close()

        conex = SqliteConexao()
        with conex.conexao() as session:
            session.execute(text('CREATE TABLE status (id INTEGER PRIMARY KEY, status INTEGER NOT NULL)'))
            session.execute(text('INSERT INTO status (id, status) VALUES (1, 1), (2, 1)'))

        manager = DatabaseManager(conex=conex)
        rows = manager.delete('status', 1)

        self.assertEqual(rows, 1)

        with conex.conexao() as session:
            status_id_1 = session.execute(text('SELECT status FROM status WHERE id = 1')).scalar()
            status_id_2 = session.execute(text('SELECT status FROM status WHERE id = 2')).scalar()

        self.assertEqual(status_id_1, 4)
        self.assertEqual(status_id_2, 1)


class TestDatabaseManagerSecurity(unittest.TestCase):
    def setUp(self):
        self.manager = DatabaseManager(conex=object())

    def test_rejeita_injection_em_table(self):
        with self.assertRaises(DomainValidationError):
            self.manager.select('status; DROP TABLE status')

    def test_rejeita_where_texto_livre(self):
        with self.assertRaises(DomainValidationError):
            self.manager.select('status', where='1=1 OR 1=1')

    def test_rejeita_injection_em_order_by(self):
        with self.assertRaises(DomainValidationError):
            self.manager.select('status', order_by='id; DROP TABLE status')


if __name__ == '__main__':
    unittest.main()
