# Auditoria técnica — Zenvix Connect

Data: 22/07/2026

## Conta administrativa

- E-mail: `admin@gmail.com`
- Senha de demonstração: `admin123456`
- Criação/ajuste: executado automaticamente na inicialização do Flask.
- Destino após login: `/admin`.

## Arquivos revisados

| Arquivo | Situação | Decisão |
| --- | --- | --- |
| `templates/admin.html` | Versão antiga do painel; nenhuma rota a renderiza. | Remover. |
| `templates/dashboard.html` | Não é alcançável: `/dashboard` apenas redireciona para painéis específicos. | Remover. |
| `templates/index.html` | Wrapper de compatibilidade sem chamada no Flask após a migração para `public/home.html`. | Remover. |
| `templates/login.html` | Wrapper de compatibilidade sem chamada no Flask após a migração para `auth/login.html`. | Remover. |
| `templates/cadastro.html` | Wrapper de compatibilidade sem chamada no Flask após a migração para `auth/cadastro.html`. | Remover. |
| `templates/base.html` | Layout de compatibilidade usado pelos templates ainda não migrados para subpastas. | Manter. |
| `static/css/style.css` | Regras visuais antigas ainda usadas por telas não migradas. | Manter até a próxima refatoração de dashboards. |
| `static/css/design-system.css` | Design system global ativo. | Manter. |
| `static/css/public.css` | Estilos da Home e autenticação ativos. | Manter. |
| `static/js/main.js` | Controla as etapas e validações do cadastro. | Manter. |
| `static/uploads/images_1.png` | Referenciado por um registro na tabela `usuarios`. | Manter. |
| `__pycache__/` | Cache gerado pelo Python; não é código-fonte. | Ignorar no controle de versão. |

## Rotas

| Grupo | Situação | Observação |
| --- | --- | --- |
| `/`, `/login`, `/cadastro`, `/logout` | Ativas | Fluxo público e autenticação concluídos. |
| `/dashboard`, `/dashboard-cliente`, `/dashboard-profissional`, `/dashboard-empresa` | Ativas | `/dashboard` redireciona conforme o tipo da conta. |
| `/admin`, `/admin/aprovar-usuario/<id>`, `/admin/recusar-usuario/<id>`, `/admin/categorias` | Ativas | Protegidas para administradores. |
| `/admin/documento/<id>/<tipo>` | Ativa | Exibe documento enviado, com validação de sessão admin. |
| `/profissionais`, `/solicitar-servico/<id>`, `/meus-servicos`, `/avaliar/<id>` | Ativas | Fluxo de descoberta e contratação. |
| `/servico/<id>/chat`, `/servico/<id>/atualizar-status`, `/servico/<id>/recusar` | Ativas | Chat e ciclo operacional do serviço. |
| `/disponibilidade/*`, `/empresa/servico/*`, `/favorito/*` | Ativas | Agenda, catálogo empresarial e favoritos. |
| `/perfil`, `/perfil/alterar-senha`, `/perfil/excluir-conta` | Ativas | Os dois últimos receberam templates nesta etapa. |
| `/forgot-password` | Preparada | Exibe confirmação; envio real de e-mail ainda não está integrado. |

## Funcionalidades

- Chat: ativo, usando a tabela `mensagens` e vínculo por serviço.
- Agenda: ativa, usando a tabela `disponibilidade`.
- Aprovação de perfis/documentos: ativa; admin pode aprovar, recusar e abrir documentos enviados.
- Pagamentos: não há modelo, rota ou integração; preparado para etapa futura.
- Notificações: não há modelo ou canal de entrega; preparado para etapa futura.
