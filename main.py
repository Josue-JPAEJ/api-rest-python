import os
import uuid
import logging
from flask import Flask, jsonify, request, g
from functools import wraps
from flask_socketio import SocketIO
from pythonjsonlogger import jsonlogger

from db import ConexaoDB, DatabaseManager, DomainValidationError
import validacao as validar


class ValidationError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = 'VALIDATION_ERROR'):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


ROLE_STATUS_READ = 'status_reader'
ROLE_STATUS_WRITE = 'status_editor'


def validate_status_payload(payload, *, require_id=False, resource_id=None):
    if require_id:
        if not isinstance(resource_id, int) or resource_id <= 0:
            raise ValidationError('ID deve ser um inteiro positivo.', 400, 'BAD_REQUEST')

    if request.mimetype != 'application/json':
        raise ValidationError('Content-Type deve ser application/json.', 400, 'BAD_REQUEST')

    if payload is None:
        raise ValidationError('Payload JSON inválido.', 400, 'BAD_REQUEST')

    if not isinstance(payload, dict):
        raise ValidationError('Payload deve ser um objeto JSON.', 400, 'BAD_REQUEST')

    if 'status' not in payload:
        raise ValidationError('Campo status é obrigatório.', 400, 'BAD_REQUEST')

    status = payload['status']
    if status is None:
        raise ValidationError('Campo status não pode ser nulo.', 422, 'UNPROCESSABLE_ENTITY')

    if not isinstance(status, str):
        raise ValidationError('Campo status deve ser string.', 422, 'UNPROCESSABLE_ENTITY')

    status = status.strip()
    if not status:
        raise ValidationError('Campo status não pode ser vazio.', 422, 'UNPROCESSABLE_ENTITY')

    if not validar.somente_letras(status):
        raise ValidationError('Status deve conter somente letras.', 422, 'UNPROCESSABLE_ENTITY')

    return status.upper()


def _extract_identity_from_headers():
    user_id = request.headers.get('X-User-Id')
    role = request.headers.get('X-User-Role')
    return user_id, role


def require_roles(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            user_id, role = _extract_identity_from_headers()

            if not user_id:
                raise ValidationError('Usuário não autenticado.', 401, 'UNAUTHORIZED')

            g.user_id = user_id
            g.user_role = role

            if role not in allowed_roles:
                logging.warning(
                    'Authorization denied',
                    extra={
                        'request_id': g.get('request_id'),
                        'user_id': user_id,
                        'action': request.endpoint,
                        'required_roles': list(allowed_roles),
                        'provided_role': role,
                    },
                )
                raise ValidationError('Usuário sem permissão para esta ação.', 403, 'FORBIDDEN')

            return view_func(*args, **kwargs)

        return wrapped

    return decorator

# Configurar o logging
handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter())
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)

app = Flask(__name__)
socketio = SocketIO(app, path='/jlt-websocket/')
db = ConexaoDB()
manager = DatabaseManager(db)


@app.before_request
def assign_request_id():
    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))


@app.errorhandler(ValidationError)
def handle_validation_error(err: ValidationError):
    payload = {
        'message': err.message,
        'code': err.code,
        'request_id': g.get('request_id'),
    }
    return jsonify(payload), err.status_code




@app.errorhandler(DomainValidationError)
def handle_domain_validation_error(err: DomainValidationError):
    payload = {
        'message': str(err),
        'code': 'UNPROCESSABLE_ENTITY',
        'request_id': g.get('request_id'),
    }
    return jsonify(payload), 422


@app.errorhandler(Exception)
def handle_unexpected_error(err: Exception):
    logging.exception(
        'Unhandled exception',
        extra={'request_id': g.get('request_id'), 'path': request.path, 'method': request.method},
    )
    payload = {
        'message': 'Erro interno do servidor',
        'code': 'INTERNAL_SERVER_ERROR',
        'request_id': g.get('request_id'),
    }
    return jsonify(payload), 500


@app.route('/status', methods=['GET'])
@require_roles(ROLE_STATUS_READ, ROLE_STATUS_WRITE)
def get_status():
    logging.info('GET /status called', extra={'request_id': g.get('request_id')})
    status = manager.select('status')
    logging.info('Status retrieved successfully', extra={'request_id': g.get('request_id'), 'user_id': g.get('user_id'), 'action': 'read_status'})
    return jsonify({'status': status})


@app.route('/status', methods=['POST'])
@require_roles(ROLE_STATUS_WRITE)
def create_status():
    logging.info('POST /status called', extra={'request_id': g.get('request_id')})
    data = request.get_json(silent=True)
    status = validate_status_payload(data)

    if manager.insert('status', {'status': status}) != 1:
        raise ValidationError('Conflito ao criar status.', 409, 'CONFLICT')
    socketio.emit('status update', {'message': 'Status criado com sucesso'}, broadcast=True)
    logging.info('Status created successfully', extra={'request_id': g.get('request_id'), 'user_id': g.get('user_id'), 'action': 'create_status'})
    return jsonify({'message': 'Status criado com sucesso'}), 201




@app.route('/status/<int:id>', methods=['DELETE'])
@require_roles(ROLE_STATUS_WRITE)
def delete_status(id):
    logging.info(f'DELETE /status/{id} called', extra={'request_id': g.get('request_id')})

    if id <= 0:
        raise ValidationError('ID deve ser um inteiro positivo.', 400, 'BAD_REQUEST')

    rows_affected = manager.delete('status', id)
    if rows_affected != 1:
        raise ValidationError('Status não encontrado para o ID informado.', 404, 'NOT_FOUND')

    socketio.emit('status update', {'message': 'Status removido com sucesso'}, broadcast=True)
    logging.info('Status deleted successfully', extra={'request_id': g.get('request_id'), 'user_id': g.get('user_id'), 'action': 'delete_status'})
    return jsonify({'message': 'Status removido com sucesso'})
@app.route('/status/<int:id>', methods=['PUT'])
@require_roles(ROLE_STATUS_WRITE)
def update_status(id):
    logging.info(f'PUT /status/{id} called', extra={'request_id': g.get('request_id')})
    data = request.get_json(silent=True)
    status = validate_status_payload(data, require_id=True, resource_id=id)

    column_values = {'status': status}
    rows_affected = manager.update('status', id, column_values)
    if rows_affected != 1:
        raise ValidationError('Status não encontrado para o ID informado.', 404, 'NOT_FOUND')
    socketio.emit('status update', {'message': 'Status atualizado com sucesso'}, broadcast=True)
    logging.info('Status updated successfully', extra={'request_id': g.get('request_id'), 'user_id': g.get('user_id'), 'action': 'update_status'})
    return jsonify({'message': 'Status atualizado com sucesso'})


if __name__ == '__main__':
    socketio.run(app, debug=True)
