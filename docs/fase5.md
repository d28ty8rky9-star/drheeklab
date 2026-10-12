# Fase 5 — produção e qualidade

Versão 2.4.0, SQLite 5. Avanço autorizado pelo proprietário. Registro histórico: Fase 6 já autorizada e implementada; consulte `fase6.md`. O instalador Windows continua dependente de geração e homologação em Windows.

## Operar

1. Cadastre produto e variante; importe o arquivo STL/3MF em Produtos. Cadastre filamentos e confirme impressora operacional.
2. Abra **Produção → Nova OP / lote**. Informe responsável, parâmetros de impressão, tempo previsto total, prioridade e modelos/quantidades. Cada modelo tem sua versão de arquivo e lista de carretéis com gramas totais, incluindo suportes. Remova linhas desnecessárias.
3. Selecione **Para estoque** ou um item de pedido aprovado. OP vinculada a pedido admite uma variante correspondente ao item; lotes mistos são registrados para estoque e podem ser reservados posteriormente para diferentes pedidos. Para item personalizado ainda sem variante de atendimento, selecione o modelo/variante na OP: a associação operacional é registrada sem alterar descrição ou preço aprovados.
4. O custo de máquina do lote é calculado uma vez e rateado pelas gramas estimadas de cada modelo. Se usar pesos manuais, informe todos os pesos e uma justificativa. A soma dos centavos é preservada.
5. Defina prioridade alta/normal/baixa, selecione uma OP e use ↑/↓ para reordenar dentro da prioridade. A data original não muda. **Iniciar** ocupa uma impressora operacional; outra OP não pode imprimir simultaneamente nessa máquina.
6. **Confirmar tentativa** exige minutos reais, gramas por carretel/modelo e custo real dos auxiliares. O cronômetro é somente uma sugestão. Progresso de falha pode sugerir gramas proporcionais, editáveis antes de salvar. A confirmação debita os carretéis e acrescenta tempo uma única vez; qualquer saldo insuficiente desfaz a transação inteira.
7. Em “Peças perdidas sem unidade aproveitável”, registre unidades que não resultaram em peça física. Defeitos em peças físicas existentes seguem para inspeção e reprovação individual. Informe motivo de falha. Falha sem peças físicas deixa a OP aguardando para outra tentativa; tentativas anteriores continuam no custo total.
8. Selecione cada peça e use **Inspecionar**. Checklist decorativo, funcional ou misto, responsável e três fotos reais distintas: frente, lateral/verso e detalhe crítico. Conforme / reprovado / não aplicável não têm aprovação automática. Os dois últimos exigem justificativa; item reprovado impede aprovação da peça. Resultado pode ser aprovado com observações leves, com observação obrigatória.
9. **Concluir OP** exige inspeção de todas as peças e pelo menos uma aprovada. As aprovadas tornam-se disponíveis; reprovadas ficam em quarentena. Uma OP totalmente reprovada permanece em inspeção e admite nova OP de reimpressão. Descarte pelo estoque fica bloqueado enquanto a OP não estiver concluída, para preservar a consolidação de custo.
10. Em Vendas, reserve as peças liberadas e registre entrega. O pedido mostra códigos/estados das OPs vinculadas. Cancelar pedido preserva custo e produção existente; a OP pode terminar para estoque, mas não se cria nova OP vinculada ao pedido cancelado.
11. **Reimprimir** gera código novo, mantém vínculo à origem e copia quantidades, arquivo e parâmetros. Recalcula custos com referências atuais; permite trocar cada carretel, inclusive finalizados. Horas/consumo da origem permanecem intactos.
12. Consulte **Histórico e fotos da peça** para registros, checklists e evidências anteriores. **Registrar problema** associa superfície, suportes, adesão ou detalhes à OP e ao produto; a aba **Produtos → Problemas de produção** reúne o histórico do modelo.

## Custos, perdas e estoque

- Custo por aquisição e referência são separados. Aquisição desconhecida usa referência explicitamente, sem inventar peso ou saldo.
- Tempo de máquina é único por tentativa, inclusive em lotes com vários modelos ou o mesmo carretel compartilhado.
- Percentual de custo perdido pode ser ajustado na confirmação. É parte do custo existente, nunca um custo adicional. Reprovações físicas entram no indicador de perda com proporção do custo da tentativa.
- Exemplo testado: 5 peças, 50 g, 60 minutos na A1 Mini. Aquisição R$ 0,10/g e referência R$ 0,20/g: custo existente R$ 6,10, por referência R$ 11,10. Uma reprovada e quatro boas: custo efetivo R$ 1,53/boa, com centavos físicos 1,53 + 1,53 + 1,52 + 1,52 = R$ 6,10. A reprovada recebe custo físico zero após absorção pelas boas; descarte não adiciona outra despesa.
- Na primeira conclusão, custo total das tentativas de cada modelo é distribuído nas boas desse modelo. Modelo sem nenhuma boa mantém custo de suas peças segregadas; não se atribui custo a uma unidade inexistente. Material perdido sem peça continua registrado nas tentativas.
- Custos consolidados ficam congelados. Reinspeção/devolução não debita materiais, acrescenta horas ou redistribui custos de unidades já entregues. Retrabalho com consumo adicional exige nova OP.
- Entradas e verificações documentadas de estoque preexistente das fases anteriores mantêm sua origem. A verificação preliminar em Estoque não libera peças vinculadas a OP; estas sempre seguem o controle formal em Produção.
- Auxiliares informados na OP são valores de custo; consumo de materiais auxiliares cadastrados continua registrado em Estoque. Não há inferência automática de quantidades a partir desses valores.

## Revalidação e rastreabilidade

Os quatro estados são aguardando, imprimindo, aguardando inspeção e concluída. Não há subsistema de pausas.

Alterações em produto/variante após criação impedem confirmação, inspeção, reserva e entrega sem revalidação. **Parâmetros / revalidação** exige motivo, cria revisão, atualiza identificação/categoria de inspeção, invalida aprovações anteriores e devolve as peças à quarentena. Não muda taxas ou consumo histórico. Impressão em curso ou peças reservadas/baixadas/descartadas bloqueiam alteração: libere reservas ou abra nova OP.

Arquivo selecionado permanece uma versão imutável e explícita. Mudar a versão preferencial do catálogo não muda silenciosamente a OP. Arquivo alterado externamente exige restaurar backup ou criar nova OP com versão importada corretamente.

Fotos são copiadas para armazenamento gerenciado, com hash. Ausência/alteração bloqueia conclusão, reserva e entrega. Inspeções anteriores e fotos são preservadas quando uma nova inspeção substitui a vigente. Retorno físico de peça produzida invalida inspeção e requer nova avaliação, mantendo custo original.

## Procedimentos e backup

**Produção → Procedimentos** inclui conteúdo PO-001 a PO-012 e FR-001, também em `procedimentos-internos.md`. Organização inspirada em práticas ISO; não é certificação.

Migração 4 → 5 preserva registros e cria backup SQLite anterior. Backups completos incluem fotos de inspeção e validam hashes; restauração de backup antigo continua compatível e migra na abertura. Faça backup completo antes da atualização. TESTES/PRODUÇÃO têm bancos e arquivos distintos.

Resultados, pacote Linux e limites de plataforma: `resultados-fase5.md`. Homologação Windows: `validacao-windows.md`.
