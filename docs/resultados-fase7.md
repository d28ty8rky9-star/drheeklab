# Validação — Fase 7 / versão 2.6.0 / esquema 7

Ambiente Linux, Python 3.12.14, PySide6 6.8.3, ReportLab 4.4.4, SQLite e PyInstaller 6.12.0. Dependências fixadas em `requirements-dev.lock`; `pip check` passou. Dados temporários de QA, sem operar dados reais. Windows não executado.

## Testes

Comando final: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q -o faulthandler_timeout=20`.

Resultado: **212 passed in 21.40s**, código de saída **0**. Nenhum teste ignorado ou asserção desativada. São 191 casos anteriores e 21 novos testes de domínio/interface da Fase 7.

Casos verificados:

- Catálogo incorpora foto e preço escolhido somente dos produtos selecionados, sem custos internos; valores emitidos sobrevivem a alterações posteriores do cadastro.
- Logo configurado incorporado ao PDF; documento antigo preservado após troca da marca. Ausência identificada como documento de revisão. Imagens sintéticas de QA não representam o logo original do negócio.
- PDF financeiro preserva período, filtros, critérios e valores históricos. Filtros vazios normalizados conservam a sequência de versões. PDF de produção inclui parâmetros, custos, tentativas, inspeção individual e fotos.
- Falha na renderização desfaz registro, sequência e arquivo. PDFs emitidos são verificados por hash; backup diário não se repete e arquivo alterado bloqueia validação.
- Arquivamento/restauração de fotos, projetos e PDFs preserva arquivos e históricos. Projeto usado por OP ativa bloqueado; restauração respeita dependências. Cancelamentos financeiros não aparecem como registros revivíveis na lixeira.
- Notificações de saldo baixo, vencimentos, entrega, orçamento e manutenção. Marcar lido não movimenta dinheiro; condição resolvida encerra alerta e recorrência volta a aparecer. Botão, leitura e navegação de área exercitados pela interface.
- Auditoria filtra textos literalmente e conserva justificativa. Formulários, central de documentos e filtros financeiros exercitados pela interface.
- Backup inclui PDFs e transfere dados/arquivos para nova pasta. Banco atual corrompido pode ser recuperado preservando bytes originais em rollback. Ambiente errado e esquema mais novo rejeitados.
- Backup completo antes de atualização; falha de migração preserva esquema anterior. Falha durante cópia de restauração retorna à árvore original.
- Recuperação autentica cópia verificada e exige confirmação; resposta negativa mantém destino intacto. Falha real na abertura oferece recuperação gráfica sem exigir linha de comando.

## Aplicativo empacotado

PyInstaller gerou `dist/DrHeekLab` com dependências:

`QT_QPA_PLATFORM=offscreen .venv/bin/python -m PyInstaller --noconfirm --windowed --onedir --name DrHeekLab --paths src --collect-all drheeklab packaging/launcher.py`

Verificação do código e do executável `QT_QPA_PLATFORM=offscreen dist/DrHeekLab/DrHeekLab --self-test`: **status: passed**, **version: 2.6.0**, saída **0**. O teste usa somente pasta temporária: autenticação, PNG/logo de QA, orçamento/pedido, pagamentos/taxas/PDFs, OP/tempo/consumo, inspeção com três fotos, entrega, obrigações/aportes/caixa/CPV, CSV/Excel, relatórios/catálogo PDF, notificações/lixeira e backup/transferência. PDFs gerados são carregados pelo QtPdf; transferência preserva senha e bytes dos documentos.

Aviso Fontconfig de cache sem permissão apareceu na execução offscreen do binário, sem impedir a verificação. Capturas da central de documentos e Configurações em 1100×720/1100×700 foram inspecionadas visualmente. Verificação Linux/offscreen não equivale a homologação Windows.

## Entrega

- Código para revisão: `dist/DrHeekLab-2.6.0-source.zip`.
- Pacote Linux: `dist/DrHeekLab-2.6.0-linux.zip`; extrair a pasta inteira e executar `DrHeekLab/DrHeekLab`.
- Integridade: `dist/DrHeekLab-2.6.0-SHA256.txt`.

Arquivos de código não incluem bancos, dados/credenciais, .venv ou caches. ZIPs têm integridade verificada. Pacotes anteriores foram preservados.

Scripts PowerShell/Inno Setup e workflow Windows atualizados para 2.6.0/Fase 7. Geração de .exe/instalador e homologação Windows permanecem pendentes; roteiro em `validacao-windows.md`. Nenhum commit, push ou publicação foi realizado nesta entrega.

`install_script` e `start_skill` foram confirmados como rascunho salvo na configuração da nuvem, preservando os demais campos e incluindo a Fase 7. Salvamento não executa scripts, aplica configuração nem publica o ambiente. Revise e salve nas configurações, depois publique o ambiente; restauração em outra tarefa não foi verificada.

Importe o arquivo original PNG/JPEG do logo em Configurações antes de compartilhar documentos finais. O original mostrado na conversa não está disponível como arquivo local; nenhuma réplica foi inventada. Instruções de operação e recuperação em `fase7.md`. **Fase 8 — testes, finalização e instalador — exige autorização expressa do proprietário.**
