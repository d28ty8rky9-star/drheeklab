# Venda enviada a prazo em Financeiro e Clientes

Corrigidos os índices de atualização dos cartões: Financeiro no índice4 e Impressoras no5. Tabelas e cartões agora acompanham a atualização real da página, sem precisar passar por Estoque.

Relatórios financeiros convertem os timestamps UTC imutáveis para a data local do computador, como os filtros de data da interface. Exemplo UTC15/10 01h = 14/10 22h em UTC−3: venda já aparece no fechamento do dia14. Contas a receber, reconhecimento comercial, produção e cancelamentos usam a mesma conversão. Datas efetivas explicitamente informadas de pagamentos e obrigações permanecem intactas. Custos/retornos antigos são projetados pela data local do evento original sem reescrever seus registros históricos ou duplicar custos.

Clientes mostra Total vendido, Recebido bruto menos reembolsos, A receber e Crédito disponível separados. Usa as vendas e pagamentos existentes, sem criar nova conta. Vendas canceladas deixam o total comercial, parcelas canceladas deixam o saldo, reembolsos descontam o recebido. Crédito aplicado não é recebimento em dinheiro. Histórico continua disponível.

Teste reproduz venda enviada por150, não paga, na virada UTC; verifica tabela e cartões A receber150 e Recebido0. Outros testes verificam pagamento parcial e cancelamento no resumo do cliente. Capturas com dados de demonstração em capturas-financeiro-clientes/.

Versão2.9.1/schema10 mantidos. Nenhum ZIP gerado neste pedido; pacotes anteriores não incluem esta correção. Avaliação manual com o banco do usuário ainda pendente.

Validação local: 308 testes aprovados, zero falhas/erros/pulos.

Windows aprovado: run38672860664 (correção financeira) e38673220952 (incluindo ocultação de baixadas no estoque). Pacote ignorado em ambos. Evidências em evidencias-financeiro-clientes/.
