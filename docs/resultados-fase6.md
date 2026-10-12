# Validação — Fase 6 / versão 2.5.0 / esquema 6

Ambiente Linux, Python 3.12.14, PySide6 6.8.3, SQLite, OpenPyXL 3.1.5 e et_xmlfile 2.0.0. Dependências fixadas em `requirements-dev.lock`. Dados temporários de QA, sem operar dados reais. Windows não executado.

## Testes

Comando final: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q -o faulthandler_timeout=20`.

Resultado: **191 passed in 18.41s**, código de saída **0**. Nenhum teste ignorado ou asserção desativada. São 160 testes anteriores e 31 novos casos financeiros/interface.

Casos verificados:

- Separação venda/recebimento/CPV/caixa, aporte/retirada, taxas, contas a receber/pagar, descontos históricos e ticket médio.
- Contas de R$ 10,01 em três parcelas conservam centavos; edição das parcelas na interface, pagamento parcial, atraso, excesso/futuro bloqueado e cancelamento somente sem pagamento/entrada de estoque.
- Categorias editáveis/arquiváveis com tratamento congelado nas contas antigas. Compra de material continua após renomear categoria.
- Estorno do proprietário preserva original, cria contraparte e bloqueia repetição. Aporte não aumenta vendido; retirada não aumenta despesas operacionais.
- Compra integrada de carretel/auxiliar com conta/pagamento atômicos; erro de parcela ou comprovante desfaz todo o conjunto. Vínculo de carretel existente preserva saldo. Repetição de compra/pagamento não duplica saldo/caixa.
- Compra e consumo: saída financeira única de compra; confirmação de material/horas registra custo sem nova saída de caixa. Produzir para estoque não vende.
- CPV conserva custo da baixa física histórica, preservando preços e descrições após alterações de catálogo. Captura repetida não duplica CPV.
- Crédito do cliente quita dívida sem novo caixa. Cancelamento preserva CPV sem retorno; retorno físico reverte o custo original.
- Falha parcial de OP entra no custo das boas sem duplicação. Pagamento de manutenção aparece no caixa/despesas efetivas, separado da reserva apropriada no custo.
- Tentativa totalmente perdida afeta resultado sem caixa extra. Reimpressão em nova OP mantém custo perdido da origem junto ao CPV novo; retry na mesma OP reverte a perda quando absorvida no custo físico, evitando somá-la novamente ao CPV.
- Perda de material em estoque baixa custo existente sem saída de caixa. Descarte misto filtrado atribui somente quantidade/custo do produto correspondente.
- Saldos incluem obrigações anteriores até a data final; abertura/fluxo/fechamento de caixa conferidos. Eventos futuros artificialmente inseridos no teste não entram no histórico até a data final.
- Filtros por cliente, produto, impressora e situação financeira; caixa geral permanece consolidado e identificado assim. Item produzido em duas impressoras com recebimento de um centavo conserva recebimento e dívida nos rateios.
- Reconciliação detecta divergência artificial de líquido de pagamento; conferência de origem/custos/alocações/contas/caixa não assume integridade sem verificar.
- Comprovante PDF real, cópia gerenciada, hash, backup completo e recuperação de arquivo alterado. Imagem inválida impede pagamento/compra.
- Excel reaberto por OpenPyXL com abas completas, textos literais sem fórmulas; CSV UTF-8 preserva valores e neutraliza descrições de fórmula. Exportação por botões reais da interface também verificada.
- Migração 5 → 6 preserva rascunho/registros, cria backup anterior e mantém integridade de vínculos; teste da migração 4 passou a usar a versão atual do esquema.

A limpeza de widgets Qt passou a ocorrer após cada teste, preservando a QApplication compartilhada. Evita finalizar widgets nativos no encerramento e aplicar temas em janelas ocultas de testes anteriores. A execução final encerrou normalmente. Nenhum fluxo foi substituído por teste trivial.

## Aplicativo empacotado

PyInstaller gerou `dist/DrHeekLab` com dependências:

`QT_QPA_PLATFORM=offscreen .venv/bin/python -m PyInstaller --noconfirm --windowed --onedir --name DrHeekLab --paths src --collect-all drheeklab packaging/launcher.py`

`QT_QPA_PLATFORM=offscreen dist/DrHeekLab/DrHeekLab --self-test` usa somente pasta temporária e valida autenticação, PNG/logo de QA, orçamento/pedido, pagamentos/taxas/PDFs, OP/tempo/consumo, três fotos de inspeção, entrega, contas/aporte/CPV/caixa/reconciliação, comprovante PDF e exportação/reabertura de CSV/Excel. Resultado final: `status: passed`, `version: 2.5.0`, saída **0**. Imagens de QA não são o logo nem fotos reais do negócio.

`pip check`: nenhuma dependência incompatível. Capturas Qt offscreen do Financeiro e conta a pagar, em 1100×700/580×650, inspecionadas visualmente; não equivalem a homologação Windows.

## Entrega

- Código para revisão: `dist/DrHeekLab-2.5.0-source.zip`.
- Pacote de teste Linux: `dist/DrHeekLab-2.5.0-linux.zip`; extrair a pasta inteira e executar `DrHeekLab/DrHeekLab`.
- Integridade: `dist/DrHeekLab-2.5.0-SHA256.txt`.

Arquivos de código não incluem bancos, dados/credenciais, .venv ou caches. ZIPs têm integridade verificada. Não são instalador Windows.

`packaging/build-windows.ps1`, Inno Setup e workflow Windows atualizados para 2.5.0/Fase 6. .exe/instalador e homologação Windows permanecem pendentes; roteiro em `validacao-windows.md`. Nenhum commit, push ou publicação foi realizado nesta entrega.

Configuração da nuvem: `install_script` e `start_skill` salvos como rascunho, incluindo dependências Excel, testes, critérios financeiros e início da Fase 6. Não foram publicados nem aplicados automaticamente pelo salvamento; revise e publique nas configurações do ambiente.

Critérios/limites de período, CPV, classificação de despesas, perdas/absorção e filtros estão em `fase6.md` e na própria tela. Fase 7 permanece pendente de autorização expressa do proprietário.
