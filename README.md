# API REST - Python

Projeto de API REST em Flask para gestão de `status`, com autenticação/autorização via headers, persistência em **SQL Server** (via **SQLAlchemy + pyodbc**) e notificação em tempo real com **Socket.IO**.

## Resumo arquitetural

- **Entrada HTTP**: `main.py` (rotas, validação de payload, autenticação/autorização e tratamento de erro).
- **Persistência**: `db.py` (montagem de DSN ODBC, engine SQLAlchemy e operações de banco encapsuladas em `DatabaseManager`).
- **Regra de validação de domínio**: `validacao.py` + validações de contrato no `main.py`.
- **Tempo real**: `Flask-SocketIO` no path `/jlt-websocket/`.

## Stack e dependências de execução

### Python packages (runtime)

Dependências atualmente declaradas no projeto:

- `Flask==2.0.3`
- `Flask-SocketIO==4.3.1`
- `python-socketio==4.6.0`
- `python-engineio==3.13.2`
- `SQLAlchemy==2.0.23`
- `pyodbc==5.0.1`
- `python-json-logger==2.0.7`
- `gevent==23.9.1`
- `eventlet==0.33.3`
- `gevent-websocket==0.10.1`
- `mysql-connector-python==8.2.0` (presente no `requirements.txt`, **não utilizado** pelo fluxo atual de SQL Server)

> Observação: o código de conexão ativo usa `mssql+pyodbc` com DSN ODBC para SQL Server.

### Dependência de sistema (obrigatória)

Para `pyodbc` funcionar, é necessário instalar um driver ODBC para SQL Server no host:

- Exemplo usado por padrão na aplicação: `ODBC Driver 17 for SQL Server`.
- Alternativa comum: `ODBC Driver 18 for SQL Server` (ajustando `DB_DRIVER`).

Sem driver instalado, a aplicação não conseguirá abrir conexão com o banco.

## Configuração de ambiente

A aplicação falha no boot se variáveis obrigatórias estiverem ausentes.

### Variáveis obrigatórias

- `DB_SERVER` (ex.: `tcp:seu-servidor.database.windows.net,1433`)
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

### Variáveis opcionais

- `DB_DRIVER` (default: `ODBC Driver 17 for SQL Server`)
- `DB_ENCRYPT` (default: `yes`)
- `DB_TRUST_CERT` (default: `no`)

### Exemplo `.env`

```env
DB_SERVER=tcp:seu-servidor.database.windows.net,1433
DB_NAME=seu_banco
DB_USER=seu_usuario
DB_PASSWORD=troque-esta-senha
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_ENCRYPT=yes
DB_TRUST_CERT=no
```

## Rede, porta e Socket.IO

- A inicialização padrão é `socketio.run(app, debug=True)`.
- **Porta HTTP**: por padrão, Flask/SocketIO sobe em `5000` quando não informada outra porta.
- **Endpoint WebSocket/Socket.IO**: `path='/jlt-websocket/'`.
  - Exemplo de URL base local: `http://localhost:5000`
  - Exemplo de path Socket.IO: `http://localhost:5000/jlt-websocket/`

## Guia rápido: subir localmente

1. Criar ambiente virtual e instalar dependências:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Garantir driver ODBC do SQL Server instalado no sistema operacional.
3. Exportar variáveis de ambiente (`DB_*`) conforme seção anterior.
4. Subir a API:
   ```bash
   python main.py
   ```
5. Testar endpoint de leitura:
   ```bash
   curl -i http://localhost:5000/status \
     -H 'X-User-Id: u-1' \
     -H 'X-User-Role: status_reader'
   ```

## Contrato da API

### Headers de autenticação/autorização

As rotas exigem:

- `X-User-Id`: identifica usuário autenticado.
- `X-User-Role`: perfil de acesso.
  - `status_reader`: pode ler.
  - `status_editor`: pode ler e escrever.

### Endpoints

#### `GET /status`
- **Permissão**: `status_reader` ou `status_editor`
- **200 OK**
  ```json
  {
    "status": [
      {"id": 1, "status": "ATIVO"}
    ]
  }
  ```

#### `POST /status`
- **Permissão**: `status_editor`
- **Content-Type obrigatório**: `application/json`
- **Payload**:
  ```json
  { "status": "ATIVO" }
  ```
- **Regras de validação**:
  - campo obrigatório
  - não nulo
  - string não vazia
  - somente letras
- **201 Created**
  ```json
  { "message": "Status criado com sucesso" }
  ```
- **409 Conflict** (quando insert não afeta 1 linha)

#### `PUT /status/<id>`
- **Permissão**: `status_editor`
- **Content-Type obrigatório**: `application/json`
- **Payload**:
  ```json
  { "status": "INATIVO" }
  ```
- **200 OK**
  ```json
  { "message": "Status atualizado com sucesso" }
  ```
- **404 Not Found** (id não encontrado)

#### `DELETE /status/<id>`
- **Permissão**: `status_editor`
- **200 OK**
  ```json
  { "message": "Status removido com sucesso" }
  ```
- **404 Not Found** (id não encontrado)

## Modelo de erro (padrão)

Erros retornam JSON padronizado:

```json
{
  "message": "descrição legível",
  "code": "CODIGO_ESTAVEL",
  "request_id": "uuid-ou-header"
}
```

### Códigos HTTP realmente usados

- **400 Bad Request**
  - `Content-Type` inválido.
  - JSON inválido ou `payload` não objeto.
  - campo `status` ausente.
  - ID inválido em cenários validados.
- **401 Unauthorized**
  - ausência de `X-User-Id`.
- **403 Forbidden**
  - `X-User-Role` sem permissão para a ação.
- **404 Not Found**
  - atualização/remoção sem linha afetada (recurso inexistente).
- **409 Conflict**
  - criação sem linha afetada.
- **422 Unprocessable Entity**
  - violações de regra de domínio (ex.: `status` nulo, não string, vazio, caracteres inválidos).
- **500 Internal Server Error**
  - falha inesperada não mapeada.

## Troubleshooting de conexão (SQL Server/ODBC)

### 1) Erro de variável obrigatória ausente

**Sintoma**: falha de boot com mensagem de configuração incompleta.

**Verificar**:
- se `DB_SERVER`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` estão definidos e não vazios.

### 2) Driver ODBC não encontrado

**Sintoma**: erro de conexão do `pyodbc` informando driver inexistente.

**Verificar**:
- instalação do driver no SO.
- valor de `DB_DRIVER` igual ao nome real do driver instalado.

### 3) Falha de TLS/certificado

**Sintoma**: erro de handshake/SSL ao conectar.

**Verificar**:
- `DB_ENCRYPT` (default `yes`).
- `DB_TRUST_CERT` (default `no`).
- política de certificado do ambiente (dev vs produção).

### 4) Timeout de conexão

**Sintoma**: conexão expira.

**Verificar**:
- reachability de rede para `DB_SERVER` e porta do SQL Server.
- firewall, regras de rede, allowlist de IP, VPN.

### 5) Erro de autenticação no banco

**Sintoma**: login failed.

**Verificar**:
- usuário/senha (`DB_USER`, `DB_PASSWORD`).
- permissões do usuário no `DB_NAME`.

## Estrutura do projeto

- `main.py` → inicialização da API e contrato HTTP.
- `db.py` → conexão SQL Server e operações de dados.
- `validacao.py` → validações de domínio auxiliares.
- `tests/` → suíte de testes unitários/API.

## Testes automatizados (pytest)

Estrutura de testes em `tests/` com foco em:
- validações puras (`validacao.py`),
- builders e validações de SQL (`db.py`),
- API `/status` (GET/POST/PUT com cenários felizes e inválidos),
- evento Socket.IO (`status update`).

### Execução local

```bash
pytest -q
```

### CI (GitHub Actions)

Pipeline em `.github/workflows/tests.yml` executa automaticamente em `push` e `pull_request`:
1. checkout do repositório,
2. setup do Python 3.11,
3. instalação de dependências,
4. execução de `pytest -q`.
