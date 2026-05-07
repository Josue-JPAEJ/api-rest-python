import importlib
import sys
from unittest.mock import patch

import pytest


@pytest.fixture()
def app_module():
    with patch('db.ConexaoDB.__init__', return_value=None):
        if 'main' in sys.modules:
            module = importlib.reload(sys.modules['main'])
        else:
            module = importlib.import_module('main')
    return module


@pytest.fixture()
def client(app_module):
    return app_module.app.test_client()


@pytest.fixture()
def auth_reader_headers():
    return {'X-User-Id': 'u-reader', 'X-User-Role': 'status_reader'}


@pytest.fixture()
def auth_editor_headers():
    return {'X-User-Id': 'u-editor', 'X-User-Role': 'status_editor'}
