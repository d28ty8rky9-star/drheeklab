# Validação — Fase 8 / 2.7.0 / esquema 7

Finalização autorizada e implementada no ambiente Linux. **A Fase 8 ainda não está concluída para uso real no Windows:** geração e homologação do instalador, máquina sem Python e identidade com ícone oficial permanecem pendentes.

## Execução final

Ambiente Linux, Python 3.12.14, PySide6 6.8.3, ReportLab 4.4.4, OpenPyXL 3.1.5, PyInstaller 6.12.0 e SQLite. Dependências fixadas no lock; instalação editável 2.7.0 e `pip check` aprovados. Não há novas dependências nesta fase.

`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q -o faulthandler_timeout=20`

Resultado final: **227 passed in 31.21s**, saída **0**, sem testes ignorados ou asserções desativadas. São os 212 casos anteriores e 15 casos novos parametrizados da finalização. Log preservado em `evidencias-fase8/pytest-linux.txt`. Matriz dos critérios financeiros/estoque/produção/atualização em `matriz-testes.md`.

- Esquemas reais 1, 2, 3, 4, 5 e 6 migrados para 7. Senha, tema e rascunhos preservados; custo horário editado não substituído por padrão; integridade SQLite e FKs verificadas. ZIP completo anterior e snapshot do esquema original conferidos.
- QA integrado produz relatório JSON com status/versão e usa dados exclusivamente temporários. Falha simulada substitui resultado antigo passed por failed e retorna 1; argumentos que apontariam dados do usuário são recusados.
- Busca global localiza os sete tipos, nomes/códigos/telefone, trata Unicode e `%`/aspas literalmente, inclui histórico arquivado identificado e não escreve dados. Navegação da seleção à área exercitada.
- Sobre mostra histórico empacotado e versão atual. `docs/CHANGELOG.md` e a cópia empacotada estão sincronizados.
- Tela inicial em 1100×700 tem rolagem e preserva cartões/logo/anotações; oito áreas mantidas. Capturas claro/escuro e busca inspecionadas, em `evidencias-fase8/`. Logo ausente identificado; nenhuma marca fictícia criada.

Durante a revisão visual, o novo atalho deixou conteúdo comprimido no início; corrigido com rolagem e alturas mínimas, seguido de teste e nova execução da suíte. O teste anterior de recuperação gráfica passou a usar a QApplication já existente, mantendo suas verificações de autenticação, confirmação e recuperação de banco corrompido.

## Pacote Linux

Build final PyInstaller, saída 0:

`QT_QPA_PLATFORM=offscreen .venv/bin/python -m PyInstaller --noconfirm --clean --windowed --onedir --name DrHeekLab --paths src --collect-all drheeklab packaging/launcher.py`

QA do código e do binário final, saída **0**, **status passed**, **version 2.7.0**:

`QT_QPA_PLATFORM=offscreen dist/DrHeekLab/DrHeekLab --self-test --self-test-report /tmp/drheeklab-phase8-binary-qa.json`

JSONs preservados em `evidencias-fase8/codigo-qa.json` e `binario-linux-qa.json`. Teste integrado: autenticação, imagens PNG de QA, venda/pagamentos/taxas, PDFs versionados, OP/consumo/tempo, inspeção individual com três fotos, baixa física, obrigações/aportes/caixa/CPV, reconciliação, reabertura de CSV/Excel, relatórios/catálogo PDF carregados pelo QtPdf, lixeira/notificações, fechamento/reabertura com senha/tema/rascunho/financeiro/documentos preservados e transferência por backup verificado.

O aviso Fontconfig de cache não gravável apareceu no Linux offscreen, sem impedir o teste. Histórico offline e módulo de busca presentes no pacote. Dados temporários e imagens sintéticas não representam fotos/logo reais do negócio.

## Entrega e integridade

- Revisão completa: `dist/DrHeekLab-2.7.0-source.zip`.
- Executável Linux: `dist/DrHeekLab-2.7.0-linux.zip`; extrair e manter a pasta inteira `DrHeekLab`, executar `DrHeekLab/DrHeekLab`.
- SHA-256: `dist/DrHeekLab-2.7.0-SHA256.txt`.

ZIPs verificados por leitura/CRC; permissões executáveis preservadas no ZIP Linux. Código inclui documentação, evidências de QA fictício, testes e scripts; exclui bancos/dados pessoais/credenciais, .venv e caches. Pacotes anteriores preservados. Binário Linux não executa no Windows.

## Windows e ambiente da nuvem

PowerShell, Inno Setup e workflow preparados para 2.7.0/Fase 8. Build bloqueia instalador se dependências, suíte ou QA com JSON/versão/persistência falharem; gera hash do Setup. Workflow também prepara compilador e testa instalação/reinstalação, binário instalado e desinstalação em runner descartável, conferindo preservação de sentinela na pasta permanente. Script restrito a CI Windows descartável.

**Esses scripts e workflow não foram executados neste Linux. Nenhum .exe/Setup Windows foi gerado, nenhum runner foi disparado e nenhum computador sem Python foi homologado.** Ícone oficial `.ico` e logo original PNG/JPEG ainda precisam ser fornecidos/importados; não foram inventados. Roteiro e formulário em `validacao-windows.md` e `homologacao-windows.md`.

`install_script` e `start_skill` confirmados como rascunho salvo da nuvem, incluindo autorização da Fase 8 e pendências Windows; demais campos preservados. Salvamento não executa/aplica/publica a configuração: revise e salve nas configurações, depois publique o ambiente. Não houve commit, push ou publicação nesta sessão; restauração em nova tarefa não foi verificada.

Manual final em `manual.md` e `fase8.md`. Lançamento real Windows depende da homologação pendente e aprovação do proprietário; esta entrega é candidata à homologação, não anúncio de sistema Windows pronto.
