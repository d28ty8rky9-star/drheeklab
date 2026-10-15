# Vendas por unidade do estoque — 2.9.1

Abas: Vendas, Orçamentos, Clientes, Contas a pagar e receber e Precificação. A navegação Pedidos foi retirada; histórico, pagamentos, entregas, encomendas e documentos continuam disponíveis em Vendas.

Nova venda permite escolher cliente e unidades reais disponíveis. Peça produzida: custo unitário histórico +100%; peça comprada: +30%; acessórios: custo, sem acréscimo em ambos os casos. O formulário mostra o detalhamento registrado da OP, horas do lote, custo de máquina, filamentos/gramas/custos e extras. Dados de lote são identificados como lote; nenhuma informação ausente é inventada para compras antigas. O valor real editável corresponde às peças; acessórios são somados pelo custo fixo.

Estoque → Acessórios oferece cadastro direto e revisão para disponibilizar unidades. Filtros na seleção da venda excluem linhas ocultas do total. Salvar reserva exatamente as unidades selecionadas, cria venda/recebível/documento, sem pagamento automático ou nova despesa de produção. Pagamento é explícito; CPV ocorre na entrega, com reversão existente em devolução. Cadastro de acessório não registra pagamento automático.

Contas a pagar e receber usa as tabelas e serviços existentes: cadastro de obrigação, pagamento de parcela e detalhes/recebimento da venda. A gestão completa de cancelamentos/comprovantes continua no Financeiro. Encomendas e orçamentos anteriores mantêm seus fluxos existentes.

Schema 10 acrescenta apenas accessory_products; migrações e históricos preservados. Versão permanece 2.9.1. Testes locais: 302 aprovados; após refinamento de filtros/revisão/retorno, os 7 testes específicos passaram. Capturas reais com dados de demonstração: capturas-vendas/abas-vendas.png e nova-venda.png.

Validação automática Windows aprovada no run 38659732134, commit d7e3c60a5bbd8f531ed7595ac7d004260e150ed4. Etapa de pacote ignorada conforme preferência do usuário.

Nenhum ZIP ou instalador gerado neste pedido. Os pacotes anteriores não incluem esta atualização. Avaliação visual manual no computador do usuário ainda pendente.
