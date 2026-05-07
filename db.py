import os
import re
import urllib.parse
from contextlib import contextmanager
from enum import Enum

from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker


class ConstraintProduto(Enum):
    POSICAO_CADARCO = 'CK__produto__posicao__17C286CF'
    ACABAMENTO = 'CK__produto__acabame__1A9EF37A'
    UNIDADE = 'CK__produto__unidade__1C873BEC'


class ConstraintUsuario(Enum):
    NIVEL_ACESSO = 'CK__usuario__nivel_a__5F7E2DAC'
    SEXO = 'CK__usuario__sexo__625A9A57'


_REQUIRED_ENV_VARS = (
    'DB_SERVER',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
)

_IDENTIFIER_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


class DatabaseConfigError(ValueError):
    """Erro de configuração de ambiente para conexão com banco."""


class DomainValidationError(ValueError):
    """Erro de domínio para entradas inválidas que devem retornar 4xx."""



def _require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if value is None or not value.strip():
        raise DatabaseConfigError(
            f"Variável de ambiente obrigatória ausente ou vazia: {var_name}. "
            "Configure o ambiente antes de iniciar a aplicação."
        )
    return value.strip()


def build_sqlserver_dsn() -> str:
    """Monta o DSN ODBC para conexão com SQL Server a partir do ambiente."""
    missing = [var for var in _REQUIRED_ENV_VARS if not os.getenv(var) or not os.getenv(var).strip()]
    if missing:
        missing_list = ', '.join(missing)
        raise DatabaseConfigError(
            f"Configuração de banco incompleta. Variáveis obrigatórias ausentes: {missing_list}."
        )

    driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server').strip()
    encrypt = os.getenv('DB_ENCRYPT', 'yes').strip()
    trust_cert = os.getenv('DB_TRUST_CERT', 'no').strip()

    server = _require_env('DB_SERVER')
    database = _require_env('DB_NAME')
    user = _require_env('DB_USER')
    password = _require_env('DB_PASSWORD')

    dsn = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        f"Encrypt={encrypt};"
        f"TrustServerCertificate={trust_cert};"
        "Connection Timeout=30;"
    )
    return dsn


class ConexaoDB:
    def __init__(self):
        dsn = build_sqlserver_dsn()
        self.engine = create_engine(
            'mssql+pyodbc:///?odbc_connect=' + urllib.parse.quote_plus(dsn),
            pool_size=20,
            max_overflow=0,
        )
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    @contextmanager
    def conexao(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


class DatabaseManager:

    def __init__(self, conex=None):
        self.conex = conex if conex else ConexaoDB()
        self.allowed_tables = {'status'}
        self.allowed_columns = {'id', 'status'}
        self.allowed_order_by = {'id', 'status'}

    def _validate_identifier(self, identifier: str, whitelist: set[str], kind: str) -> str:
        if not isinstance(identifier, str) or not _IDENTIFIER_PATTERN.match(identifier):
            raise DomainValidationError(f'Identificador inválido para {kind}: {identifier!r}')
        if identifier not in whitelist:
            raise DomainValidationError(f'Identificador não permitido para {kind}: {identifier}')
        return identifier

    def _validate_identifiers(self, identifiers, whitelist: set[str], kind: str):
        return [self._validate_identifier(item, whitelist, kind) for item in identifiers]

    def execute(self, sql, params=None):
        with self.conex.conexao() as session:
            try:
                if params:
                    result = session.execute(text(sql), params)
                else:
                    result = session.execute(text(sql))
                session.commit()
                return result.rowcount
            except Exception as err:
                session.rollback()
                raise Exception(f"Erro ao executar SQL: {err}")

    def insert(self, table, column_values):
        table = self._validate_identifier(table, self.allowed_tables, 'table')
        columns = self._validate_identifiers(column_values.keys(), self.allowed_columns, 'column')
        values = ', '.join(':' + key for key in column_values.keys())
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({values})"
        return self.execute(sql, column_values)

    def update(self, table, iD, column_values, nome_coluna_primary_key: str = 'id'):
        table = self._validate_identifier(table, self.allowed_tables, 'table')
        self._validate_identifier(nome_coluna_primary_key, self.allowed_columns, 'primary_key')
        self._validate_identifiers(column_values.keys(), self.allowed_columns, 'column')
        columns_values_str = ', '.join(f"{column}=:{column}" for column in column_values.keys())
        sql = f"UPDATE {table} SET {columns_values_str} WHERE {nome_coluna_primary_key}=:id"
        params = dict(column_values)
        params['id'] = iD
        return self.execute(sql, params)

    def select(self, table, columns=None, order_by='', filters=None, where=''):
        if where:
            raise DomainValidationError('Uso de where em texto livre não é permitido. Utilize filtros estruturados.')

        table = self._validate_identifier(table, self.allowed_tables, 'table')
        columns = columns if columns else ['id', 'status']
        validated_columns = self._validate_identifiers(columns, self.allowed_columns, 'column')

        where_clause = ''
        params = {}
        if filters:
            filter_columns = self._validate_identifiers(filters.keys(), self.allowed_columns, 'filter_column')
            where_clause = ' WHERE ' + ' AND '.join(f'{column} = :{column}' for column in filter_columns)
            params = {column: filters[column] for column in filter_columns}

        order_clause = ''
        if order_by:
            order_column = self._validate_identifier(order_by, self.allowed_order_by, 'order_by')
            order_clause = f' ORDER BY {order_column}'

        sql = f"SELECT {', '.join(validated_columns)} FROM {table}{where_clause}{order_clause}"
        sql = ' '.join(sql.split())

        with self.conex.conexao() as session:
            try:
                result_proxy = session.execute(text(sql), params)
                result = result_proxy.fetchall()
                column_names = result_proxy.keys()
                return [dict(zip(column_names, row)) for row in result]
            except Exception as err:
                raise Exception(f"Erro ao executar SQL: {err}")

    def delete(self, table, iD):
        table = self._validate_identifier(table, self.allowed_tables, 'table')
        sql = f"UPDATE {table} SET status = :status WHERE id = :id"
        return self.execute(sql, {'status': 4, 'id': iD})

    def sql_general_internal(self, consulta_sql: str, params=None):
        consulta_sql = ' '.join(consulta_sql.split())

        with self.conex.conexao() as session:
            try:
                result_proxy = session.execute(text(consulta_sql), params)
                result = result_proxy.fetchall()
                return [dict(zip(result_proxy.keys(), row)) for row in result]
            except Exception as err:
                raise Exception(f"Erro ao executar SQL: {err}")

    def sql_general(self, *_args, **_kwargs):
        raise DomainValidationError('sql_general não pode ser exposto a input externo. Use APIs específicas e seguras.')

    def join_internal(self, tables, ons, columns=None, where='', order_by=''):
        columns = ', '.join(columns) if columns else '*'
        joins = ' '.join(f'INNER JOIN {table} ON {on}' for table, on in zip(tables[1:], ons))
        if where:
            where = ' WHERE {} '.format(where)
        order_by = f' ORDER BY {order_by}' if order_by else ''
        sql = f"SELECT {columns} FROM {tables[0]} {joins}{where}{order_by}"
        sql = ' '.join(sql.split())

        with self.conex.conexao() as session:
            try:
                result_proxy = session.execute(text(sql))
                result = result_proxy.fetchall()
                return [dict(zip(result_proxy.keys(), row)) for row in result]
            except Exception as err:
                raise Exception(f"Erro ao executar SQL: {err}")

    def join(self, *_args, **_kwargs):
        raise DomainValidationError('join não pode ser exposto a input externo sem contrato estruturado.')

    def enum_internal(self, table, constraint_name):
        sql = "SELECT definition FROM sys.check_constraints " \
              f"WHERE parent_object_id = OBJECT_ID('{table}') AND name = '{constraint_name}'"

        with self.conex.conexao() as session:
            try:
                result = session.execute(text(sql)).scalar()
                if result is not None:
                    result = result.strip("()\"")
                    values = result.split('OR')
                    values = [value.split('=')[1].strip(" '") for value in values]
                    return values
                return None
            except Exception as err:
                raise Exception(f"Erro ao executar SQL: {err}")

    def enum(self, *_args, **_kwargs):
        raise DomainValidationError('enum não pode ser exposto a input externo sem whitelist explícita.')
