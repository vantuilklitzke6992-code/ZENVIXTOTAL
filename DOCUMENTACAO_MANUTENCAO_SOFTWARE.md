# DOCUMENTAÇÃO DE MANUTENÇÃO DE SOFTWARE — ZENVIX CONNECT

## 1. Introdução

Este documento descreve manutenções identificadas no código atual e no histórico da branch `limpeza-tcc` do Zenvix Connect. As auditorias existentes foram consideradas registros auxiliares; quando divergiam da estrutura ou do código atual, prevaleceram as evidências atuais e os commits alcançáveis pela branch analisada.

As categorias adotadas são:

- **Corretiva:** corrige falhas ou comportamentos inadequados já existentes.
- **Adaptativa:** ajusta o sistema a ambientes, dependências ou requisitos externos.
- **Preventiva:** reduz riscos e busca evitar falhas futuras.
- **Perfectiva:** aprimora funcionalidades, organização, interface ou experiência de uso.

## 2. Manutenção Corretiva

### 2.1 Correção dos endpoints após a utilização de Blueprints

**Problema ou necessidade:** Após a organização das rotas em Blueprints, alguns redirecionamentos ainda usavam nomes antigos de endpoints.

**O que foi feito:** Os redirecionamentos foram atualizados para os endpoints registrados nos Blueprints, como `auth.login` e `public.home`.

**Arquivos envolvidos:** `app.py`; `routes/auth.py`.

**Objetivo:** Evitar referências a endpoints incorretos e manter os redirecionamentos compatíveis com a organização atual das rotas.

**Evidência:** Commit `7cb31c9`; redirecionamentos atuais com `url_for("auth.login")` e `url_for("public.home")`.

**Tipo de manutenção:** Corretiva

### 2.2 Correção do fluxo de login e cadastro com PRG

**Problema ou necessidade:** Respostas renderizadas diretamente após POST podiam tornar o fluxo de formulários menos consistente e não preservar adequadamente a etapa do cadastro.

**O que foi feito:** Foi aplicado Post/Redirect/Get. O cadastro guarda temporariamente os dados e a etapa na sessão e redireciona para a rota de cadastro; o login redireciona após erros.

**Arquivos envolvidos:** `routes/auth.py`.

**Objetivo:** Tornar o tratamento de erros de login e cadastro mais consistente e recuperar o estado do formulário após o redirecionamento.

**Evidência:** Commit `272b384`; função `_registration_error_redirect()` e recuperação dos dados de cadastro da sessão.

**Tipo de manutenção:** Corretiva

### 2.3 Correção da validação de uploads

**Problema ou necessidade:** A lista de formatos de documentos também era usada para fotos de perfil e logos, permitindo extensões que não eram apropriadas para imagens.

**O que foi feito:** Foi criado um validador específico de imagens, limitado a PNG, JPG e JPEG, e ele passou a ser usado para fotos e logos.

**Arquivos envolvidos:** `routes/auth.py`.

**Objetivo:** Restringir os formatos aceitos para imagens de perfil e logos aos formatos previstos.

**Evidência:** Commit `3f8ac2e`; funções `allowed_image_file()` e `save_uploaded_file()` com validador selecionável.

**Tipo de manutenção:** Corretiva

### 2.4 Correção de sintaxe no CSS

**Problema ou necessidade:** Havia uma chave de fechamento excedente antes de uma regra `@media`.

**O que foi feito:** A chave excedente foi removida.

**Arquivos envolvidos:** `static/css/style.css`.

**Objetivo:** Manter a estrutura das regras CSS corretamente delimitada.

**Evidência:** Commit `3f8ac2e`; diff remove a chave excedente no fim do bloco responsivo.

**Tipo de manutenção:** Corretiva

### 2.5 Reparo de referências de chaves estrangeiras no SQLite

**Problema ou necessidade:** A normalização da tabela `usuarios` podia deixar referências de outras tabelas apontando para a tabela temporária `usuarios_old`.

**O que foi feito:** Foi adicionada uma rotina para localizar essas referências, reconstruir as tabelas envolvidas em transação, copiar os dados e reverter a operação se ocorrer uma falha.

**Arquivos envolvidos:** `utils/db.py`.

**Objetivo:** Reparar referências de chaves estrangeiras após a normalização estrutural da tabela de usuários.

**Evidência:** Commit `d2fd3ea`; função `repair_usuarios_foreign_keys()` e chamada em `init_db()`.

**Tipo de manutenção:** Corretiva

### 2.6 Correção da seleção de prestadores em destaque

**Problema ou necessidade:** A lógica anterior selecionava os primeiros prestadores retornados sem considerar avaliações ou serviços concluídos.

**O que foi feito:** A seleção passou a considerar prestadores com avaliações ou serviços concluídos e ordená-los pela pontuação de recomendação.

**Arquivos envolvidos:** `routes/public.py`.

**Objetivo:** Melhorar os critérios usados para exibir prestadores em destaque na página inicial.

**Evidência:** Commit `cb31728`; filtro por `rating_count` ou `completed_services` e ordenação por `recommendation_score`.

**Tipo de manutenção:** Corretiva

### 2.7 Correção do acesso ao chat de serviço

**Problema ou necessidade:** A regra anterior permitia que administradores ou empresas acessassem um chat de serviço sem serem participantes daquele serviço.

**O que foi feito:** A autorização passou a permitir somente o cliente ou o profissional associados ao serviço. A mesma regra é usada ao solicitar entrada na sala Socket.IO.

**Arquivos envolvidos:** `app.py`; `tests/test_chat_consolidation.py`.

**Objetivo:** Restringir o chat aos participantes do serviço e verificar essa regra por testes.

**Evidência:** Commit `879f474`; função `user_can_access_service_chat()`, handler `handle_join_service()` e testes `test_user_can_access_service_chat_only_for_participants` e `test_service_chat_route_denies_third_party`.

**Tipo de manutenção:** Corretiva

### 2.8 Correção do horário das mensagens

**Problema ou necessidade:** As datas armazenadas em UTC precisavam ser apresentadas no fuso horário de São Paulo.

**O que foi feito:** Foi criado o filtro `brasil_datetime`, que interpreta a data como UTC e converte para `America/Sao_Paulo`; os templates de chat aplicam esse filtro.

**Arquivos envolvidos:** `utils/app_init.py`; `requirements.txt`; `templates/chat.html`; `templates/conversa.html`.

**Objetivo:** Apresentar os horários das mensagens no fuso configurado para o Brasil.

**Evidência:** Commit `879f474`; filtro `format_brasil_datetime()` e dependência `tzdata`.

**Tipo de manutenção:** Corretiva

## 3. Manutenção Adaptativa

### 3.1 Adaptação para execução com Docker

**Problema ou necessidade:** O projeto precisava de uma configuração para construção e execução em contêiner.

**O que foi feito:** O `Dockerfile` define a imagem Python, instalação das dependências, porta exposta e comando de inicialização. O `.dockerignore` define itens ignorados no contexto de build.

**Arquivos envolvidos:** `Dockerfile`; `.dockerignore`.

**Objetivo:** Preparar o projeto para construção e execução em Docker.

**Evidência:** Commits `f8d4fdb` e `e0cc250`; diretivas `FROM`, `RUN`, `EXPOSE` e `CMD`, além das regras de `.dockerignore`.

**Observação:** `.dockerignore` contém `database_*.db`, padrão que não corresponde ao nome `database.db`. Portanto, este documento não afirma que o banco principal esteja excluído do contexto Docker.

**Tipo de manutenção:** Adaptativa

### 3.2 Implementação do processo de CI/CD

**Problema ou necessidade:** O projeto precisava automatizar testes, construção/publicação da imagem Docker e acionamento do deploy.

**O que foi feito:** O workflow instala dependências, executa `pytest`, constrói e publica a imagem e aciona o deploy hook do Render. O job de testes define `SECRET_KEY` no ambiente.

**Arquivos envolvidos:** `.github/workflows/deploy.yml`; `requirements.txt`.

**Objetivo:** Automatizar as etapas de integração e entrega utilizadas pelo projeto.

**Evidência:** Commits `97cbb6e`, `ef45c20` e `e4df0c6`; jobs `test`, `docker` e `deploy`. O gatilho atual é `push` na branch `limpeza-tcc`.

**Tipo de manutenção:** Adaptativa

### 3.3 Adaptação dos dados de localidades

**Problema ou necessidade:** O cadastro precisava disponibilizar estados e municípios brasileiros.

**O que foi feito:** Foi criado um script que consulta a API do IBGE e gera um JSON local. O backend lê esse arquivo e o template/JavaScript o utilizam no preenchimento dos campos.

**Arquivos envolvidos:** `atualizar_localidades.py`; `static/data/brazilian_locations.json`; `routes/auth.py`; `templates/auth/cadastro.html`; `static/js/main.js`.

**Objetivo:** Integrar dados estruturados de localidades ao fluxo de cadastro.

**Evidência:** Commit `df7feae`; `API_BASE` e `OUTPUT_FILE` no script, `get_brazilian_location_data()` no backend e `populateCityOptions()` no JavaScript.

**Tipo de manutenção:** Adaptativa

## 4. Manutenção Preventiva

### 4.1 Validação CSRF e tratamento seguro de mensagens

**Problema ou necessidade:** Reduzir riscos de requisições não autorizadas e de interpretação de mensagens não confiáveis como HTML executável.

**O que foi feito:** Tokens CSRF são gerados e validados nas rotas e formulários correspondentes. No chat, as mensagens dinâmicas são criadas com elementos DOM e inseridas como texto.

**Arquivos envolvidos:** `utils/security.py`; `app.py`; `routes/auth.py`; `static/js/main.js`; `templates/alterar_senha.html`; `templates/auth/cadastro.html`; `templates/auth/login.html`; `templates/avaliar.html`; `templates/chat.html`; `templates/conversa.html`; `templates/dashboard_admin.html`; `templates/dashboard_cliente.html`; `templates/dashboard_empresa.html`; `templates/dashboard_profissional.html`; `templates/excluir_conta.html`; `templates/meus_servicos.html`; `templates/perfil.html`; `templates/solicitar_servico.html`.

**Objetivo:** Validar tokens CSRF nas rotas que implementam essa checagem e reduzir o risco de execução de conteúdo HTML recebido pelo chat.

**Evidência:** Commit `fc7c3c8`; `generate_csrf_token()` usa `secrets.token_urlsafe()` e `validate_csrf_token()` usa `secrets.compare_digest()`; os templates listados contêm `_csrf_token`; `static/js/main.js` usa `createElement()` e `textContent` para mensagens.

**Limite da implementação:** A validação CSRF é chamada pelas rotas correspondentes; não é uma proteção global aplicada automaticamente a todos os formulários e endpoints.

**Tipo de manutenção:** Preventiva

### 4.2 Isolamento dos testes

**Problema ou necessidade:** Evitar que os testes automatizados utilizem diretamente o banco de dados local da aplicação.

**O que foi feito:** A configuração dos testes direciona `DATABASE_PATH` para um banco temporário e remove o diretório ao final da execução. Também configura o caminho do projeto para os imports.

**Arquivos envolvidos:** `tests/conftest.py`; `tests/test_chat_consolidation.py`; `tests/test_registration_ui.py`; `tests/test_service_flow.py`; `.github/workflows/deploy.yml`.

**Objetivo:** Reduzir interferência dos testes nos dados principais e executá-los no processo de CI.

**Evidência:** Commits `eca1954`, `b4d41ed` e `97cbb6e`; configuração com `tempfile`, `DATABASE_PATH`, limpeza ao final e etapa `pytest` no workflow.

**Tipo de manutenção:** Preventiva

### 4.3 Regras para evitar versionamento acidental

**Problema ou necessidade:** Arquivos locais, bancos e uploads não devem ser adicionados acidentalmente ao Git.

**O que foi feito:** O `.gitignore` inclui regras para `.env`, ambiente virtual, bancos e arquivos em `static/uploads`, preservando o `.gitkeep`.

**Arquivos envolvidos:** `.gitignore`.

**Objetivo:** Reduzir o risco de versionar arquivos locais ou dados de upload.

**Evidência:** Commit `022cf7d` e regras atuais do `.gitignore`. O banco `database.db` já rastreado ainda pode aparecer como modificado apesar da regra de ignore.

**Tipo de manutenção:** Preventiva

### 4.4 Escape do valor do logo no template

**Problema ou necessidade:** O nome do arquivo do logo é inserido em um atributo HTML de estilo.

**O que foi feito:** Foi aplicado o filtro de escape `e` ao valor interpolado no template.

**Arquivos envolvidos:** `templates/dashboard_empresa.html`.

**Objetivo:** Escapar explicitamente o valor usado na saída HTML.

**Evidência:** Commit `879f474`; uso de `user['logo_empresa']|e` no atributo `background-image`.

**Tipo de manutenção:** Preventiva

## 5. Manutenção Perfectiva

### 5.1 Melhoria visual do chat

**Problema ou necessidade:** A interface do chat precisava de refinamento visual sem mudança declarada da lógica principal.

**O que foi feito:** Foram acrescentadas regras visuais para cabeçalho, mensagens, janela, formulário e comportamento responsivo do chat.

**Arquivos envolvidos:** `static/css/design-system.css`.

**Objetivo:** Aprimorar a apresentação e manter os estilos do chat integrados ao sistema visual.

**Evidência:** Commit `648a88a`, que adicionou regras CSS ao arquivo; blocos atuais de estilos `.chat-*` e media queries.

**Tipo de manutenção:** Perfectiva

### 5.2 Melhoria visual da página inicial

**Problema ou necessidade:** A página inicial precisava apresentar melhor os serviços e a identidade visual da plataforma.

**O que foi feito:** Foram alterados o conteúdo e os estilos da home e adicionadas imagens para seções da página.

**Arquivos envolvidos:** `templates/public/home.html`; `static/css/public.css`; `static/images/home/cliente-servico.jpg`; `static/images/home/cta-tecnologico.jpg`; `static/images/home/hero.jpg`; `static/images/home/home.jpg`; `static/images/home/profissional.jpg`.

**Objetivo:** Aprimorar a apresentação visual da página inicial.

**Evidência:** Commits `c03c222` e `14e6e65`; alterações de template/CSS e inclusão das imagens listadas.

**Tipo de manutenção:** Perfectiva

### 5.3 Melhoria visual das categorias

**Problema ou necessidade:** Facilitar a identificação dos tipos de serviço apresentados na home.

**O que foi feito:** Foram adicionadas imagens próprias para as categorias e alterados estilos e conteúdo de apresentação.

**Arquivos envolvidos:** `templates/public/home.html`; `static/css/public.css`; `static/images/categorias/ar-condicionado.jpg`; `static/images/categorias/eletricista.jpg`; `static/images/categorias/encanador.jpg`; `static/images/categorias/informatica.jpg`; `static/images/categorias/limpeza.jpg`; `static/images/categorias/manutencao.jpg`; `static/images/categorias/outros.jpg`; `static/images/categorias/pintura.jpg`.

**Objetivo:** Facilitar a identificação visual das categorias de serviço.

**Evidência:** Commits `0b7b024` e `53fba5f`; inclusão das imagens e alterações de estilo da home.

**Tipo de manutenção:** Perfectiva

### 5.4 Melhoria da responsividade

**Problema ou necessidade:** A interface precisava se adaptar a diferentes tamanhos de tela.

**O que foi feito:** Foram ajustados estilos, cabeçalho, home, busca de profissionais e dashboard do cliente.

**Arquivos envolvidos:** `static/css/design-system.css`; `static/css/public.css`; `templates/components/header.html`; `templates/public/home.html`; `templates/dashboard_cliente.html`; `templates/profissionais.html`.

**Objetivo:** Melhorar a adaptação das telas e da navegação a diferentes resoluções.

**Evidência:** Commit `7b0e055`; media queries atuais nos CSS e navegação móvel em `templates/components/header.html`.

**Tipo de manutenção:** Perfectiva

### 5.5 Melhoria do fluxo de cadastro

**Problema ou necessidade:** O preenchimento precisava de uma sequência guiada e de campos de localidade adequados.

**O que foi feito:** O cadastro foi organizado em etapas, com seleção de tipo de conta, dados geográficos e recursos de seleção/visualização de imagens.

**Arquivos envolvidos:** `templates/auth/cadastro.html`; `static/js/main.js`; `static/css/style.css`; `static/data/brazilian_locations.json`; `tests/test_registration_ui.py`; `routes/auth.py`; `templates/components/header.html`; `templates/public/home.html`; `static/css/public.css`; `static/logo_oficial.png`.

**Objetivo:** Organizar e facilitar o fluxo de cadastro e aplicar a identidade visual da plataforma.

**Evidência:** Commit `df7feae`; stepper no template, lógica de formulário em `main.js` e testes de selects em `tests/test_registration_ui.py`.

**Tipo de manutenção:** Perfectiva

### 5.6 Organização arquitetural parcial

**Problema ou necessidade:** A estrutura precisava de separação de responsabilidades para apoiar a manutenção e a evolução do projeto.

**O que foi feito:** Foram introduzidos módulos e pacotes separados para rotas, serviços, banco, inicialização, presença e segurança.

**Arquivos e diretórios envolvidos:** `app.py`; `models/`; `routes/`; `services/`; `socket_handlers/`; `utils/`.

**Objetivo:** Separar parcialmente responsabilidades da aplicação.

**Evidência:** Commit `f8d4fdb` e estrutura atual. A organização é parcial: muitas rotas e regras de negócio continuam em `app.py`; `models/` e `socket_handlers/` possuem somente seus arquivos `__init__.py`. Os módulos históricos `services/chat_service.py` e `services/user_service.py` foram removidos no commit `d2fd3ea` e não fazem parte da estrutura atual.

**Tipo de manutenção:** Perfectiva

### 5.7 Busca e navegação da lista de conversas

**Problema ou necessidade:** A lista anterior apresentava conversas relacionadas a serviços em formato de tabela, dificultando a localização de conversas e contatos.

**O que foi feito:** A navegação foi aprimorada com busca por nome, filtro de conversas não lidas, apresentação da última mensagem e indicadores de presença.

**Arquivos envolvidos:** `app.py`; `templates/chat/index.html`; `static/js/main.js`; `static/css/design-system.css`.

**Objetivo:** Melhorar a localização, a navegação e a visualização das conversas existentes.

**Evidência:** Commit `f8d4fdb`; `get_user_chat_conversations()` aplica busca e filtro de não lidas; o template mostra conversas recentes, última mensagem e presença; o JavaScript atualiza prévias, contadores e indicadores.

**Tipo de manutenção:** Perfectiva

**Observação:** Esta alteração aprimora a navegação de conversas já existentes; não representa a criação do chat.

### 5.8 Atalho da conversa privada para solicitar um serviço

**Problema ou necessidade:** O usuário precisava de um caminho mais direto entre uma conversa privada existente e a solicitação de serviço ao prestador.

**O que foi feito:** Foi adicionada uma ação contextual “Solicitar serviço” na conversa privada, acompanhada de orientação para iniciar a contratação.

**Arquivos envolvidos:** `app.py`; `templates/conversa.html`; `tests/test_chat_consolidation.py`.

**Objetivo:** Facilitar a transição da conversa para o fluxo de solicitação de serviço.

**Evidência:** Commit `f8d4fdb`; a conversa privada e a solicitação de serviço já existiam; o template oferece o atalho contextual e `test_conversa_privada_oferece_botoes_de_transicao_para_servico` verifica essa ação.

**Tipo de manutenção:** Perfectiva

**Observação:** Trata-se de melhoria de navegação/UX sobre fluxos existentes, não da criação da conversa ou da solicitação.

### 5.9 Atalhos telefônicos no chat de serviço

**Problema ou necessidade:** No chat de serviço existente, os telefones dos participantes ainda não eram apresentados como links diretos para iniciar uma ligação.

**O que foi feito:** Os telefones passaram a ser apresentados em contextos pertinentes do chat e disponibilizados como links `tel:`.

**Arquivos envolvidos:** `app.py`; `templates/chat.html`; `static/js/main.js`; `static/css/design-system.css`.

**Objetivo:** Facilitar o contato entre participantes durante um atendimento já existente.

**Evidência:** Commit `76281ac`; telefones são disponibilizados no contexto do chat e renderizados em links `tel:` no template e nas mensagens dinâmicas do JavaScript; o CSS estiliza `.chat-phone`.

**Tipo de manutenção:** Perfectiva

### 5.10 Exibição de telefone na lista administrativa

**Problema ou necessidade:** A lista administrativa existente não apresentava o telefone junto às demais informações dos usuários.

**O que foi feito:** Foi adicionada uma coluna de telefone à tabela de usuários do painel administrativo.

**Arquivos envolvidos:** `templates/dashboard_admin.html`.

**Objetivo:** Melhorar a consulta das informações de contato dos usuários.

**Evidência:** Commit `76281ac`; a tabela administrativa existente passou a exibir a coluna `Telefone` com `user.telefone`.

**Tipo de manutenção:** Perfectiva

## 6. Tabela-resumo das manutenções

| Nº | Manutenção                       | Tipo       | Arquivos/Diretórios principais                                                                 | Objetivo                                 |
| -- | -------------------------------- | ---------- | ---------------------------------------------------------------------------------------------- | ---------------------------------------- |
| 1  | Correção dos endpoints           | Corretiva  | `app.py`, `auth.py`                                                                            | Corrigir redirecionamentos               |
| 2  | Fluxo PRG                        | Corretiva  | `auth.py`                                                                                      | Melhorar o tratamento de POST            |
| 3  | Validação de uploads             | Corretiva  | `auth.py`                                                                                      | Restringir formatos de imagem            |
| 4  | Sintaxe CSS                      | Corretiva  | `style.css`                                                                                    | Corrigir a estrutura do CSS              |
| 5  | Referências do banco             | Corretiva  | `db.py`                                                                                        | Reparar referências após alterações      |
| 6  | Prestadores em destaque          | Corretiva  | `public.py`                                                                                    | Melhorar a seleção de prestadores        |
| 7  | Acesso ao chat                   | Corretiva  | `app.py`, `test_chat_consolidation.py`                                                         | Restringir acesso aos participantes      |
| 8  | Horário do chat                  | Corretiva  | `app_init.py`, `requirements.txt`, `chat.html`, `conversa.html`                                | Corrigir o fuso horário                  |
| 9  | Docker                           | Adaptativa | `Dockerfile`, `.dockerignore`                                                                  | Adaptar a execução para contêiner        |
| 10 | CI/CD                            | Adaptativa | `deploy.yml`                                                                                   | Automatizar testes e deploy              |
| 11 | Localidades do IBGE              | Adaptativa | `atualizar_localidades.py`, `brazilian_locations.json`, arquivos de cadastro                   | Integrar dados de localidades            |
| 12 | CSRF e tratamento seguro         | Preventiva | `security.py`, `app.py`, `auth.py`, `main.js`, templates com `_csrf_token`                     | Reduzir riscos de segurança              |
| 13 | Testes isolados                  | Preventiva | `tests`, `deploy.yml`                                                                          | Reduzir interferência no banco principal |
| 14 | Regras de versionamento          | Preventiva | `.gitignore`                                                                                   | Evitar versionamento acidental           |
| 15 | Escape de dados                  | Preventiva | `dashboard_empresa.html`                                                                       | Escapar o valor exibido no atributo HTML |
| 16 | Interface do chat                | Perfectiva | `design-system.css`                                                                            | Melhorar a apresentação visual           |
| 17 | Página inicial                   | Perfectiva | `home.html`, `public.css`, `home`                                                              | Melhorar a apresentação da home          |
| 18 | Categorias                       | Perfectiva | `home.html`, `public.css`, `categorias`                                                        | Facilitar a identificação dos serviços   |
| 19 | Responsividade                   | Perfectiva | CSS e templates indicados na seção 5.4                                                         | Melhorar a adaptação às telas            |
| 20 | Fluxo de cadastro                | Perfectiva | `cadastro.html`, `main.js`, `style.css`, `brazilian_locations.json`, `test_registration_ui.py` | Melhorar a experiência de cadastro       |
| 21 | Organização arquitetural parcial | Perfectiva | `routes`, `services`, `utils`, `socket_handlers`, `models`, `app.py`                           | Separar responsabilidades parcialmente   |
| 22 | Busca e navegação da lista de conversas | Perfectiva | `app.py`, `index.html`, `main.js`, `design-system.css` | Melhorar a localização e navegação das conversas |
| 23 | Atalho para solicitar serviço | Perfectiva | `app.py`, `conversa.html`, `test_chat_consolidation.py` | Facilitar a transição da conversa para o serviço |
| 24 | Atalhos telefônicos no chat | Perfectiva | `app.py`, `chat.html`, `main.js`, `design-system.css` | Facilitar o contato entre participantes |
| 25 | Telefone no painel administrativo | Perfectiva | `dashboard_admin.html` | Facilitar a consulta dos usuários |

**Nota sobre a tabela:** Os nomes `home` e `categorias` representam diretórios; os arquivos individuais correspondentes estão discriminados nas subseções 5.2 e 5.3.

## 7. Conclusão

O histórico da branch `limpeza-tcc` registra manutenções corretivas, adaptativas, preventivas e perfectivas no Zenvix Connect. As alterações documentadas abrangem correção de fluxos, adaptação a Docker e CI/CD, proteção e isolamento de testes, além de melhorias na interface e na organização do projeto.

A classificação foi limitada às alterações que puderam ser relacionadas a commits e evidências do código atual. A organização arquitetural permanece parcial, e a configuração Docker não exclui o arquivo `database.db` pelo padrão `database_*.db` existente em `.dockerignore`.
