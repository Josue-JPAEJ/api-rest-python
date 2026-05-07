import os
import uuid
import logging
from flask import Flask, jsonify, request, g
from flask_socketio import SocketIO
from pythonjsonlogger import jsonlogger

from db import ConexaoDB, DatabaseManager
import validacao as validar


class ValidationError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = 'VALIDATION_ERROR'):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


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
def get_status():
    logging.info('GET /status called', extra={'request_id': g.get('request_id')})
    status = manager.select('status')
    logging.info('Status retrieved successfully', extra={'request_id': g.get('request_id')})
    return jsonify({'status': status})


@app.route('/status', methods=['POST'])
def create_status():
    logging.info('POST /status called', extra={'request_id': g.get('request_id')})
    data = request.get_json(silent=True)
    status = (data or {}).get('status')

    if not status:
        raise ValidationError('Campo status é obrigatório.', 400, 'BAD_REQUEST')
    if not validar.somente_letras(status):
        raise ValidationError('Status deve conter somente letras.', 422, 'UNPROCESSABLE_ENTITY')

    manager.insert('status', {'status': str(status).strip().upper()})
    socketio.emit('status update', {'message': 'Status criado com sucesso'}, broadcast=True)
    logging.info('Status created successfully', extra={'request_id': g.get('request_id')})
    return jsonify({'message': 'Status criado com sucesso'}), 201




@app.route('/status/<int:id>', methods=['DELETE'])
def delete_status(id):
    logging.info(f'DELETE /status/{id} called', extra={'request_id': g.get('request_id')})

    if id <= 0:
        raise ValidationError('ID deve ser um inteiro positivo.', 400, 'BAD_REQUEST')

    rows_affected = manager.delete('status', id)
    if rows_affected != 1:
        raise ValidationError('Status não encontrado para o ID informado.', 404, 'NOT_FOUND')

    socketio.emit('status update', {'message': 'Status removido com sucesso'}, broadcast=True)
    logging.info('Status deleted successfully', extra={'request_id': g.get('request_id')})
    return jsonify({'message': 'Status removido com sucesso'})
@app.route('/status/<int:id>', methods=['PUT'])
def update_status(id):
    logging.info(f'PUT /status/{id} called', extra={'request_id': g.get('request_id')})
    data = request.get_json(silent=True)
    status = (data or {}).get('status')

    if id <= 0:
        raise ValidationError('ID deve ser um inteiro positivo.', 400, 'BAD_REQUEST')
    if not status:
        raise ValidationError('Campo status é obrigatório.', 400, 'BAD_REQUEST')
    if not validar.somente_letras(status):
        raise ValidationError('Status deve conter somente letras.', 422, 'UNPROCESSABLE_ENTITY')

    column_values = {'status': str(status).strip().upper()}
    manager.update('status', id, column_values)
    socketio.emit('status update', {'message': 'Status atualizado com sucesso'}, broadcast=True)
    logging.info('Status updated successfully', extra={'request_id': g.get('request_id')})
    return jsonify({'message': 'Status atualizado com sucesso'})


if __name__ == '__main__':
    socketio.run(app, debug=True)
