# Zenvix Connect

Sistema de marketplace de serviços desenvolvido em Python, Flask, SQLite e Flask-SocketIO.

## Como executar

### 1. Criar ambiente virtual
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Iniciar a aplicação
```bash
python app.py
```

O modo padrão é desenvolvimento (`APP_ENV=development`): usa o SQLite local,
desativa o cache dos arquivos estáticos e habilita a recarga automática dos
templates. Ele não conecta ao PostgreSQL mesmo que `DATABASE_URL` esteja definido.
Para usar PostgreSQL localmente, defina `DATABASE_BACKEND=postgres` e configure
`DATABASE_URL`.

O Docker define `APP_ENV=production`, preservando o backend de produção quando
`DATABASE_URL` estiver configurado. No VS Code, o perfil de execução usa o modo
de desenvolvimento e não reinstala dependências a cada inicialização.

A aplicação ficará disponível em:
```text
http://127.0.0.1:5000/
```

## Estrutura principal

- app.py: aplicação Flask, rotas, autenticação, dashboards e chat.
- templates/: páginas HTML do sistema.
- static/: arquivos CSS, JavaScript e uploads.
- database.db: banco de dados SQLite do projeto.

## Observações

- O projeto foi organizado sem alterar rotas, templates principais, dashboards, autenticação ou o funcionamento do chat.
- Para apresentação do TCC, o foco foi remover apenas artefatos de apoio e cache sem impactar a execução.
