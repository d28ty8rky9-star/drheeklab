# Limpeza de código sem mudança funcional — 2.9.1

Removidas construção/atualização da interface Auxiliares já oculta, seus handlers inacessíveis e a tabela agregada de estoque já oculta. MaterialDialog, ConsumeMaterialDialog, domínio de materiais, perdas, compras, documentos e dados históricos permanecem; não houve exclusão/migração de dados. Resumo textual oculto do Início removido com cálculo duplicado; cartões visíveis continuam iguais.

stock_snapshot centraliza uma leitura de peças e acessórios, retornando as listas e os mesmos totais. StockPage reaproveita essa leitura, eliminando classificação por consulta individual e leituras duplicadas. A apresentação reutiliza os totais já atualizados ao entrar no Estoque; Início continua lendo dados atuais. stock_totals mantém a interface anterior para demais consumidores. Removidas consultas de resumo cujo resultado não era usado e 35 vínculos de importação sem uso.

Testes antes vinculados a widgets ocultos agora verificam a tabela efetivamente visível, contagens/estados e preservação do item descartado no banco; resumo financeiro é verificado nos cartões visíveis. Nenhum teste foi excluído ou desativado. Suíte local: 310 aprovados, zero falhas/erros/pulos.

Experimento com os mesmos dados (4 peças e2 acessórios), comparando StockPage.refresh de ed651b8 com a nova implementação: 35→22 SELECTs, mesmos totais/listas, sem comparação de tempo prometida. A apresentação completa também deixa de reler totais já calculados. Evidências em evidencias-limpeza/. Código Python principal: 7.828→7.773 linhas, redução líquida55, incluindo linhas vazias/comentários. Não houve meta de reduzir linhas ou compactação da lógica para diminuir a contagem.

Arquivos grandes de telas permanecem nesta etapa para evitar reorganização ampla sem necessidade funcional. Não foram alteradas fórmulas, regras de estoque/produção/vendas/segurança, versão2.9.1 ou schema10. ZIP/instalador somente sob pedido explícito; pacotes antigos não incluem esta limpeza.

Validação Windows aprovada no run38832775408, código8ec528db44f5d0a596599a2c01698b28222c026d; etapa de pacote ignorada.
