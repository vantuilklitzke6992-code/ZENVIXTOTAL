# Zenvix Connect

Sistema inicial do marketplace de serviços usando Python, Flask e SQLite.

## Como executar

### Usando o VS Code
1. Abra a pasta `ZenvixConnect` no VS Code.
2. Pressione `F5` ou vá em Run and Debug.
3. O servidor Flask será iniciado automaticamente e o navegador será aberto em `http://127.0.0.1:5000/`.

### Usando o terminal
1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute o aplicativo:
   ```bash
   python app.py
   ```
3. Abra no navegador:
   ```
   http://127.0.0.1:5000/
   ```

## O que foi criado

- `app.py`: configuração do Flask, criação automática do banco SQLite e rota inicial.
- `templates/index.html`: página inicial exibida pelo Flask.
- `templates/base.html`: estrutura de layout compartilhada.
- `static/css/style.css`: estilo básico para o tema do projeto.
- `static/js/main.js`: arquivo JavaScript vazio para futuras interações.
- `database.db`: gerado automaticamente na primeira execução.
