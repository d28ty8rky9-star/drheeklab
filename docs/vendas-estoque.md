# Vendas por unidade do estoque — 2.9.1

Abas: Vendas, Orçamentos, Clientes, Contas a pagar e receber e Precificação. A navegação Pedidos foi retirada; histórico, pagamentos, entregas, encomendas e documentos continuam disponíveis em Vendas.

Nova venda permite escolher cliente e unidades reais disponíveis. Peça produzida: custo unitário histórico +100%; peça comprada: +30%; acessórios: custo, sem acréscimo em ambos os casos. O formulário mostra o detalhamento registrado da OP, horas do lote, custo de máquina, filamentos/gramas/custos e extras. Dados de lote são identificados como lote; nenhuma informação ausente é inventada para compras antigas. O valor real editável corresponde ao TOTAL da venda, com acessórios incluídos. Preço mínimo = todos os custos; sugerido = preço das peças com sua margem + acessórios pelo custo. Lucro bruto = total vendido − todos os custos; percentual sobre o custo das peças, excluindo acessórios do denominador. A receita dos acessórios permanece fixada no custo, e a diferença de preço é atribuída às peças. Seleção explícita por caixas de marcação, preservadas durante a busca.

Estoque → Acessórios oferece cadastro direto e revisão para disponibilizar unidades. Filtros na seleção da venda excluem linhas ocultas do total. Salvar reserva exatamente as unidades selecionadas, cria venda/recebível/documento, sem pagamento automático ou nova despesa de produção. Pagamento é explícito; CPV ocorre na entrega, com reversão existente em devolução. Cadastro de acessório não registra pagamento automático.

Contas a pagar e receber usa as tabelas e serviços existentes: cadastro de obrigação, pagamento de parcela e detalhes/recebimento da venda. A gestão completa de cancelamentos/comprovantes continua no Financeiro. Encomendas e orçamentos anteriores mantêm seus fluxos existentes.

Schema 10 acrescenta apenas accessory_products; migrações e históricos preservados. Versão permanece 2.9.1. Testes locais: 302 aprovados; após refinamento de filtros/revisão/retorno, os 7 testes específicos passaram. Capturas reais com dados de demonstração: capturas-vendas/abas-vendas.png e nova-venda.png.

Validação automática Windows aprovada no run 38659732134, commit d7e3c60a5bbd8f531ed7595ac7d004260e150ed4. Etapa de pacote ignorada conforme preferência do usuário.

Nenhum ZIP ou instalador gerado neste pedido. Os pacotes anteriores não incluem esta atualização. Avaliação visual manual no computador do usuário ainda pendente.


Atualização: Auxiliares retirado da navegação (dados históricos mantidos). Estoque de peças e Acessórios separados, com quantidade e custo dos itens fisicamente em mãos (disponíveis, reservados, a verificar e uso pessoal). Vendidos e descartados não entram nos totais. Filamentos valorados proporcionalmente ao saldo conhecido/peso inicial e aquisição; dados insuficientes ficam explícitos, sem estimativa pelo preço de referência. Totais por categoria e geral nos cartões. Preço mínimo é custo, não inclui taxas de venda futuras. Lucro mostrado é bruto antes de taxas; a conciliação financeira existente continua considerando pagamentos/taxas reais.

Filamento novo na interface exige peso inicial e entra com esse saldo integral e valor total da compra. Campo de saldo segue o peso inicial, sem edição nesta criação; cadastros antigos continuam editáveis/auditados e podem manter saldo desconhecido. Tabela acrescenta Valor restante, calculado pelo custo de compra proporcional ao saldo. Produção confirmada, perdas e ajustes atualizam o valor automaticamente sem lançamento de caixa adicional.

Validação desta atualização: 305 testes locais aprovados, zero falhas/erros/pulos. Capturas: capturas-vendas/estoque-separado.png e nova-venda-total-lucro.png.

Validação Windows aprovada no run 38665100231 sobre fcf16710b5979b6bb6a4839f1d31fc0986c34182; pacote ignorado e zero artefatos.

Listas Estoque de peças/Acessórios mostram somente unidades fisicamente em mãos (disponíveis, reservadas, quarentena, uso pessoal). Baixadas e descartadas continuam nos registros de origem, Movimentos, Vendas/Financeiro e Perdas, mas saem das listas atuais. Devolução física as traz de volta em quarentena sem alterar o custo. Reservadas continuam visíveis até a baixa real, inclusive se já quitadas.
