# Validação — Fase 4 / versão 2.3.0 / esquema 4

Linux, Python 3.12.14, PySide6 6.8.3, ReportLab 4.4.4 e pytest 8.3.5. Dados de testes temporários; nenhum banco de produção foi utilizado.

## Evidências

**128 testes passaram** em `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q -o faulthandler_timeout=20`, incluindo regressões das Fases 1–3.

- Clientes: validação, edição/lixeira, histórico e snapshots antigos de nome/contatos preservados.
- Orçamento: validade padrão sete dias, vazio/rejeitado/vencido, múltiplos itens e frete, nenhum efeito em caixa/receita/estoque antes da aprovação.
- Conversão: cópia sem redigitar, preços preservados, reserva única e rollback completo se faltar estoque; não converte duas vezes.
- Pagamentos: parcial/integral, taxas e líquido, saldo pelo bruto, alocação FIFO aos itens seguida de frete, alocação e reconciliação de parcelas.
- Parcelas: centavos distribuídos exatamente, calendário de fim de mês, atrasos/saldos/recebimentos separados. Interface permite entrada + parcelas do saldo e valores/datas desiguais editáveis.
- Recebimento inválido/futuro/acima do saldo e operação duplicada não deixam pagamento/PDF adicional.
- Documentos: pypdf lê os PDFs emitidos, verifica valores, cliente, saldo/QUITADO e ausência de custos internos/desconto automático. PDFs longos dividem páginas; aprovação/rejeição gera versões novas preservando originais. Taxas internas não são mostradas ao cliente.
- Falha de geração de PDF reverte pagamento/parcelas e não deixa arquivos novos. Falha de entrada em evento composto reverte pedido, reservas e PDF, sem commit antecipado do estoque.
- Cancelamentos: reembolso/crédito/retenção somam o já pago/aplicado; liberam reservas ativas, preservam custos/pagamentos/histórico, não repetem reembolso, zeram saldo exigível sem falsificar quitação.
- Crédito: compra futura aplica saldo sem novo caixa, não permite reembolso de dinheiro que só foi crédito. Reposição de crédito ao cancelar conserva o saldo do cliente.
- Entregas: estoque baixado uma vez, envio e entrega posterior com rastreio, retirada direta, comprovante opcional e saldo pendente mantido. Estoque recusa processar reservas vinculadas a pedidos fora de Vendas.
- Retorno físico pós-cancelamento: mantém peça/custo original, exige confirmação e nova verificação, bloqueia retorno duplicado; não inventa retorno automático ao cancelar.
- Cálculo/consumo incorrido sobrevive ao cancelamento; produção concluída pode entrar em estoque sem novo consumo/horas/custo de fabricação.
- Anexos personalizados são copiados, vinculados e mantidos mesmo sem original externo; orçamento convertido mantém a referência.
- Backup/restauração preserva pedidos, parcelas, pagamentos, crédito, PDFs, anexos e estoque. Migração real de esquema 3 para 4 conserva senha e peças; backups antigos continuam restauráveis.
- Qt offscreen: formulários de cliente/orçamento/aprovação/pedido/parcelas/pagamento/cancelamento/entrega/retorno, rascunho recuperado, oito áreas e indicadores integrados.

## Pacote e ambiente

Instalação editável e dependências fixadas atualizadas para 2.3.0; `pip check` não encontrou incompatibilidades. PyInstaller gerou `dist/DrHeekLab`, com suas dependências.

**O executável congelado Linux passou em `--self-test`**, exercitando autenticação, codec PNG/logo temporário de QA, orçamento → pedido, pagamentos parciais/taxas, três versões de comprovante e baixa de estoque. Tudo ocorre em diretório descartável, sem dados do usuário. Essa é validação funcional do pacote; a interface gráfica completa empacotada não foi automatizada com cliques.

Inspeção visual Qt offscreen de Vendas/Pedidos/Detalhes e redimensionamento 1100×700 realizada. Não equivale à homologação visual Windows. Pacote de código completo para revisão em `dist/DrHeekLab-2.3.0-source.zip`; não é instalador e não inclui dados/credenciais do usuário, .venv ou binário Windows.

## Pendências declaradas

- .exe/instalador Windows: scripts atualizados com bloqueio por pytest e teste funcional do pacote, mas não executados/homologados neste Linux. Validar no Windows sem Python com `validacao-windows.md`.
- Logo/ícone oficial: arquivo original ainda precisa ser importado/configurado. PDFs mostram placeholder explícito até isso acontecer; a imagem de QA é descartada e não substitui a marca.
- OPs, fila, qualidade formal com três fotos, reimpressões e lotes completos dependem da Fase 5. Acompanhamento nesta fase usa cálculos e peças.
- Financeiro completo/despesas/contas a pagar/relatórios e demais Fases 6–8 não foram iniciados. Os indicadores desta fase não são o fluxo de caixa completo do negócio.
- Sem integração bancária ou emissão fiscal: registrar pagamento/reembolso é registro local do fato informado, não transferência de dinheiro. A aplicação continua offline.

`install_script` e `start_skill` foram atualizados e salvos no rascunho do ambiente. Salvar o rascunho não o publicou, não aplicou alterações a outras tarefas e não comprova restauração em nova máquina. Revise e salve as configurações e publique quando desejar preservar esta preparação.

A Fase 5 aguarda aprovação expressa do proprietário.
