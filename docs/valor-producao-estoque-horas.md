# Valor de produção, peça comprada e tempo em horas — 2.9.1

## Valor de produção demonstrativo

Em **Produção**, selecione a peça/variante e abra **Ficha de produção / custos**. Informe os carretéis e gramas por peça, tempo **em horas** e custos adicionais por peça. O valor atualiza ao editar os campos. Ele considera material, custo horário da impressora (investimento, energia e manutenção) e adicionais; aquisição quando conhecida, referência quando necessária, preservando as fórmulas anteriores.

Depois de salvar, **Valor de produção** aparece na peça selecionada, no cartão e na tabela do catálogo. Se variantes tiverem custos diferentes, o cartão/tabela mostram a faixa; a peça selecionada mostra o custo da variante escolhida. A informação é demonstrativa: cadastro, edição e consulta não movimentam saldo ou Financeiro. A OP copia a ficha, e o custo só é reconhecido na conclusão com inspeção, fotos e observações, quando as unidades entram no Estoque. Não há pagamento automático.

## Peça comprada diretamente no Estoque

Abra **Estoque → Estoque → Nova peça comprada**. Informe nome, quantidade, custo total da compra, origem, condição e destino; descrição e preço sugerido são opcionais. Para entrada disponível, registre o responsável e confirme a verificação. Uma peça ainda não verificada pode entrar em Aguardando verificação e ser liberada depois.

Não precisa selecionar modelo/variante, cadastrar em Produção, adicionar STL, filamento ou OP. O sistema mantém internamente a identificação necessária para estoque, reserva e venda, mas a peça comprada não aparece no catálogo de modelos de Produção. Ela fica disponível nos seletores de Vendas, no filtro de produto do Financeiro, na busca global (abrindo Estoque) e no catálogo PDF.

O valor informado é rateado entre as unidades e compõe o valor atual do estoque. Na entrega da venda entra no CPV, sem duplicação. O pagamento da compra continua sendo uma operação separada, sem geração automática de saída de caixa. Entrada manual de itens já cadastrados também continua disponível.

## Tempo em horas

Cadastro da peça, ficha de produção, OP antiga, confirmação excepcional e calculadora recebem horas. Exemplos: **1,5 = 1h30**, **2 = 2h**, **0,25 = 15min**. Vírgula e ponto são aceitos. Valores inválidos ou negativos são rejeitados.

Internamente o sistema continua usando minutos inteiros, para preservar as regras e o histórico. Frações são convertidas para o minuto mais próximo, com meio minuto arredondado para cima. Tempos muito pequenos que arredondem para zero não servem como previsão da ficha (mínimo de um minuto). Ao reabrir um tempo antigo, o valor em horas retorna ao mesmo número de minutos; rascunhos antigos da calculadora em minutos são convertidos na leitura.

## Preservação e entrega

Banco 8 → 9, backup prévio e migração transacional. A nova tabela apenas identifica o catálogo de peças compradas; não modifica produtos, OPs, custos, recebimentos ou arquivos históricos. Versão do aplicativo permanece **2.9.1**.

Capturas reais do Qt com dados temporários:

- [Valor demonstrativo no catálogo](capturas-estoque-horas/valor-producao.png)
- [Ficha com horas e cálculo](capturas-estoque-horas/ficha-horas.png)
- [Compra sem modelo/variante de Produção](capturas-estoque-horas/nova-peca-comprada.png)
- [Estoque da peça comprada](capturas-estoque-horas/estoque.png)
- [Financeiro separado do planejamento](capturas-estoque-horas/financeiro.png)

284 testes locais aprovados (zero falhas/erros/pulos); 20 testes de interface/fluxo repetidos após os ajustes visuais finais, aprovados. Suíte completa [Windows aprovada](https://github.com/d28ty8rky9-star/drheeklab/actions/runs/38503428577); pacote ignorado e zero artefatos. Evidências: `evidencias-estoque-horas/`. Avaliação prática no Windows pelo proprietário permanece pendente. Código atualizado no GitHub; nenhum ZIP/instalador nesta alteração. O pacote entregue anteriormente não contém as mudanças de código posteriores.
