# ZENVIX CONNECT

Documento principal consolidado do projeto.

## 1. Visao geral

O Zenvix Connect e um marketplace de servicos desenvolvido para conectar clientes a profissionais e empresas. A aplicacao oferece descoberta de prestadores, solicitacao e acompanhamento de servicos, comunicacao por chat e avaliacao.

**Estado geral:** IMPLEMENTADO com pendencias relevantes de produto, cobertura e operacao.

## 2. Objetivo do sistema

Disponibilizar uma plataforma web para que clientes encontrem prestadores ativos, solicitem servicos e acompanhem seu ciclo, enquanto profissionais e empresas gerenciam oportunidades, disponibilidade e atendimento.

## 3. Problema resolvido

Centraliza a descoberta de prestadores, a abertura de solicitacoes, a comunicacao entre participantes e o acompanhamento basico do atendimento, reduzindo a dependencia de contatos dispersos e processos manuais.

## 4. Publico-alvo

- Clientes que precisam contratar servicos.
- Profissionais autonomos que oferecem servicos.
- Empresas que oferecem catalogos de servicos.
- Administradores responsaveis por aprovacao e organizacao da plataforma.

## 5. Tipos de usuarios

### Cliente

Pode criar conta, pesquisar prestadores ativos, favoritar, solicitar servicos, conversar com participantes e avaliar servicos concluidos.

**Estado:** IMPLEMENTADO parcialmente conforme cobertura automatizada atual.

### Profissional

Pode criar perfil sujeito a aprovacao, informar especialidade e disponibilidade, receber solicitacoes, aceitar, iniciar, concluir ou recusar servicos e conversar com o cliente.

**Estado:** IMPLEMENTADO parcialmente; testes manuais e cobertura administrativa ainda pendentes.

### Empresa

Pode criar perfil sujeito a aprovacao, cadastrar servicos empresariais, receber solicitacoes e participar do atendimento.

**Estado:** IMPLEMENTADO parcialmente; catalogo e fluxo completo ainda precisam de testes dedicados.

### Administrador

Pode acessar painel restrito, consultar usuarios, aprovar ou recusar profissionais e empresas, consultar documentos e cadastrar categorias.

**Estado:** IMPLEMENTADO no backend; operacoes administrativas ainda precisam de cobertura automatizada completa.

## 6. Funcionalidades

| Funcionalidade | Estado |
| --- | --- |
| Cadastro de cliente, profissional e empresa | IMPLEMENTADO |
| Login, logout e sessoes | IMPLEMENTADO |
| Dashboards por tipo de usuario | IMPLEMENTADO |
| Busca e filtros de prestadores | IMPLEMENTADO |
| Favoritos | IMPLEMENTADO |
| Solicitacao de servico | IMPLEMENTADO |
| Ciclo pendente, aceito, em andamento e concluido | IMPLEMENTADO |
| Recusa de servico | IMPLEMENTADO |
| Disponibilidade profissional | IMPLEMENTADO |
| Avaliacao de servico concluido | IMPLEMENTADO |
| Chat por servico com persistencia | IMPLEMENTADO |
| Chat privado legado descrito em documentos antigos | OBSOLETO/NAO CONFIRMADO |
| Aprovacao de perfis | IMPLEMENTADO |
| Categorias administrativas | IMPLEMENTADO |
| Pagamentos | PLANEJADO |
| Notificacoes | PLANEJADO |
| Recuperacao de senha por e-mail | PENDENTE |

## 7. Fluxos do sistema

### Cadastro e acesso

1. Usuario acessa cadastro e escolhe o tipo de conta.
2. Preenche dados gerais e dados especificos do tipo.
3. Cliente recebe status ativo; profissional e empresa ficam pendentes de aprovacao.
4. Usuario faz login e e direcionado ao dashboard correspondente.
5. Logout encerra a sessao e marca a presenca como offline.

### Contratacao

1. Cliente pesquisa prestadores ativos.
2. Cliente abre perfil e solicita um servico.
3. O servico e criado como `Pendente`.
4. O prestador autorizado acessa a solicitacao.
5. O prestador pode aceitar, iniciar e concluir, ou recusar.
6. Apos conclusao, o cliente pode avaliar uma vez.

### Chat

O chat atual e vinculado a um servico. Somente cliente e prestador registrados no servico podem acessar a rota e entrar na sala Socket.IO correspondente.

### Administracao

1. Administrador autenticado acessa `/admin`.
2. Consulta pendencias, usuarios e categorias.
3. Aprova ou recusa profissionais e empresas.
4. Consulta documentos por rota administrativa autorizada.

## 8. Regras de negocio

- Apenas clientes podem criar solicitacoes.
- O destino da solicitacao deve ser profissional ou empresa ativo.
- Somente o prestador vinculado pode alterar o status do servico.
- As transicoes validas sao `Pendente` -> `Aceito` -> `Em andamento` -> `Concluido`.
- Um servico concluido nao pode ser alterado novamente.
- Somente o cliente participante pode avaliar o servico.
- A nota deve estar entre 1 e 5.
- Uma avaliacao por servico e permitida.
- Favoritos pertencem ao cliente autenticado e ao prestador selecionado.
- Disponibilidade pertence ao profissional autenticado; horarios invertidos e duplicados sao rejeitados.
- Chat e rooms devem ser acessiveis somente aos participantes do servico.
- Operacoes administrativas exigem usuario do tipo administrador.
- Profissionais e empresas pendentes ou recusados nao devem ser tratados como prestadores ativos.

## 9. Arquitetura

Aplicacao web monolitica de pequeno porte:

- Flask concentra rotas, sessoes, regras e acesso ao banco.
- Jinja2 renderiza templates no servidor.
- JavaScript melhora interacoes de cadastro, presenca e chat.
- Flask-SocketIO fornece eventos em tempo real.
- SQLite armazena usuarios, servicos, mensagens e demais entidades.
- Eventlet e usado pela stack Socket.IO.

Nao ha frontend separado nem API REST independente documentada.

## 10. Stack tecnologica

- Python.
- Flask 3.0.0.
- Flask-SocketIO 5.4.1.
- Eventlet 0.39.1.
- SQLite.
- Jinja2.
- Werkzeug para hash de senha, nomes seguros e utilitarios HTTP.
- HTML, CSS e JavaScript.
- Pytest 8.3.5 para testes automatizados.

## 11. Backend

O backend esta concentrado em `app.py` e inclui:

- Inicializacao Flask e Socket.IO.
- Criacao e migracao incremental do schema.
- Conexao SQLite por contexto Flask.
- Cadastro e autenticacao.
- Autorizacao por sessao e tipo de usuario.
- Dashboards e ciclo de servicos.
- Uploads e visualizacao administrativa de documentos.
- Chat persistido em SQLite e eventos Socket.IO.
- Presenca online baseada em atualizacao no banco.
- Validacao global de CSRF para requisicoes POST.

## 12. Frontend

Os templates ficam em `templates/`, organizados por areas publicas, autenticacao, dashboards e componentes. CSS fica em `static/css/`; JavaScript principal em `static/js/main.js`.

O layout injeta token CSRF em meta tag e adiciona o campo aos formularios POST no navegador. O chat usa `textContent` quando essa protecao esta presente na implementacao atual; a validacao frontend nunca substitui a validacao do backend.

## 13. Banco de dados

O banco padrao e `database.db`, criado no diretorio do projeto. O schema contem, entre outras, as tabelas:

- `usuarios`
- `servicos`
- `avaliacoes`
- `favoritos`
- `mensagens`
- `disponibilidade`
- `servicos_empresa`
- `conversas`
- `conversa_participantes`
- `conversa_mensagens`
- `categorias`

A inicializacao usa `CREATE TABLE IF NOT EXISTS` e migracoes incrementais por coluna. Testes da fase 2 usam banco temporario e nao devem destruir o banco local.

**Risco pendente:** ainda e recomendavel formalizar migracoes, constraints de unicidade e verificacao de foreign keys para producao.

## 14. Autenticacao e autorizacao

Senhas sao armazenadas com hash via Werkzeug. A sessao guarda identificador, nome, tipo e status de aprovacao. Rotas de dashboard, servicos, avaliacoes, documentos e administracao verificam autenticacao e, quando aplicavel, o tipo e a titularidade do recurso.

Em producao, `SECRET_KEY`, `ADMIN_EMAIL` e `ADMIN_PASSWORD` devem ser fornecidos por variaveis de ambiente. Valores secretos nao fazem parte deste documento.

## 15. Seguranca

- **CSRF:** validacao global para POST usando token associado a sessao e comparacao resistente a timing attacks. **Estado:** IMPLEMENTADO e testado.
- **XSS:** documentos anteriores registram correcao para renderizacao de mensagens com `textContent`. **Estado:** historico documentado; teste de navegador ainda pendente.
- **IDOR/BOLA:** testes verificam isolamento de servicos, chat, avaliacoes e disponibilidade. **Estado:** cobertura parcial.
- **Sessoes:** chave aleatoria em desenvolvimento e exigencia de chave forte em producao.
- **SQL:** queries observadas usam parametros; revisao automatica completa ainda e pendente.
- **Autorizacao:** painel administrativo e rooms de servico exigem vinculo/tipo adequado.

## 16. Uploads e documentos

Extensoes aceitas: PDF, JPG, JPEG e PNG. O backend limita o corpo a 8 MiB, relaciona MIME e extensao e salva nomes aleatorios, evitando sobrescrita direta pelo nome enviado.

Documentos administrativos ainda ficam sob `static/uploads` e sao expostos por uma rota protegida para administradores. A migracao para armazenamento fora de `static/` e uma pendencia de seguranca.

## 17. Chat e Socket.IO

O chat atual usa `/servico/<id>/chat`, a tabela `mensagens` e rooms `service_<id>`. O cliente e o profissional vinculados ao servico podem entrar na room e trocar mensagens. A rota HTTP tambem verifica o vinculo antes de exibir ou persistir mensagens.

Documentos antigos mencionam uma rota `/conversa/<id>`, `templates/conversa.html` e tabelas de conversas privadas. Essas referencias nao coincidem com o inventario mais recente.

**[CONFLITO DOCUMENTAL — REVISAO NECESSARIA]** A documentacao historica descreve um fluxo privado adicional que nao esta confirmado no fluxo atual; foi mantido aqui apenas como historico, nao como funcionalidade ativa.

## 18. Rotas

Inventario consolidado a partir do mapa de rotas registrado:

| Metodos | Rotas principais |
| --- | --- |
| GET | `/`, `/chat`, `/chat/`, `/dashboard`, `/dashboard-cliente`, `/dashboard-profissional`, `/dashboard-empresa`, `/admin`, `/admin/documento/<id>/<tipo>`, `/meus-servicos`, `/profissionais`, `/profissional/<id>`, `/empresa/<id>`, `/logout` |
| GET, POST | `/login`, `/cadastro`, `/forgot-password`, `/perfil`, `/perfil/alterar-senha`, `/perfil/excluir-conta`, `/solicitar-servico/<id>`, `/servico/<id>/chat`, `/avaliar/<id>` |
| POST | `/admin/aprovar-usuario/<id>`, `/admin/recusar-usuario/<id>`, `/admin/categorias`, `/presenca/heartbeat`, `/favorito/<id>/toggle`, `/disponibilidade/adicionar`, `/disponibilidade/<id>/remover`, `/empresa/servico/adicionar`, `/empresa/servico/<id>/remover`, `/servico/<id>/recusar`, `/servico/<id>/atualizar-status` |
| GET | `/static/<path:filename>` |

`/forgot-password` esta parcialmente implementada: informa que o recurso esta em preparacao, mas nao envia e-mail nem cria token de redefinicao.

## 19. APIs e contratos

Nao existe API REST publica separada. Os contratos HTTP principais sao formularios HTML com redirects e mensagens flash. O chat aceita POST de formulario e pode retornar JSON quando enviado com `X-Requested-With: XMLHttpRequest`.

Eventos Socket.IO relevantes:

- `connect`
- `disconnect`
- `join_service`
- `nova_mensagem`
- `mensagem_lida`

O cliente deve enviar o token CSRF no header `X-CSRF-Token` para requisicoes AJAX POST.

## 20. Testes

A fase 2 criou uma estrutura `tests/` com banco e uploads temporarios.

- Total executado: 11.
- PASS: 11.
- FAIL: 0.
- SKIP: 0.

Areas cobertas:

- Cadastro de cliente, profissional e empresa.
- Login invalido e logout.
- Paginas protegidas e separacao de tipos.
- Isolamento de servicos, chat, avaliacoes e disponibilidade.
- Ciclo de servico e transicoes invalidas.
- Favoritos e IDs inexistentes.
- Horarios invalidos e duplicidades.
- CSRF sem token, token incorreto e token correto.
- Upload MIME/extensao e nomes unicos.
- Entrada autorizada e nao autorizada em room Socket.IO.
- Paginas inexistentes.

Ainda sem cobertura suficiente:

- Operacoes administrativas completas.
- Todos os POSTs individualmente.
- Testes de navegador, console, responsividade e XSS end-to-end.
- Recuperacao de senha.
- Concorrencia e integridade completa do banco.
- Teste manual integral de todos os perfis.

## 21. Auditoria tecnica

A auditoria mais recente foi registrada em 24/08/2026 e classificou o sistema como **APROVADA COM PENDENCIAS**. O baseline analisado foi `08ec9f61bc016216d8840f1700383cf78b5afcae`.

## 22. Bugs encontrados e correcoes

| ID | Severidade | Problema | Arquivo | Correcao | Status |
| --- | --- | --- | --- | --- | --- |
| SEC-01 | Critica | Defaults previsiveis para chave de sessao e admin | `app.py` | Exigencia de ambiente em producao; chave aleatoria em desenvolvimento | Corrigido |
| SEC-02 | Alta | POSTs sem protecao CSRF | `app.py`, layout, JS | Token de sessao validado globalmente | Corrigido |
| SEC-03 | Alta | Room Socket.IO permitia usuario sem vinculo | `app.py` | Room limitada aos participantes | Corrigido |
| SEC-04 | Alta | Upload dependia de extensao e podia sobrescrever nome | `app.py` | MIME compativel, limite e nome aleatorio | Corrigido |
| AUTH-01 | Media | Solicitacao aceitava destino que nao era prestador | `app.py` | Aceita apenas profissional ou empresa ativo | Corrigido |
| FUNC-01 | Media | `.get()` usado em `sqlite3.Row` no Socket.IO | `app.py` | Acesso por chave da row | Corrigido |
| FUNC-02 | Media | Horarios invertidos e duplicados aceitos | `app.py` | Parse, ordem e verificacao de duplicidade | Corrigido |
| FUNC-03 | Media | Favorito podia apontar para ID inexistente | `app.py` | Validacao do prestador antes do INSERT | Corrigido |
| OPS-01 | Baixa | Artefatos locais sem exclusao documentada | `.gitignore` | Regras para cache, banco, uploads e temporarios | Corrigido |

Os documentos v0.6 tambem registram correcoes historicas de XSS, presenca e autorizacao de conversas. Como algumas referencias nao coincidem com o inventario atual, esses itens permanecem como historico sujeito a confirmacao.

## 23. Estado atual do sistema

- **IMPLEMENTADO:** aplicacao Flask, SQLite, autenticacao, dashboards, servicos, favoritos, disponibilidade, avaliacoes, chat por servico, Socket.IO, CSRF e validacoes principais.
- **PARCIALMENTE IMPLEMENTADO:** administracao testada apenas em parte, uploads privados, cobertura de frontend e fluxos completos por perfil.
- **PENDENTE:** recuperacao real de senha, testes manuais completos, testes frontend e armazenamento privado de documentos.
- **PLANEJADO:** pagamentos e notificacoes.
- **OBSOLETO:** referencias documentais ao fluxo privado `/conversa/<id>` quando tratadas como rota ativa sem confirmacao no inventario atual.

## 24. Pendencias

1. Mover documentos administrativos para fora de `static/` e servir por rota autorizada.
2. Implementar recuperacao de senha com tokens de uso unico e infraestrutura de e-mail segura.
3. Expandir testes administrativos, de banco, concorrencia e todos os POSTs.
4. Executar teste manual dos fluxos cliente, profissional, empresa e administrador.
5. Adicionar testes de navegador para XSS, console, Socket.IO e responsividade.
6. Formalizar migracoes e constraints do SQLite.

## 25. Limitacoes conhecidas

- SQLite e adequado ao desenvolvimento local, mas limita escalabilidade e concorrencia.
- Presenca depende de heartbeat e estado persistido; cenarios multi-aba exigem validacao manual.
- Nao ha pagamentos, notificacoes ou envio de e-mail.
- Nao ha API externa documentada.
- Uploads ainda compartilham arvore de arquivos estaticos.
- O status de documentacao nao equivale a homologacao de producao.

## 26. Configuracao e instalacao

Requisito: Python compativel com o ambiente do projeto.

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

O banco e inicializado automaticamente quando a aplicacao e carregada. Para testes, utilize o banco temporario fornecido pelas fixtures.

## 27. Execucao local

```bash
python app.py
```

A aplicacao fica normalmente em `http://127.0.0.1:5000/`. Para execucao na rede local, o projeto tambem possui `run_lan.py`.

Testes:

```bash
pytest
python -m py_compile app.py
```

## 28. Estrutura de pastas

```text
app.py
run_lan.py
requirements.txt
ZENVIX_CONNECT.md
tests/
static/
  css/
  js/
  uploads/
templates/
  admin/
  auth/
  chat/
  cliente/
  components/
  empresa/
  layouts/
  profissional/
  public/
database.db
```

`database.db`, uploads e caches sao artefatos locais e nao devem ser tratados como documentacao fonte.

## 29. Dependencias

As dependencias declaradas sao Flask, Flask-SocketIO, eventlet e pytest. A lista oficial esta em `requirements.txt`; versoes devem ser atualizadas somente mediante decisao tecnica registrada.

## 30. Variaveis de ambiente

- `SECRET_KEY`: obrigatoria em producao; deve ter pelo menos 32 caracteres.
- `ADMIN_EMAIL`: e-mail administrativo configurado fora do codigo.
- `ADMIN_PASSWORD`: senha administrativa configurada fora do codigo e com comprimento forte.
- `FLASK_ENV`: define o modo de producao quando configurado como `production`.
- `FLASK_DEBUG`: habilita debug quando configurado como `1`.
- `PORT`: porta HTTP; padrao local 5000.

Nenhum valor de segredo, token ou credencial e armazenado neste documento.

## 31. Decisoes tecnicas

- Manter Flask, SQLite, Jinja e Flask-SocketIO para preservar o projeto existente.
- Preferir correcoes locais a reescrita arquitetural.
- Usar queries parametrizadas.
- Isolar testes em banco temporario.
- Manter migracoes incrementais e evitar destruicao do banco existente.
- Usar validacao no backend como autoridade para seguranca e regras de negocio.
- Nao documentar funcionalidades antigas como ativas sem confirmacao no codigo atual.

## 32. Historico relevante

- O projeto foi iniciado como marketplace Flask com SQLite.
- A versao de referencia das auditorias foi `08ec9f6`.
- Documentos v0.6 registraram correcoes pretendidas de XSS, CSRF, presenca e autorizacao.
- A primeira rodada de hardening removeu defaults inseguros, restringiu Socket.IO, endureceu uploads e adicionou CSRF.
- A fase 2 criou testes isolados e corrigiu bugs funcionais em Socket.IO, uploads, favoritos e disponibilidade.
- A documentacao anterior continha credenciais de demonstracao; esses valores foram deliberadamente descartados.

## 33. Proximos passos

1. Completar a matriz automatizada de administracao e isolamento.
2. Fazer homologacao manual por tipo de usuario.
3. Corrigir armazenamento privado de documentos.
4. Implementar recuperacao de senha somente com infraestrutura segura.
5. Revisar e confirmar o historico de conversa privada legado.

## 34. Checklist final

- [x] Todos os 5 arquivos Markdown existentes foram inventariados e lidos.
- [x] Informacoes repetidas foram consolidadas.
- [x] Credenciais, senhas, tokens e secrets foram excluidos.
- [x] Conflitos documentais foram marcados.
- [x] Estados IMPLEMENTADO, PARCIALMENTE IMPLEMENTADO, PENDENTE, PLANEJADO e OBSOLETO foram diferenciados.
- [x] Testes reais registrados: 11 PASS, 0 FAIL, 0 SKIP.
- [x] Rotas e estrutura principal registradas.
- [x] Nenhum codigo, banco, HTML, CSS ou JavaScript foi alterado nesta consolidacao.
- [ ] Testes manuais e frontend ainda nao concluídos.
- [ ] Documentos administrativos ainda nao foram movidos para armazenamento privado.

## Fontes consolidadas

- `README.md`
- `AUDITORIA.md`
- `CORRECOES_IMPLEMENTADAS.md`
- `CHECKLIST_TESTES.md`
- `RESUMO_FINAL_v0.6.md`
