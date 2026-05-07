from contextlib import contextmanager

import pytest

from db import DatabaseManager, DomainValidationError


class _CaptureSession:
    def __init__(self):
        self.last_sql = None
        self.last_params = None

    def execute(self, sql, params=None):
        self.last_sql = str(sql)
        self.last_params = params

        class _Result:
            def fetchall(self):
                return []

            def keys(self):
                return ['id', 'status']

        return _Result()

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


class _CaptureConexao:
    def __init__(self):
        self.session = _CaptureSession()

    @contextmanager
    def conexao(self):
        yield self.session


def test_insert_monta_sql_parametrizado():
    manager = DatabaseManager(conex=object())
    calls = {}

    def _fake_execute(sql, params=None):
        calls['sql'] = sql
        calls['params'] = params
        return 1

    manager.execute = _fake_execute

    rows = manager.insert('status', {'id': 1, 'status': 'ATIVO'})

    assert rows == 1
    assert calls['sql'] == 'INSERT INTO status (id, status) VALUES (:id, :status)'
    assert calls['params'] == {'id': 1, 'status': 'ATIVO'}


def test_update_monta_sql_parametrizado_com_id_no_where():
    manager = DatabaseManager(conex=object())
    calls = {}

    def _fake_execute(sql, params=None):
        calls['sql'] = sql
        calls['params'] = params
        return 1

    manager.execute = _fake_execute

    rows = manager.update('status', 9, {'status': 'INATIVO'})

    assert rows == 1
    assert calls['sql'] == 'UPDATE status SET status=:status WHERE id=:id'
    assert calls['params'] == {'status': 'INATIVO', 'id': 9}


def test_select_monta_sql_com_filtro_e_order_by():
    conex = _CaptureConexao()
    manager = DatabaseManager(conex=conex)

    manager.select('status', columns=['id', 'status'], filters={'status': 'ATIVO'}, order_by='id')

    assert conex.session.last_sql == 'SELECT id, status FROM status WHERE status = :status ORDER BY id'
    assert conex.session.last_params == {'status': 'ATIVO'}


def test_select_rejeita_where_livre():
    manager = DatabaseManager(conex=object())
    with pytest.raises(DomainValidationError):
        manager.select('status', where='1=1')
