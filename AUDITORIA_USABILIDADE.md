# Auditoria de usabilidade e funcionalidades

Data: 22/07/2026

## Mapa de ações

| Página | Botão, link ou menu | Função atual | Situação / ação tomada |
| --- | --- | --- | --- |
| Home | Buscar profissionais | Abre `/profissionais` com categoria e cidade. | Ativo. |
| Home | Categorias | Abrem a busca já filtrada. | Ativo. |
| Home | Ver perfil / Ver disponíveis | Abre perfil público ou lista de online. | Ativo. |
| Home | Criar conta / Entrar | Abrem cadastro e login. | Ativo. |
| Login | Entrar | Autentica, cria sessão e redireciona por tipo. | Ativo. |
| Login | Ajuda para acessar | Abre aviso de recuperação por e-mail ainda não integrada. | Preparado corretamente; não promete envio inexistente. |
| Cadastro | Tipo, Continuar, Voltar, Finalizar | Controlados pelo JS e persistidos pelo Flask. | Ativo. |
| Busca | Filtros, Ver perfil, Solicitar | Filtram apenas prestadores ativos, abrem perfil e criam solicitação. | Ativo. |
| Cliente | Buscar, Ver serviços, Perfil, Favoritos, Chat, Avaliar | Navegação, contratação, favoritos, conversa e avaliação pós-conclusão. | Ativo. |
| Cliente | Configurações | Antes apontava para âncora inexistente. | Corrigido para `/perfil`. |
| Profissional | Editar perfil | Antes possuía destino sem rota. | Rota `/perfil` implementada; salva informações. |
| Profissional | Aceitar, Recusar, Iniciar, Concluir | Atualizam o ciclo de uma solicitação própria. | Ativo. |
| Profissional | Agenda | Adiciona e remove disponibilidade. | Ativo. |
| Profissional | Financeiro | Mostra ganhos e comissão calculados de serviços concluídos. | Ativo. |
| Empresa | Cadastro/remoção de serviços e aceite de solicitações | Gerencia catálogo e solicitações destinadas à empresa. | Ativo. |
| Empresa | Perfil | Usa a rota comum `/perfil`; salva nome, contato, cidade e descrição. | Ativo. |
| Admin | Usuários, aprovar, recusar, documentos, categorias | Administração e aprovação protegidas por sessão admin. | Ativo. |
| Serviço | Mensagens | Cria e lista mensagens para participantes do mesmo serviço. | Ativo. |
| Perfil | Atualizar perfil, senha e exclusão | Salva perfil, troca senha e registra pedido de exclusão. | Ativo. |

## Fluxos validados

- Login direciona cliente, profissional, empresa e administrador para o painel correto.
- Cadastro salva cliente e cria cadastros pendentes para profissional/empresa.
- Busca só retorna profissional ou empresa com aprovação `Ativo`.
- Solicitação cria serviço `Pendente` para o prestador escolhido.
- Prestador autorizado atualiza o status; cliente avalia somente serviço concluído.
- Chat exige que o usuário participe do serviço.
- Favoritos são vinculados ao cliente e ao prestador.

## Estados vazios e recursos futuros

- Listas sem resultados mostram mensagem de estado vazio.
- Recuperação de senha por e-mail: preparada para integração futura; tela informativa, sem falso envio.
- Notificações automáticas: ainda não possuem tabela/canal; prioridade alta para próxima etapa.
- Pagamento online, mapa e aplicativo mobile: não implementados; não há botões falsos para eles.

## Próximas melhorias sugeridas

1. **Alta:** notificações dentro do sistema para nova solicitação, chat e aprovação.
2. **Alta:** histórico mais detalhado e filtros salvos para clientes.
3. **Alta:** avaliação com resposta do prestador e resumo público.
4. **Média:** relatórios administrativos por período e destaque de prestadores.
5. **Média:** planos premium/cuponagem, somente após validar o fluxo principal.
6. **Baixa:** pagamento online, mapa e aplicativo mobile.
