# Produção → OP → Estoque → Financeiro — Dr. Heek Lab 2.9.1

## Como usar

1. Em **Produção**, cadastre a ideia/modelo. Na ficha da peça ficam variantes, fotos de referência e arquivos STL/3MF.
2. Selecione a variante e abra **Ficha de produção / custos**. Salve impressora, arquivo, filamentos e gramas **por peça**, minutos **por peça**, auxiliares e parâmetros. O botão Calcular custo mostra aquisição e referência. Isso é planejamento: não movimenta estoque nem Financeiro.
3. Clique **Produzir esta peça**. A OP pede quantidade, responsável, prioridade e pedido vinculado opcional. Arquivo, consumo, tempo e parâmetros vêm da ficha; consumo, auxiliares e tempo multiplicam pela quantidade. A OP guarda uma cópia da revisão utilizada e dos parâmetros de custo.
4. Na fila, clique **Iniciar** e, ao terminar a impressão, **Impressão terminada**. O padrão utiliza o consumo e tempo cadastrados. Se houve perdas, registre quantidade e motivo; se consumo/tempo foram diferentes, use o ajuste excepcional. Confirmar baixa o material efetivamente utilizado e atualiza horas da impressora, mas as unidades permanecem apenas na inspeção da OP.
5. Inspecione cada peça com checklist, responsável, **três fotos distintas** e **observações obrigatórias**. Clique **Concluir OP**. Todas as unidades devem ser inspecionadas e deve existir ao menos uma aprovada. Só então aparecem no Estoque, aprovadas disponíveis e reprovadas identificadas em quarentena.
6. No **Financeiro → Produção**, o custo aparece na data da conclusão. É custo de produção reconhecido e valor das unidades, **sem pagamento automático ou conta a pagar**. O valor atual consolidado do estoque também aparece no Financeiro, identificado como posição de hoje, separado do filtro histórico do relatório.
7. Ao vender e entregar, o custo atribuído é reconhecido no CPV uma vez. O custo de produção não é subtraído outra vez do resultado nem duplicado no caixa.

## Estoque único

A aba **Peças prontas** foi retirada da interface. **Peças físicas** passou a se chamar **Estoque**, com uma linha por unidade, nome, variante, estado, condição e custo. Entrada manual/peça comprada, reservas, revisão, descarte, materiais, movimentos e histórico continuam disponíveis.

Peças compradas prontas continuam usando entrada manual, sem obrigar a criar uma OP ou STL. Seu custo compõe o valor atual em estoque; pagamento e venda continuam sendo operações separadas.

## Preservação e limites

- Migração do banco 7 → 8, com backup anterior automático e transação. Novas tabelas guardam fichas por variante, vínculo da OP à revisão e reconhecimento único na conclusão. Dados e arquivos anteriores são preservados.
- Fichas, prioridade e criação da OP não criam consumo, recebimento, despesa ou estoque. A confirmação da impressão continua registrando consumo real dos materiais; não inventa pagamento.
- Custos em centavos, aquisição quando conhecida e referência quando necessária; arredondamento/rateio e absorção de perdas preservados. Revisar uma ficha ou mudar preços não reescreve uma OP já gerada.
- Reinspeção não reconhece custo uma segunda vez. Reimpressão de OP do novo fluxo também aguarda conclusão para aparecer no estoque/Financeiro.
- OPs históricas mantêm o tratamento anterior de confirmação e datas, para não reescrever relatórios já existentes. A nova regra vale para OPs criadas a partir da ficha. As unidades históricas em quarentena permanecem rastreáveis.
- A confirmação padrão utiliza o cadastro; consumo diferente precisa ser informado no ajuste excepcional. Fotografias usadas nas capturas são demonstração isolada, não documentação de uma produção real.
- Versão continua 2.9.1 em desenvolvimento. Esta atualização é de código; o ZIP/instalador entregue anteriormente não contém estas mudanças. Nenhum novo pacote será gerado sem pedido explícito.

## Evidências

Capturas reais do Qt com dados descartáveis:

- [Produção e fila](capturas-fluxo-producao/producao.png)
- [Ficha por variante](capturas-fluxo-producao/ficha-producao.png)
- [OP simplificada](capturas-fluxo-producao/nova-op.png)
- [Estoque único](capturas-fluxo-producao/estoque.png)
- [Financeiro após conclusão, sem caixa](capturas-fluxo-producao/financeiro.png)

266 testes locais aprovados (0 falhas/erros/pulos); suíte completa Windows aprovada no [run 38502081384](https://github.com/d28ty8rky9-star/drheeklab/actions/runs/38502081384). Empacotamento ignorado; zero artefatos. Evidências: `evidencias-fluxo-producao/`. Avaliação manual do proprietário no Windows permanece necessária; testes automatizados não substituem a avaliação prática.
