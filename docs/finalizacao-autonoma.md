# Finalização autônoma — versão 2.8.0, esquema 7

Continuidade técnica autorizada em `solicitacao-finalizacao-autonoma.md`, sem aprovações intermediárias. Regras comerciais preservadas. Push, release e alterações externas não foram autorizados. Aplicativo candidato à homologação Windows; não há instalador Windows gerado nesta máquina Linux.

## Para o proprietário

1. **Instalar:** após geração e homologação Windows, execute `DrHeekLab-2.8.0-Fase8-Setup.exe`. A instalação exige administrador; o uso diário não. Atalhos no menu Iniciar e área de trabalho. Não precisa instalar Python no computador de destino, requisito ainda pendente de comprovação prática no Windows.
2. **Abrir:** escolha TESTES, cadastre senha própria e valide os fluxos antes de usar PRODUÇÃO. Os ambientes não compartilham banco/senha. Configure impressoras e filamentos; importe produtos, fotos e STL/3MF. Importe o logo original em Configurações; nenhum substituto foi criado.
3. **Backup manual:** Configurações → Criar backup completo. Escolha pasta, pendrive ou HD e responda à escolha de criptografia. Sim produz `.hbk`; Não produz ZIP sem criptografia. Ambas as formas são verificadas antes da entrega do arquivo final.
4. **Backup com senha:** use 12–1.024 caracteres e confirme a senha. Ela pode ser diferente do login, não é armazenada no banco, logs, tarefa ou argumentos. Guarde-a separadamente: sem a senha não há recuperação do .hbk. Não envie senha junto com o arquivo.
5. **Agendar:** Configurações → Agendar backup diário no Windows. Configure horário local e destino. A tarefa pertence ao usuário atual, usa privilégio normal e executa enquanto esse usuário estiver conectado, mesmo com aplicativo fechado. Executa diariamente e ao entrar no Windows; tenta novamente a cada hora. Se o aplicativo estiver aberto, seu backup diário cobre o ambiente e a tarefa respeita a trava. PC desligado, usuário desconectado ou tarefa desabilitada não são execução garantida.
6. **Configuração assistida:** se o Windows negar a criação, exporte XML pelo mesmo diálogo. No Agendador de Tarefas, importe, confira usuário/ambiente/executável/destino/horário e mantenha privilégios normais. Não coloque senha de criptografia na tarefa. Agendamento faz ZIP **sem criptografia**, informado na tela; use pasta protegida. Logs ficam em Logs/backup-job-*.json. Se o HD estiver ausente, consulte o erro e reconecte para a próxima execução.
7. **Atualizar:** faça backup externo verificado, feche todas as instâncias e execute o novo Setup. O verificador independente faz backup dos ambientes existentes antes de substituir binários e bloqueia instância em uso, banco danificado ou esquema mais novo. Migrações na abertura continuam transacionais e protegidas por backup. A versão 2.8.0 conserva esquema 7. Versões de binários com metadados mais novos não são rebaixadas; versões antigas sem esses metadados não permitem comparação confiável por propriedades do .exe.
8. **Restaurar:** Configurações → Restaurar backup, escolha ZIP/.hbk. Para .hbk, informe primeiro a senha de criptografia; integridade e ambiente são verificados antes da confirmação de substituição. Erro de senha mantém os dados e a janela atual. Confirme, aguarde e reabra com a senha de login do backup. A recuperação da tela inicial também aceita .hbk; autentica o login da cópia verificada antes de substituir. Estado anterior permanece em rollback.
9. **Desinstalar:** remova antes a tarefa em Configurações; tarefas de usuário não são apagadas indiscriminadamente pelo instalador. A desinstalação preserva `C:\DrHeekLab`. Reinstalação deve preservar banco, documentos e permissões existentes; validar no roteiro Windows.

## Criptografia e armazenamento

Implementação pela biblioteca `cryptography` 46.0.3: AES-256-GCM, nonce aleatório de 96 bits, tag de 128 bits; chave de 256 bits derivada por scrypt (N=32768, r=8, p=1) e salt aleatório de 128 bits. Cabeçalho versionado autenticado. Não há algoritmo criptográfico inventado, chave fixa ou senha padrão. Autenticação termina antes de interpretar o ZIP; arquivo adulterado ou senha incorreta impede restauração.

Encriptação e decriptação são processadas em blocos. Preparação/restauração usam cópias temporárias sem criptografia em diretórios temporários protegidos; não há promessa de apagamento forense. O .hbk protege a cópia exportada, não o banco ativo, rollback, backups automáticos ZIP ou todo o disco. Login não criptografa os dados locais. Pasta padrão nova concede escrita aos usuários locais para operação normal; atualização preserva ACL existente. Restrinja acesso às contas autorizadas conforme a configuração do computador.

Backups usam SQLite backup API, incluem todas as mídias/documentos gerenciados, conferem banco/FKs/manifesto/hashes e escrevem arquivo parcial próprio antes de renomear o resultado válido. Falhas removem a saída parcial do processo. Links simbólicos gerenciados são recusados para não copiar conteúdo externo inadvertidamente. Arquivados continuam preservados. Nunca apague dados para resolver erro.

## Ferramentas de suporte

Sem interface, para ambiente já criado:

```powershell
DrHeekLab.exe --scheduled-backup --environment test --data-dir C:\DrHeekLab
DrHeekLab.exe --backup-now --environment production --data-dir C:\DrHeekLab --backup-destination E:\Backups
```

Entrada padrão de senha (`--backup-password-stdin`) é opção para Python/console técnico, não argumento de senha nem configuração da tarefa. Executável sem console recusa essa opção quando não há entrada padrão. Use a interface para .hbk no aplicativo instalado. Não colocar senha em comandos, histórico ou arquivos de script.

Build Windows: `packaging/build-windows.ps1`, com `-IconPath caminho\oficial.ico` quando o original estiver disponível. Pytest/JUnit, pip check, QA do pacote com JSON/versão/criptografia e checksums bloqueiam instalador em falha. `DrHeekLabUpdate.exe` é extraído temporariamente pelo Setup para verificação/backup anterior aos binários. Workflow testa instalação/reinstalação/desinstalação, banco/mídia preservados, backup sem interface e criação/remoção de tarefa em runner descartável. **Nada disso foi executado em Windows nesta sessão.**

Resultados e evidências: `resultados-2.8.0.md`, `evidencias-2.8.0/`. Retomada: `CONTINUIDADE.md`. Validação Windows: `validacao-windows.md` e `homologacao-windows.md`.
