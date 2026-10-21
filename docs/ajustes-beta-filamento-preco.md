# ZIP atualizado entregue sob solicitação

Pacote dist/DrHeekLab-2.9.10-Beta-Ajustes-Filamento-Preco-Windows.zip, run39534133352, artifact12317133513, código800ced6b3adc7b9d2ef80c94584ac6284ff4f7dc. 314 testes nativos Windows aprovados sem falhas/erros/pulos. Compilação/instalação/reinstalação/backup/preservação dados/agendamento/desinstalação aprovados; CRC e hashes do ZIP/executáveis conferidos. Fluxo de filamento usado, preço sugerido e acessórios sem margem confirmados nos módulos dentro do executável. Evidências evidencias-ajustes-beta/requested-package.json. Preparação abaixo é histórica.

# Beta — filamento usado no cadastro e sugerido da Produção

FilamentDialog libera Saldo desconhecido e Estado no cadastro inicial. Marcar usado/desconhecido seleciona Aberto; salva remaining_mg NULL, sem estimar o que resta ou exigir edição posterior. Pode também deixar peso inicial desconhecido. Filamento novo conhecido continua entrando com o peso integral e valor proporcional já existente; Aberto com saldo conhecido admite informar a quantidade restante. Edição preserva validação/auditoria anterior.

Produção mostra Preço sugerido na tabela e nos cartões com base nas fichas de variantes ativas: (custo total − extras detalhados) ×2 + extras detalhados. Extras/argolas/acessórios são repassados ao custo. Se não há ficha, permanece o preço manual já cadastrado ou Não informado; múltiplas variantes mostram faixa. A leitura retorna custo e sugestão juntos sem gravar preço no cadastro nem movimentar estoque/Financeiro.

Novas vendas usam a mesma regra para extras embutidos, pela receita congelada na OP; acessórios selecionados separadamente continuam pelo custo. Peças compradas mantêm +30%. A base do percentual de lucro exclui os acessórios embutidos e os separados. Valores efetivos, snapshots de vendas e custos históricos anteriores não são reescritos; CPV e caixa permanecem nas operações existentes. Custos adicionais antigos sem detalhamento de extras não são inventados como acessórios.

Exemplo verificado: impressão3,10 + acessório10 = custo13,10; sugerido16,20; margem100% sobre3,10. Novo acessório separado5 leva o total para21,20. Capturas reais temporárias em capturas-ajustes-beta/.

Validação: 314 testes locais aprovados, zero falhas/erros/pulos. Versão2.9.10 Beta e schema10 mantidos. Nenhum ZIP/instalador gerado; último pacote não contém estes ajustes. Avaliação manual no computador do proprietário pendente.

Validação Windows aprovada no run39532755479, código427b78fe8424aac46bd3aaceb23545c59b606972; etapa de pacote ignorada.
