# Validação — valor demonstrativo, estoque comprado e horas

Código Windows: 2357b31c27adb91823980836dc3870f72d3fe8f1.

- Suíte local Linux/Qt offscreen: 284 testes aprovados, 0 falhas/erros/pulos; linux-tests.xml.
- Após ajustes finais de legenda/coluna, 20 testes de formulários e fluxo real repetidos e aprovados.
- Cobertura: conversão decimal de horas (inclusive vírgula), arredondamento e tempos antigos, valores inválidos, rascunho legado da calculadora, cálculo automático da ficha e valor nos cartões/tabela/seleção sem efeitos no Financeiro.
- Compra direta: cadastro com catálogo de Produção vazio, entrada/valor do estoque, busca abrindo Estoque, filtro Financeiro, venda/CPV/recebimento; confirmação de rollback sem cadastro órfão em erro/duplicidade.
- Migração de versões anteriores até schema 8 incluída na suíte; banco atual schema 9. OPs, fotos, documentos e custos históricos preservados.
- Capturas Qt reais com dados descartáveis em ../capturas-estoque-horas/. Exemplo de planejamento: 25g a R$0,10/g + 1,5h a R$1,10/h + adicionais R$2 = R$6,15; custo de produção financeiro zero antes da conclusão. Peça comprada: custo R$50 no estoque, sem saída de caixa automática.
- Windows: execução 38503428577, suíte completa aprovada. Empacotamento ignorado, zero artefatos. Resultado final em windows-status.json e windows-artifacts.json.
- Sem empacotamento/novo ZIP/instalador. Pacotes anteriores não contêm estas alterações. Avaliação prática do proprietário ainda pendente.
