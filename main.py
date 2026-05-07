import traceback
import os
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from db import ConexaoDB, DatabaseManager
import validacao as validar
import logging
from pythonjsonlogger import jsonlogger

# Configurar o logging
handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter())
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)

app = Flask(__name__)
socketio = SocketIO(app, path='/jlt-websocket/')
db = ConexaoDB()
manager = DatabaseManager(db)


@app.route('/status', methods=['GET'])
def get_status():
    logging.info('GET /status called')
    try:
        status = manager.select('status')
        logging.info('Status retrieved successfully')
        return jsonify({'status': status})
    except Exception as e:
        tb = traceback.format_exc()
        logging.error(f'Error getting status: {e}, traceback: {tb}')
        return jsonify({'error': str(e), 'traceback': tb}), 500


@app.route('/status', methods=['POST'])
def create_status():
    logging.info('POST /status called')
    try:
        data = request.get_json()
        if validar.somente_letras(data['status']):
            manager.insert('status', {'status': str(data['status']).strip().upper()})
            socketio.emit('status update', {'message': 'Status criado com sucesso'}, broadcast=True)
            logging.info('Status created successfully')
            return jsonify({'message': 'Status criado com sucesso'}), 201
        else:
            logging.warning('Invalid status')
            return jsonify({'error: Status deve conter somente letras.'}), 500
    except Exception as e:
        tb = traceback.format_exc()
        logging.error(f'Error creating status: {e}, traceback: {tb}')
        return jsonify({'error': str(e), 'traceback': tb, 'data': str(data)}), 500


@app.route('/status/<int:id>', methods=['PUT'])
def update_status(id):  # Adicione 'id' aqui
    logging.info(f'PUT /status/{id} called')
    try:
        data = request.get_json()
        if id > 0 and validar.somente_letras(data['status']):
            column_values = {'status': str(data['status']).strip().upper()}
            manager.update('status', id, column_values)
            socketio.emit('status update', {'message': 'Status atualizado com sucesso'}, broadcast=True)
            logging.info('Status updated successfully')
            return jsonify({'message': 'Status atualizado com sucesso'})
        else:
            logging.warning('Invalid status or ID')
            return jsonify({'error: Atenção: Status deve conter somente letras. O ID deve ser um ID válido.'}), 500
    except Exception as e:
        tb = traceback.format_exc()
        logging.error(f'Error updating status: {e}, traceback: {tb}')
        return jsonify({'error ID ': str(id), 'exception': str(e), 'traceback': tb, 'data': str(data)}), 500


if __name__ == '__main__':
    # socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8002)), debug=True)
    socketio.run(app, debug=True)
