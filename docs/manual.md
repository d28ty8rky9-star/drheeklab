# Manual das Fases 1–8

1. Escolha o ambiente. TESTES nunca acessa o banco de PRODUÇÃO. Ambos são separados fisicamente, sem migração automática entre eles.
2. Cadastre a senha no primeiro acesso. Nas próximas aberturas, autentique-se. Em Configurações, a troca de senha exige a senha atual. Não há recuperação automática de senha nesta fase.
3. Use o menu lateral; ☰ recolhe o menu. O botão Tema alterna claro/escuro. Essas preferências são preservadas por ambiente.
4. Anotações em Início são rascunhos livres, salvos após 600 ms de inatividade e ao fechar. Após falha inesperada, o último salvamento é recuperado; caracteres digitados antes do próximo salvamento podem ser perdidos. Não são pedidos ou lançamentos financeiros.
5. Configurações permite abrir a pasta, importar logo PNG/JPEG original, mudar senha, consultar auditoria e criar/restaurar backups.
6. Impressoras, Vendas → Precificação, Produtos e Estoque estão disponíveis. Consulte `fase2.md`, `fase3.md`, `fase4.md`, `fase5.md`, `fase6.md` e `fase7.md` para cadastro, cálculo, arquivos, materiais e peças. Clientes, orçamentos, pedidos, pagamentos, contas a receber e entregas estão disponíveis em Vendas; Início mostra vendas/recebimentos separados. Produção oferece OPs, fila, lotes e inspeção individual com três fotos; Financeiro oferece contas, caixa, compras, aportes, relatórios e exportação; notificações ficam no cabeçalho; documentos, catálogo, auditoria e lixeira em Configurações. Use Buscar no cabeçalho para localizar clientes, pedidos, orçamentos, produtos, projetos, filamentos e produção; selecione um resultado e abra sua área. A busca é literal, inclui arquivados identificados e mostra até 200 resultados. Início e Estoque exibem alerta de filamento baixo.

## Pastas

`C:\DrHeekLab\TESTES` e `C:\DrHeekLab\PRODUÇÃO` contêm separadamente:

| Pasta | Conteúdo |
|---|---|
| Banco de Dados | SQLite permanente |
| Projetos STL e 3MF | Versões STL/3MF preservadas |
| Fotos dos Produtos | Fotos dos produtos e inspeções |
| Orçamentos | PDFs de orçamentos emitidos |
| Pedidos e Comprovantes | Comprovantes comerciais/financeiros e anexos |
| Catálogos | Catálogos PDF emitidos |
| Relatórios | Relatórios PDF e exportações CSV/Excel |
| Backups | ZIPs verificados |
| Logs | Diagnóstico técnico |
| Marca | Logo importado |

`preferences.json` na raiz lembra somente a escolha de ambiente. Os arquivos do programa e dependências não ficam nessas pastas.

## Backup e restauração

O backup automático roda após login e verifica a necessidade de novo backup a cada hora enquanto o programa está aberto, uma vez por dia. No Windows, Configurações → Agendar backup diário permite tarefa com aplicativo fechado enquanto o usuário estiver conectado. Veja `finalizacao-autonoma.md`. Falhas são mostradas e registradas. Não há exclusão automática de backups; monitore espaço disponível.

Backup manual: escolha uma pasta local, pendrive ou HD externo e confirme se deseja criptografia por senha. .hbk usa AES-256-GCM/scrypt; a senha não é salva e não pode ser recuperada. Sem criptografia, sai um ZIP explicitamente identificado. O ZIP inclui banco consistente via API SQLite, todos os arquivos das pastas de documentos e a marca. Logs e backups antigos não são incluídos. O manifesto registra SHA-256; a integridade do SQLite também é verificada. Faça backups externos regulares.

Restaurar: selecione ZIP do **mesmo ambiente**, confirme a substituição e aguarde. O programa valida o arquivo antes de alterar dados, cria backup do estado atual e guarda uma pasta `*-rollback-*` com o estado anterior. Fecha após a restauração; reabra e autentique-se com a senha que existia no backup. O ZIP mantém senha em hash, configurações, rascunhos, cadastros e estoque. Caso uma foto/projeto atual já esteja ausente ou alterado, a restauração de ZIP íntegro preserva o banco consistente e todos os arquivos existentes em rollback, sem chamar esse estado anterior incompleto de backup íntegro. Não renomeie backups de teste para usá-los em produção.

Transferência: instale no outro computador, crie o mesmo ambiente, restaure um ZIP verificado e reabra. Preserve uma cópia independente antes de qualquer operação. O aplicativo bloqueia uma segunda instância do mesmo ambiente usando um arquivo de trava na raiz. Feche outros programas que possam manter arquivos abertos antes de restaurar.

## Atualizações e segurança

Antes de atualizar, crie e verifique backup completo manual. Encerre o aplicativo, instale a nova versão e abra. O esquema usa `PRAGMA user_version`, migrações transacionais e backup completo verificado e preservação SQLite antes de atualização de esquema existente. Bancos com esquema mais novo são recusados. Falhas de migração não consolidam alterações parciais.

Login limita acesso pela interface, **não criptografa banco/fotos ou ZIPs locais**. Backup .hbk opcional é criptografado; cópias automáticas, temporárias e rollback permanecem em disco local sem essa criptografia. Permissões do Windows e proteção física do computador são necessárias. Os backups contêm dados privados; não compartilhe. O instalador concede escrita aos usuários locais na pasta padrão para operação sem privilégios administrativos, portanto outros usuários locais podem acessar arquivos. Guarde dados sensíveis em armazenamento com acesso restrito. Nunca apague pastas de dados para resolver erro.

Se um erro ocorrer, a interface informa a falha; detalhes ficam em Logs/application.log. Mudanças críticas de configurações e senha são auditadas; senhas e hashes nunca aparecem na auditoria. Lixeira, documentos e registros comerciais estão disponíveis nas áreas documentadas.

## Instalação e finalização

Leia `fase8.md` para instalar/atualizar, verificar o pacote, conferir versões e conhecer as pendências Windows. Consulte `matriz-testes.md` e `validacao-windows.md`. A versão 2.8.0 é candidata à homologação; não é anunciada como lançamento Windows pronto.

Instruções atualizadas de instalação, criptografia, agendamento e atualização em `finalizacao-autonoma.md`.
