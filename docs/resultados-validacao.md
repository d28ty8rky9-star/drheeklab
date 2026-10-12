# Evidências da Fase 1

Registro histórico da entrega inicial. A versão atual é 2.1.0; resultados atuais estão em `resultados-fase2.md`.

Ambiente utilizado: Linux, Python 3.12.14, PySide6 6.8.3, pytest 8.3.5.

- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q`: **17 testes passaram**.
- Login Qt: criação com confirmação, recusa de senha incorreta, autenticação correta.
- Interface Qt: janela aberta em modo offscreen, oito botões navegáveis, tema e menu persistentes, rascunho recuperado após reabrir.
- Segurança: hash salgado, alteração de senha, limitação de tentativas, ausência de senha em texto no banco e auditoria.
- Armazenamento: pastas, bancos e preferências independentes, transação revertida ao falhar auditoria.
- Migrações: inicialização idempotente, recusa de esquema mais recente, atualização preservando registros e falha com rollback e backup íntegro. As migrações de versões futuras foram exercitadas com esquema de teste; o esquema real atual é versão 1.
- Backup: snapshot SQLite e arquivo vinculado, integridade/checksum, restauração, recusa de outro ambiente, corrupção e caminho inseguro, uma execução diária.
- Trava de instância: segundo bloqueio no mesmo arquivo recusado, liberação permite novo bloqueio.
- Dependências fixadas: instalação repetida com requirements-dev.lock e instalação editável sem resolução extra concluídas.
- PyInstaller: pacote Linux gerado em `dist/DrHeekLab`, incluindo dependências. Use a pasta inteira, não apenas o binário.
- Pacote Linux: `--help` retornou sucesso; inicialização Qt offscreen permaneceu no login, criou banco com esquema 1, sem usuário padrão, preferências e trava. Processo encerrado após essa verificação. O fluxo autenticado completo foi testado no código pelo pytest, não automatizado no pacote congelado.

## Não executado / limitações

- Geração de aplicativo .exe e instalador Windows: scripts preparados, **não executados**. Não há Windows nem Wine neste ambiente. O workflow Windows também não foi executado.
- Homologação em Windows sem Python, atalhos, reinstalação/desinstalação, atualizações empacotadas, ícone oficial e diferentes resoluções: pendentes conforme checklist.
- Logo original: imagem da conversa não está disponível como arquivo no checkout. Importação PNG/JPEG funcional; espaço reservado é explícito até importar o original.
- Fases 2–8: não implementadas. Busca global, notificações comerciais, PDFs, estoque, produção e financeiro permanecem pendentes.
- Não há criptografia de arquivos nem recuperação de senha. Backup diário depende de aplicativo aberto; restauração pode precisar de recuperação manual da pasta rollback se houver interrupção de energia durante a substituição de arquivos.

Nenhuma validação de comportamento comercial das fases futuras foi alegada. Esta entrega precisa da validação do proprietário e da homologação Windows antes de uso real e avanço da fase.
