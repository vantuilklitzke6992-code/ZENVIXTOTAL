# CHECKLIST DE TESTES - Zenvix Connect v0.6

## 🧪 TESTES DE SEGURANÇA

### 1. XSS - Teste de Payload Simples
- [ ] Fazer login como qualquer usuário
- [ ] Ir para chat de serviço ou conversa privada
- [ ] Enviar mensagem: `<script>alert('XSS')</script>`
- [ ] **Resultado esperado**: Mensagem exibida como texto puro, sem execução de script

### 2. XSS - Teste com IMG Tag
- [ ] Enviar mensagem: `<img src=x onerror=alert(1)>`
- [ ] **Resultado esperado**: Mensagem exibida como texto, img tag não renderiza

### 3. CSRF - Teste Token Obrigatório
- [ ] Fazer login
- [ ] Abrir DevTools → Network
- [ ] Enviar mensagem em conversação
- [ ] Verificar POST: `/conversa/<id>`
- [ ] **Resultado esperado**: POST contém `_csrf_token` no body

### 4. CSRF - Teste Token Inválido
- [ ] Fazer login
- [ ] Abrir DevTools → Storage → Cookies
- [ ] Copiar qualquer outra sessão CSRF token
- [ ] Interceptar POST de conversa, modificar token
- [ ] **Resultado esperado**: Erro 400/403 ou mensagem "Token inválido"

### 5. Autorização - Usuário Inativo
- [ ] Buscar um usuário com status "Pendente" ou "Recusado"
- [ ] Clicar no botão "Conversar"
- [ ] **Resultado esperado**: Mensagem "Usuário não está disponível para conversas"

### 6. Autorização - Cliente-Cliente
- [ ] Fazer login como cliente
- [ ] Encontrar outro usuário cliente
- [ ] Clicar em "Conversar"
- [ ] **Resultado esperado**: Mensagem "Clientes não podem conversar entre si"

### 7. Presença - Multi-aba
- [ ] Fazer login em uma aba (aba-1)
- [ ] Abrir mesma URL em outra aba (aba-2)
- [ ] Ambas devem mostrar status "online"
- [ ] Fechar aba-1
- [ ] Aba-2 deve continuar mostrando "online"
- [ ] **Resultado esperado**: Status consistente em ambas as abas

### 8. Presença - Heartbeat
- [ ] Fazer login
- [ ] Abrir DevTools → Network → WebSocket
- [ ] Aguardar ~2 minutos
- [ ] **Resultado esperado**: Heartbeat enviado a cada 120s para `/presenca/heartbeat`

---

## 🔄 TESTES DE FLUXO

### 9. Fluxo Completo - Cliente Contrata Profissional
- [ ] Logout (se conectado)
- [ ] Home page abre normalmente
- [ ] Clicar "Ver profissionais"
- [ ] Listar profissionais OK
- [ ] Fazer login como cliente
- [ ] Dashboard cliente carrega
- [ ] Voltar a profissionais
- [ ] Clicar "Conversar" com profissional ativo
- [ ] Conversa criada/aberta com sucesso
- [ ] Enviar mensagem
- [ ] Mensagem aparece formatada (sem XSS)
- [ ] **Resultado esperado**: Fluxo sem erros

### 10. Fluxo - Profissional Recebe Mensagem
- [ ] Ter 2 browsers abertos (cliente + profissional)
- [ ] Cliente envia mensagem em conversa
- [ ] Profissional vê mensagem em tempo real (Socket.IO)
- [ ] **Resultado esperado**: Mensagem entregue em <1s

### 11. Fluxo - Alterar Senha
- [ ] Fazer login
- [ ] Ir para Perfil → Alterar Senha
- [ ] **Verificar**: Form tem `_csrf_token` hidden input
- [ ] Preencher senhas corretas
- [ ] Clicar "Salvar"
- [ ] **Resultado esperado**: "Senha atualizada com sucesso"

### 12. Fluxo - Novo Cadastro
- [ ] Logout
- [ ] Clicar "Criar conta"
- [ ] Selecionar tipo (Cliente/Profissional/Empresa)
- [ ] **Verificar**: Form tem `_csrf_token` hidden input
- [ ] Preencher todos os dados
- [ ] Clicar "Finalizar cadastro"
- [ ] **Resultado esperado**: Cadastro criado, pode fazer login

### 13. Fluxo - Login
- [ ] Home page
- [ ] Clicar "Entrar"
- [ ] **Verificar**: Form tem `_csrf_token` hidden input
- [ ] Preencher email/senha corretos
- [ ] Clicar "Entrar"
- [ ] **Resultado esperado**: Redirecta para dashboard

---

## 📊 TESTES DE BANCO DE DADOS

### 14. BD - Conversas Criadas
- [ ] Executar: `SELECT COUNT(*) FROM conversas`
- [ ] Executar: `SELECT COUNT(*) FROM conversa_mensagens`
- [ ] **Resultado esperado**: Dados consistentes (sem orphans)

### 15. BD - Status Online
- [ ] Fazer login
- [ ] Executar: `SELECT status_online FROM usuarios WHERE id = ?`
- [ ] **Resultado esperado**: status_online = 'online'
- [ ] Fazer logout
- [ ] Executar mesma query
- [ ] **Resultado esperado**: status_online = 'offline'

---

## 🎯 VERIFICAÇÃO FINAL

### 16. Verificar Sem Erros
- [ ] Abrir DevTools → Console
- [ ] Navegar pelas páginas principais
- [ ] **Resultado esperado**: Nenhum erro vermelho no console

### 17. Verificar Performance
- [ ] Network tab: Todas as requisições completam <2s
- [ ] Aplicação não trava em nenhum momento
- [ ] **Resultado esperado**: UX responsiva

### 18. Verificar Compatibilidade
- [ ] Chrome/Edge: Funciona ✓
- [ ] Firefox: Funciona ✓
- [ ] Mobile: Funciona ✓
- [ ] **Resultado esperado**: Cross-browser compatible

---

## ✅ CHECKLIST FINAL

- [ ] Todos os testes de segurança passaram
- [ ] Todos os testes de fluxo passaram
- [ ] Nenhum erro no console
- [ ] Performance aceitável
- [ ] Cross-browser compatível
- [ ] Pronto para commit
- [ ] Pronto para push
- [ ] Pronto para tag v0.6

---

## 📝 NOTAS DE TESTE

**Data de Teste**: _______________
**Testador**: _______________
**Ambiente**: Windows 10 / Python 3.x / Flask 2.x

### Problemas Encontrados
_____________________________________________________________________________

### Recomendações
_____________________________________________________________________________

---

**Status Geral**: ○ PASSOU ○ FALHOU ○ PENDENTE
