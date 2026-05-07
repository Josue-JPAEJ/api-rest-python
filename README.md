# API REST - Python

Projeto de API REST desenvolvido em Python para estudos de backend, validação de dados e integração com banco de dados.

## Tecnologias

- Python
- SQL Server (via SQLAlchemy + pyodbc)
- REST API

## Estrutura

- `main.py` -> inicialização da API
- `db.py` -> conexão com banco
- `validacao.py` -> validações

## Configuração de Ambiente

A conexão com banco usa variáveis de ambiente. Antes de executar a aplicação, configure:

- `DB_SERVER` (obrigatória)
- `DB_NAME` (obrigatória)
- `DB_USER` (obrigatória)
- `DB_PASSWORD` (obrigatória)
- `DB_DRIVER` (opcional, padrão: `ODBC Driver 17 for SQL Server`)
- `DB_ENCRYPT` (opcional, padrão: `yes`)
- `DB_TRUST_CERT` (opcional, padrão: `no`)

Se qualquer variável obrigatória estiver ausente, a aplicação falhará no boot com mensagem operacional clara.

Exemplo de arquivo `.env.example` (sem segredo real):

```env
DB_SERVER=tcp:seu-servidor.database.windows.net,1433
DB_NAME=seu_banco
DB_USER=seu_usuario
DB_PASSWORD=troque-esta-senha
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_ENCRYPT=yes
DB_TRUST_CERT=no
```

## Objetivo

Praticar:

- desenvolvimento backend
- APIs REST
- persistência de dados
- validações
- organização de projeto
