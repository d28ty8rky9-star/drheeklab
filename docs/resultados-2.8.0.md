# Resultados — finalização autônoma 2.8.0 / esquema 7

## Implementado e validado em Linux

Continuidade a partir de 2.7.0, sem reescrever módulos por preferência ou alterar regras comerciais. Manutenção dos 227 testes e acréscimo de 21 casos: **248 passed in 45.03s**, saída **0**, **0 falhas**, **0 ignorados** na execução Linux. JUnit e log em `evidencias-2.8.0/`. Python 3.12.14, PySide6 6.8.3, cryptography 46.0.3, cffi 2.0.0, SQLite, ReportLab/OpenPyXL e PyInstaller; instalação editável e pip check aprovados.

Correções/melhorias verificadas:

- Backup criptografado real com AES-256-GCM/scrypt; restauração/transporte com documentos, mídias, rascunhos e senha original de login.
- Senha de criptografia independente e não persistida em SQL/auditoria/argumentos/logs. Senha errada, cabeçalho/payload adulterados ou truncados bloqueiam restauração antes de substituir dados.
- Backup ZIP continua compatível. Arquivo final só entregue após verificação; disco cheio simulado limpa saída parcial própria. Arquivo existente de destino não é apagado por erro de criptografia/decriptação.
- Links simbólicos gerenciados bloqueados para impedir inclusão de arquivo externo. Backup não altera caixa, custos, estoque ou métricas financeiras.
- Processo sem interface usa trava do mesmo ambiente, deduplica diariamente e registra erro; não inicializa banco novo nem toca o outro ambiente. CLI real exercitada por subprocesso.
- Verificação pré-atualização protege TESTES/PRODUÇÃO existentes, conserva rascunhos e bloqueia ambiente aberto/banco mais novo. Atualização mantém esquema 7; migrações anteriores e falhas seguem cobertas.
- Interface cria .hbk e rejeita senha incorreta na restauração sem fechar a janela ou confirmar substituição. Diálogo identifica agendamento sem criptografia, cancelamento e erro de confirmação de senha.
- XML do Agendador conferido: usuário atual, privilégio normal, caminhos citados/escapados, sem senha, gatilhos diário/login e nova tentativa. Chamadas schtasks verificadas por simulação; execução no Agendador Windows NÃO foi validada no Linux.

## Auditoria financeira, estoque e produção

Suíte anterior preservada: aquisição versus referência, múltiplos filamentos, A1 Mini R$ 1,10/h, custo × 3, preço manual/desconto único, parcelas/centavos/taxas, aporte versus venda, caixa versus custo, compras/consumo, CPV histórico, cancelamento/crédito/reembolso/retorno, falhas/perdas/absorção e reconciliação. Serviços existentes usam transações compostas; nenhuma regra financeira foi alterada nesta revisão. Critérios e evidências em `matriz-testes.md` e testes das Fases 2–7.

Estoque/produção: consumo único, saldo desconhecido, reservas/liberação/baixa/descarte, lotes iguais/mistos, rateio, falhas/reimpressão, produção para estoque, inspeção individual/fotos/rejeição e bloqueio de entrega permanecem nos testes ativos. Aprovação dos casos executados não é prova de inexistência de qualquer defeito em todas as condições possíveis.

As oito áreas foram abertas em 1366×768, nos dois temas, usando dados temporários; capturas em `evidencias-2.8.0/`. Agendamento também inspecionado. Esses registros não equivalem a teste visual no Windows com dados reais.

## Executáveis e artefatos

PyInstaller gerou o pacote GUI Linux e verificador independente Linux, saída 0. QA do código e do GUI final: **passed**, **version 2.8.0**, saída **0**, incluindo transferência/restauração criptografada, PDFs/Excel/CSV, produção/inspeção/venda, financeiro, reinício e persistência. JSONs preservados. QA do verificador independente Linux também passou: backup verificado dos dois ambientes, bloqueio de instância aberta e de banco mais novo, com dados temporários (`preflight-linux-qa.json`). Aviso Fontconfig de cache não gravável não impediu QA offscreen.

- Código completo: `dist/DrHeekLab-2.8.0-source.zip`.
- Pacote Linux: `dist/DrHeekLab-2.8.0-linux.zip` — extrair e manter a pasta inteira; executar `DrHeekLab/DrHeekLab`. Verificador auxiliar `DrHeekLabUpdate` é Linux, para diagnóstico técnico.
- Integridade: `dist/DrHeekLab-2.8.0-SHA256.txt`.

ZIPs verificados, permissões executáveis preservadas e SHA-256 calculados. Código exclui .venv, caches, bancos/dados pessoais e segredos; inclui testes/evidências fictícias e solicitação do proprietário. Pacotes anteriores preservados. Linux não executa no Windows.

## Preparado, mas NÃO executado no Windows

PowerShell/Inno/workflow atualizados para 2.8.0: propriedades de versão, preflight independente antes da cópia de binários, backup completo e compatibilidade, bloqueio de downgrade versionado, preservação da pasta de dados/ACL existente, JUnit, QA de criptografia e checksums. Roteiro automatizado preparado para instalação/reinstalação/desinstalação, banco/mídia preservados, backup sem interface e criar/remover tarefa em runner descartável.

**Nenhum .exe/Setup Windows foi gerado. Nenhum teste Windows, tarefa schtasks real ou computador sem Python foi validado. Nenhum runner remoto foi iniciado.** O ambiente é Linux e o proprietário não autorizou push. Homologação/prontidão para uso real Windows seguem pendentes. Logo/ícone originais também não estão no checkout; suporte existe e substituição não foi inventada.

Configuração da nuvem: install_script/start_skill atualizados como rascunho para dependências e instruções 2.8.0, sem alterar campos alheios. Rascunho não executa/aplica/publica nem comprova nova tarefa. Código pode ser preservado em commit local autorizado; nenhuma publicação/push/release foi realizada. Consulte `git log` e `CONTINUIDADE.md`.

Instruções do proprietário: `finalizacao-autonoma.md`. Pendências externas: execução/homologação Windows e arquivos oficiais da marca. Não há solicitação de aprovação intermediária para continuar o desenvolvimento técnico.
