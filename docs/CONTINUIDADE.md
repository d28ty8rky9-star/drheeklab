# Ajuste adicional — ocultar baixadas no estoque atual

Listas de peças/acessórios filtram somente estados fisicamente em mãos, sem apagar dados ou movimentos. Reservadas visíveis, baixadas/descartadas ocultas, devolvidas voltam em quarentena. Correção Financeiro/Clientes anterior aprovada Windows no run38672860664. Validação: 308 testes locais na correção financeira, 10 testes específicos após filtro de estoque; suíte Windows final aprovada no run38673220952 sobre cbab1239d9ee30f97524e61bff4fad346ea5f355, pacote ignorado. Nenhum ZIP solicitado para estas mudanças. Notas seguintes históricas.

# Estado atual — correção Financeiro e saldo por cliente

Corrigidos índices visuais Financeiro4/Impressoras5 e filtros financeiros por dia local dos eventos UTC; históricos preservados. Clientes acrescenta Total vendido, Recebido bruto menos reembolsos e A receber, separados do Crédito disponível. Teste de venda enviada a prazo na virada UTC e pagamento/cancelamento. Ver docs/financeiro-clientes.md e tests/test_finance_local_date.py. Sem ZIP solicitado nesta atualização; somente código/testes/GitHub. Notas seguintes históricas.

# Última entrega — ZIP com total vendido, lucro e estoques separados

Pedido explícito atendido: dist/DrHeekLab-2.9.1-VendasLucro-Estoque-Windows.zip; run 38666818545; artifact 11943311256; código 6a8189b8c1f3cd77f18538d54014a49b383407b2. 305 testes Windows aprovados, zero falhas/erros/pulos. Compilação/instalação/preservação dados aprovadas; ZIP SHA256 igual ao GitHub, CRC e hashes executáveis verificados. Evidências docs/evidencias-vendas-total/requested-package.json. Executar installer/DrHeekLab-2.9.1-Fase8-Setup.exe, preservar C:\DrHeekLab. Avaliação manual pendente. Próximos ZIPs somente sob solicitação. Notas seguintes históricas.

# Estado atual — total da venda, lucro, marcação e estoques separados

Valor real informado é TOTAL com acessórios, sem somá-los novamente. Mínimo custos totais, sugerido produzidas +100% / compradas +30% + acessórios custo; lucro bruto total−custos, percentual somente sobre custo das peças. Seleção por caixas de marcação, independente da busca. Estoque sem Auxiliares visível (dados preservados), peças/acessórios separados, totais por categoria e geral. Filamento novo UI entra com saldo/peso completo; Valor restante diminui proporcionalmente ao consumo, sem pagamento duplicado. Antigos desconhecidos não são estimados. Versão 2.9.1/schema10. Ver docs/vendas-estoque.md, testes test_stock_totals.py/test_stock_sale_ui.py. 305 testes locais aprovados; suíte Windows aprovada no run 38665100231 (fcf16710b5979b6bb6a4839f1d31fc0986c34182), pacote ignorado. ZIP não solicitado nesta alteração; somente código/GitHub/testes. Notas seguintes históricas.

# Última entrega — ZIP solicitado com Vendas simplificada

ZIP completo Windows gerado mediante pedido: dist/DrHeekLab-2.9.1-Vendas-Windows.zip. Run 38660484911, artifact 11939141141, código 714a848cc4d2ec9b3776560c79561e8f9a2b49ae. 302 testes Windows aprovados, zero falhas/erros/pulos; compilação e verificação de instalação/preservação de dados aprovadas. SHA256 ZIP igual ao digest GitHub; CRC e hashes executáveis/instalador conferidos. Evidências docs/evidencias-vendas/requested-package.json. Extrair pasta nova, abrir installer/DrHeekLab-2.9.1-Fase8-Setup.exe. Preservar C:\DrHeekLab. Avaliação manual pendente. Próximos ZIPs somente sob pedido explícito. Notas seguintes históricas.

# Estado atual — Vendas simplificada e cálculo por origem

Implementadas abas Vendas, Orçamentos, Clientes, Contas a pagar e receber e Precificação. Nova venda: cliente, unidades exatas do estoque, detalhes históricos, produzidas +100%, compradas +30%, acessórios pelo custo. Valor real das peças editável; acessórios separados e somados ao custo. Sem despesa/pagamento automático duplicado. Schema 10/versão 2.9.1. Consulte docs/vendas-estoque.md e testes test_stock_sale*.py. Testes Windows aprovados no run 38659732134; pacote ignorado. ZIP somente mediante pedido explícito. Notas seguintes históricas.

# Última entrega — ZIP refeito após publicação do ambiente

Usuário pediu explicitamente refazer o ZIP depois de publicar o ambiente. Nova compilação completa Windows: dist/DrHeekLab-2.9.1-CadastroCompleto-Refeito-Windows.zip; run 38652867662; artifact 11935828123; código compilado 2c182cac4fb8878bb6e37e2e6b831403ba4013fe. Versão 2.9.1/schema 9, mesma ficha integrada com cálculo automático/extras/OP sem recadastro/custo único.

294 testes Windows aprovados, zero falhas/erros/pulos. Pacote e instalação/reinstalação/backup/preservação de banco e mídia/agendamento/desinstalação aprovados. SHA256 do ZIP 4408e3282cb1a993aa1a085f7e42a2c01900f32638b26410598b1f87d108008c igual ao digest do GitHub; CRC e hashes GUI/helper/Setup conferidos. Integração ProductProductionFields no construtor ProductDialog do executável confirmada via bytecode. Evidências docs/evidencias-cadastro-producao/requested-package-rebuilt*.json.

Fechar programa, extrair em pasta nova e executar installer/DrHeekLab-2.9.1-Fase8-Setup.exe; preservar C:\DrHeekLab e fazer backup antes de reinstalar. Avaliação manual do proprietário continua pendente. Esta autorização cobre ESTA nova entrega; futuros ZIPs/instaladores somente sob pedido explícito. Notas seguintes históricas.

# Última entrega — ZIP pedido com ficha completa dentro de Nova peça

Usuário pediu novo ZIP explicitamente após confirmar cálculo automático, OP sem recadastro e custo sem duplicação. Pacote COMPLETO Windows gerado: dist/DrHeekLab-2.9.1-CadastroCompleto-Windows.zip; run 38651226605; artifact 11935270883; código compilado f0a72a32d13b6d99076a6a5690211d31f43d34b2; versão 2.9.1/schema 9.

294 testes Windows aprovados, zero falhas/erros/pulos. Pacote funcional, instalação/reinstalação/backup/preservação de banco e mídia/agendamento/desinstalação aprovados. CRC do ZIP válido e SHA256 igual ao digest GitHub (702b47706d0ff261a667a275e75c02440b123caa892416577aaca33d9ff5c5c9); hashes GUI/helper/Setup conferidos. product_production_ui incluído e bytecode do construtor ProductDialog dentro do executável realmente referencia ProductProductionFields: integração confirmada, não somente presença do módulo. Evidências docs/evidencias-cadastro-producao/requested-package*.json.

Instalar: extrair ZIP em pasta nova, executar installer/DrHeekLab-2.9.1-Fase8-Setup.exe. Preservar C:\DrHeekLab (banco/fotos/documentos), fazer backup antes da reinstalação; excluir apenas pasta extraída de entrega antiga. Avaliação prática do proprietário permanece pendente.

Autorização vale para ESTA entrega. Futuras mudanças: código/testes/GitHub, sem gerar ZIP/instalador até pedido explícito. Não disparar gerar_pacote=true automaticamente. Notas seguintes históricas.

# Estado atual — correção: ficha completa dentro de Nova peça / Editar peça

Usuário mostrou a janela Editar peça e confirmou que todos os detalhes/calculadora/extras deveriam estar nela. Corrigido: ProductDialog incorpora ProductProductionFields, com filamentos múltiplos/gramas, horas, impressora, parâmetros, extras detalhados, variante, fotos e importação STL/3MF. Custo automático/readonly quando configurado, atualização imediata, sem botão Calcular. Botão superior da ficha abre o mesmo formulário completo, sem segundo cadastro de custos. Dados básicos ainda podem ser salvos como ideia sem consumo informado; ficha de custos pode ser guardada sem STL/parâmetros, que são obrigatórios para gerar OP. Fotos/arquivos/cadastro/receita salvos atomicamente com limpeza de novos arquivos em falha. Nada de estoque/Financeiro na ideia; OP aproveita receita, custo entra somente na conclusão/Estoque.

Validação: 294 testes locais aprovados, zero falhas/erros/pulos; suíte completa Windows aprovada no run 38508888418, código 9e4b7be817d10f7e9b017e03ec19d98afe8e213a. Pacote ignorado, zero artefatos.

Schema 9/version2.9.1 preservados. Não gerar ZIP automaticamente: o ZIP entregue antes desta correção contém a janela anterior. Usuário não pediu novo ZIP nesta correção. Código/testes/GitHub e capturas em docs/capturas-cadastro-producao/, detalhes docs/cadastro-producao-integrado.md. Preservar C:\DrHeekLab. Notas seguintes históricas.

# Última entrega — ZIP completo solicitado, extras e estoque em horas

Usuário pediu ZIP explicitamente. Gerado pacote Windows completo com TODAS as alterações atuais (Produção unificada/ficha, cálculo automático, aba Extras, OP simples, reconhecimento na conclusão, Estoque único/peça comprada, horas e marca oficial). ZIP local dist/DrHeekLab-2.9.1-Extras-Producao-Windows.zip; run 38506019047; artifact 11868460181; código compilado 5fd331ce9a834d79cef6b56021fc35a11e628d76; versão 2.9.1/schema 9.

289 testes Windows aprovados, zero falhas/erros/pulos; executável empacotado e instalação/reinstalação/backup/preservação de banco e mídia/agendamento/desinstalação aprovados. ZIP CRC e SHA256 iguais ao digest do GitHub; hashes GUI/helper/Setup conferidos; extras_ui, production_extras, production_recipe, time_input, migration9 e workshop_ui presentes no executável. SHA256 do ZIP 4d3abd460a0778e26a8bf30bea641976c66e2c6fe08a77428106200f94d79357. Evidências docs/evidencias-extras-producao/requested-package*.json.

Instalar: extrair ZIP em pasta nova, executar installer/DrHeekLab-2.9.1-Fase8-Setup.exe. Preservar C:\DrHeekLab (banco/fotos/documentos); excluir apenas pasta extraída da entrega anterior. Avaliação manual do proprietário continua pendente.

A autorização deste pedido vale para ESTA entrega. Próximas alterações: código/testes/GitHub; ZIP e instalador somente quando explicitamente pedidos. Não disparar gerar_pacote=true sem pedido. Notas seguintes históricas.

# Estado atual — extras detalhados em Produção, OP somente fluxo

Implementada aba Extras • argolas e acessórios na ficha de Produção. Nome, quantidade por peça, custo unitário; soma por linha e total. Prévia automática ao mudar filamentos, horas, adicionais ou extras, inclusive antes de escolher STL. Não há botão obrigatório de cálculo. Salvar continua validando arquivo/parâmetros. Extras persistidos no JSON versionado da receita, auxiliary_base separado do total; ficha antiga mantém auxiliares anteriores. OP copia ficha/extras imutáveis e multiplica o custo pela quantidade, sem solicitar os itens de novo. Cadastro de extras não movimenta materiais auxiliares/caixa. Custo reconhecido somente após conclusão e publicação no estoque.

Validação: 289 testes locais aprovados, zero falhas/erros/pulos; suíte completa Windows aprovada no run 38504392901 sobre fa06628883476f8547982ac9ed31c73fc8486605. Pacote ignorado, zero artefatos.

Sem mudança de schema (continua 9) ou versão (2.9.1). Código/GitHub, testes e capturas; ZIP/instalador somente se solicitado. Preservar dados, OPs e receitas anteriores. Veja docs/extras-producao.md, tests/test_production_extras.py e docs/evidencias-extras-producao/. Notas seguintes históricas.

# Estado atual — valor demonstrativo, peça comprada no Estoque e horas

Pedido atual implementado em 2.9.1: Valor de produção por variante selecionada, cartão e tabela; prévia da ficha atualiza em tempo real (filamentos, tempo, adicionais). Peça comprada cadastrada diretamente por Estoque → Nova peça comprada, sem selecionar produto/variante em Produção ou exigir STL/OP. Identificação interna fica no catálogo de estoque e mantém reserva, Vendas, CPV, busca e filtros Financeiro/catálogo PDF. Custos e pagamentos continuam separados.

Tempo nos formulários da peça (cadastro, ficha, OP antiga, ajuste de confirmação e calculadora) agora em horas. Banco/APIs/histórico continuam em minutos; Decimal com arredondamento para minuto inteiro. Exemplos 1,5h=90min e 0,25h=15min; rascunhos antigos convertidos na leitura. Não alterar fórmulas.

Schema 9: tabela purchased_products, migração/backup transacional; preservadas tabelas/dados existentes e snapshots de OPs. Não cadastrar peça comprada no catálogo visível da Produção. Detalhes docs/valor-producao-estoque-horas.md; evidências docs/evidencias-estoque-horas/ e capturas docs/capturas-estoque-horas/.

Validação: 284 testes locais aprovados, zero falhas/erros/pulos; 20 testes UI/fluxo repetidos após ajustes finais e aprovados. Windows suíte completa aprovada no run 38503428577 sobre 2357b31c27adb91823980836dc3870f72d3fe8f1, pacote ignorado, zero artefatos.

Somente código/testes/GitHub. Nenhum pacote solicitado nesta alteração. ZIP/instalador apenas mediante pedido explícito; os pacotes antigos não incluem alterações recentes. Preservar C:\DrHeekLab. Sem worktree. Avaliação manual do proprietário pendente. Notas seguintes históricas.

# Estado atual — ficha de Produção → OP simples → Estoque → custo no Financeiro

Usuário confirmou custo sem pagamento automático. Implementado em 2.9.1: ficha de produção por variante (arquivo, filamentos/gramas por peça, tempo por peça, auxiliares, parâmetros, custos congelados); OP mínima (quantidade, responsável, prioridade, pedido opcional); consumo confirmado sem reconhecer custo/unidades públicas antes da conclusão; inspeção com três fotos distintas e observações; reconhecimento único na primeira conclusão; Estoque único por unidade; valor atual do estoque no Financeiro. Ajuste excepcional de consumo/tempo preservado. Entrada manual de peça comprada e vendas/CPV/caixa preservados.

Banco schema 8, migração com backup/transação. OPs históricas preservam datas/tratamento anterior. OPs geradas da nova ficha, inclusive reimpressões, usam reconhecimento na conclusão. Reinspeção não duplica custo. Editar cadastro/ficha não reescreve a receita congelada de uma OP existente. Veja docs/fluxo-producao-estoque.md, tests/test_recipe_flow.py e tests/test_recipe_ui.py.

Regra vigente: código/testes/GitHub; ZIP e instalador somente quando explicitamente pedidos. Nenhum pacote novo para esta alteração. O ZIP anterior indicado abaixo continua sendo a entrega anterior e não contém este fluxo. Não apagar dados de C:\DrHeekLab. Usar checkout existente, sem worktree. Avaliação prática do proprietário segue pendente.

Validação desta alteração: 266 testes locais aprovados, 0 falhas/erros/pulos; suíte completa Windows aprovada no run 38502081384, código b4799b2c94470531d454c3913853b4ce1a4b6328. Pacote ignorado, zero artefatos. Evidências em docs/evidencias-fluxo-producao/. Capturas reais com dados temporários: docs/capturas-fluxo-producao/. As notas seguintes são históricas.

# Última entrega — ZIP solicitado da Produção unificada

Usuário pediu explicitamente ZIP após a união de Produtos/Produção. Pacote completo gerado e verificado: dist/DrHeekLab-2.9.1-ProducaoUnificada-Windows.zip; run 38483874439, artifact 11858064343, código compilado 4486ad5795891813f7b066d0b65ab9b3dcf71074. Windows 258 testes aprovados, 0 falhas/erros/pulos; executáveis e instalação/reinstalação/backup/preservação/agendamento/desinstalação aprovados. Hashes e integridade do ZIP conferidos; módulo workshop_ui dentro do executável. Esta entrega já contém a tela unificada e sete áreas. Nome Dr. Heek Lab, versão 2.9.1.

Regra continua: ZIP/instalador somente mediante pedido explícito. Este pedido autorizou somente esta entrega. Futuras alterações: implementar/testar/GitHub; não empacotar automaticamente. Preservar C:\DrHeekLab. Avaliação manual do proprietário continua pendente. Notas seguintes históricas.

# Estado atual — Produção unificada; pacotes somente a pedido

Produtos e Produção agora são uma área única Produção, em uma tela com catálogo à esquerda e fila/inspeção à direita. Selecionar peça → Produzir esta peça abre formulário preenchido com variante, arquivo preferencial e recomendações; ficha de variantes/fotos/STL/3MF permanece acessível. Dados, schema, custos, estoque e inspeção preservados. Variante arquivada selecionada é bloqueada, sem substituir por outra. Menu com sete áreas e busca/navegação ajustadas.

257 testes locais completos e três testes finais de fluxo aprovados. Windows run 38483313429: testes aprovados sobre 2ebc0b40cf40b7bc29eaa166dc0bfa8e932a823a. Pacote ignorado e zero artefatos criados. Nenhum ZIP/instalador gerado. Relatório docs/producao-unificada.md e capturas docs/capturas-producao-unificada/. Código no GitHub; o último instalador entregue mantém a interface anterior.

PREFERÊNCIA ATUAL, que substitui a antiga: implementar/testar/enviar alterações ao GitHub, mas somente gerar ZIP ou instalador quando o usuário pedir explicitamente. Workflow push/PR apenas testa; pacote só via workflow_dispatch com gerar_pacote=true e pedido explícito. Não disparar esse input sem autorização. Usar checkout existente; preservar C:\DrHeekLab e dados, versões e documentos históricos. Versão do código continua 2.9.1 em desenvolvimento.

Notas seguintes são históricas.

# Nome atual — Dr. Heek Lab, versão 2.9.1

Pedido de 13/10/2026: nome do produto Dr. Heek Lab, sem “2.0”; versão continua 2.9.1. Nome atualizado em interface, instalador, propriedades do executável e novos documentos. PDFs e dados históricos preservados. A cada alteração, o usuário exige ZIP completo para reinstalar, sem copiar modificações para uma pasta antiga. Preservar C:\DrHeekLab (dados), excluir somente a pasta extraída da entrega anterior. LEIA-ME.txt incluído no pacote.

Validação: 65 testes locais relacionados aprovados; 255 testes Windows aprovados, zero falhas/erros/pulos. Instalação/reinstalação/backup/preservação/agendamento/desinstalação aprovados. Run 38403682558; build a36711e0d22e9a743695cdc3bb2e1e8a73b1fa51; artifact 11817081703 (DrHeekLab-Windows-2.9.1-NomeAtualizado). Nome no metadata do GUI e hashes verificados. ZIP completo local: dist/DrHeekLab-2.9.1-NomeAtualizado-Windows.zip. Notas seguintes históricas.

# Estado atual — marca oficial e revisão final 2.9.1

Logotipo fornecido no ZIP incorporado no canto superior esquerdo, nome e versão abaixo; oito ícones da folha original no menu. Início sem os blocos inferiores/alerta amarelo; informações e anotações preservadas em Configurações → Sobre. Ícone oficial incorporado no executável, instalador e janela. Menu com rolagem em janelas menores. Nenhuma regra, fórmula ou migração alterada.

Linux 255 testes aprovados; Windows 255 aprovados e instalação/reinstalação/backup/preservação/agendamento/desinstalação aprovados. Run 38319542522, commit compilado 09423e0ea372a16911a2c766348d688b9ec08dfc, artifact 11779025415 (DrHeekLab-Windows-2.9.1). Hashes verificados, sete frames do ICO presentes no GUI e Setup e três assets com hashes iguais aos do source. Installer local dist/windows-2.9.1/installer/DrHeekLab-2.9.1-Fase8-Setup.exe. A pendência de arquivo oficial foi resolvida. Avaliação prática do proprietário continua pendente.

Veja docs/ajustes-marca-2.9.1.md, docs/capturas-2.9.1/ e docs/evidencias-2.9.1/. Notas seguintes são históricas.

# Estado atual — modernização visual 2.9.0

As oito áreas foram modernizadas com tema compartilhado, cartões, botões/ícones/tabelas/formulários padronizados, filtros, gráficos sobre dados reais, galeria/tabela sincronizada, progresso por peças aprovadas e configurações por assunto. Nenhuma fórmula, migração ou regra de negócio foi alterada.

Linux: 254 testes aprovados. Windows: 254 testes aprovados, pacote e instalação/reinstalação/backup/preservação/agendamento/desinstalação aprovados. Run 38306782123, código compilado c37b967a04fd227771a74cd86dcee5aec31659f3, artifact 11772568668 (DrHeekLab-Windows-2.9.0). Installer local dist/windows-2.9.0/installer/DrHeekLab-2.9.0-Fase8-Setup.exe; hashes verificados. Avaliação manual do proprietário e importação do logotipo oficial permanecem pendentes. As capturas usam somente dados demonstrativos temporários.

Veja docs/modernizacao-visual-2.9.0.md e docs/evidencias-2.9.0/. Os registros seguintes são históricos.

## Atualização mais recente — Windows 2.8.1

Instalador gerado e validação automatizada Windows aprovada no run 38299222677 / commit74ae16b: 250 testes, zero falhas/erros/ignorados. Artefatos e hashes conferidos em dist/windows-2.8.1. Correções SQLite e QtPdf implementadas. Push e execução para homologação foram autorizados; release/mudança de visibilidade não. Avaliação prática do proprietário e marca oficial permanecem pendentes. Leia resultados-windows-2.8.1.md; estados anteriores abaixo são históricos.

# Continuidade — Dr. Heek Lab 2.8.0

## Estado preservado

- Checkout: `/workspace/drheeklab`; versão 2.8.0, esquema 7.
- Autonomia técnica concedida; não exigir nova aprovação por fase. Preservar regras e dados, não recomeçar o projeto.
- Implementados backup AES-GCM/scrypt, suporte .hbk/ZIP, agendamento Windows assistido, CLI de backup com trava, preflight de atualização e proteção de saída parcial/symlinks.
- Suíte Linux: 248 testes aprovados, saída 0. QA do código e binário GUI Linux aprovado, incluindo criptografia/restauração. Executável de preflight Linux gerado para verificar o mesmo código independentemente do pacote GUI.
- Pip check aprovado. Dependências fixadas, incluindo cryptography/cffi/pycparser. Documentação e evidências preservadas.
- Preparar/preservar commit local autorizado pelo proprietário. Não fazer push, release ou publicação externa sem autorização específica.

## Comandos reproduzíveis

```bash
cd /workspace/drheeklab
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/python -m pip check
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q -o faulthandler_timeout=20
QT_QPA_PLATFORM=offscreen .venv/bin/python -m drheeklab --self-test --self-test-report /tmp/qa.json
QT_QPA_PLATFORM=offscreen .venv/bin/python -m PyInstaller --noconfirm --clean --windowed --onedir --name DrHeekLab --paths src --collect-all drheeklab packaging/launcher.py
.venv/bin/python -m PyInstaller --noconfirm --clean --onefile --console --name DrHeekLabUpdate --paths src packaging/update_preflight.py
QT_QPA_PLATFORM=offscreen dist/DrHeekLab/DrHeekLab --self-test --self-test-report /tmp/qa-binario.json
```

Não repetir testes/builds já aprovados sem alteração, falha ou motivo novo. Dados de QA sempre temporários, sem abrir PRODUÇÃO real. Não usar credenciais em texto/argumentos.

## Pendências externas

1. Disponibilizar Windows ou autorizar envio do código ao GitHub para executar `.github/workflows/windows.yml`. Nenhum push/runner/Windows build ocorreu; ambiente atual é Linux.
2. Gerar executável/instalador Windows, investigar qualquer falha real e repetir somente verificações afetadas. Não confundir Linux ELF com .exe Windows.
3. Homologar usuário comum, máquina sem Python, atalhos, resoluções, tarefas com aplicativo fechado, criptografia, atualização/preflight, mídias e erros de disco/permissão. Preencher evidências, não apenas marcar scripts como aprovados.
4. Importar logo PNG/JPEG e ícone .ico oficiais quando fornecidos. Ausência não bloqueia desenvolvimento; não inventar marca.

Rascunho de nuvem não equivale a publicação, execução automática ou restauração comprovada em nova tarefa. Código/pacotes locais permanecem disponíveis; consultar `git log` para commits locais. Não declarar o sistema Windows pronto até cumprir os critérios da solicitação.
