# Fase 2 — impressoras, filamentos e precificação

Versão 2.1.0. Implementação autorizada pelo proprietário; Fase 3 depende de nova aprovação expressa.

## Cadastros

Impressoras: fabricante, modelo, identificação única, data opcional, valor de compra, minutos acumulados, três componentes horários editáveis e situação operacional. A1 Mini inicial mantém exatamente os valores aprovados. Correção manual de tempo exige justificativa. Tempo em minutos é mostrado também em horas/minutos.

Manutenções: data, descrição, valor pago informado, próxima data opcional e histórico. Registrar manutenção não soma novamente a reserva por hora e **não lança saída de caixa**; o financeiro pertence à Fase 6.

Filamentos: marca, material livre (PLA, PLA Silk, PETG, TPU, ABS e outros), cor, nome comercial, compra, peso inicial, fornecedor, data, referência por grama, saldo conhecido ou desconhecido e estado novo/aberto/finalizado. Valores usam até três casas em gramas e seis casas na referência por grama. Compra usa centavos. Carretel novo deve ter saldo conhecido; a opção de desconhecido abre o carretel sem exigir pesagem. Peso inicial pode ficar vazio quando também não for conhecido.

Custo de aquisição por grama = compra / peso inicial, quando conhecido. O botão para usá-lo como referência **não altera automaticamente** referências já cadastradas; é uma escolha explícita. Compra gratuita é zero, mas a referência para precificação pode ser positiva. Não há lançamento automático de compra no caixa nesta fase.

Arquivar conserva registros e vínculos históricos; a lixeira permite restaurar. Alterações são auditadas. Ajustes de saldo e finalização manual exigem justificativa. Saldo maior que peso inicial é recusado; corrija o peso inicial com os dados corretos antes de ajustar.

## Cálculo e históricos

- Custo à referência = máquina por tempo + consumo × referência de cada carretel + auxiliares informados para o lote.
- Preço sugerido total = custo à referência × (1 + acréscimo / 100). Padrão 200% = multiplicador 3.
- Quantidade divide custo e preço sugerido para exibir valores unitários. O total é a referência definitiva; valores unitários arredondados podem não multiplicar exatamente ao total.
- Preço final é o **total do lote**, não preço unitário. Vazio usa o sugerido; zero significa preço final zero. Auxiliares também são valores totais.
- Redução = sugerido − final, quando positiva; quando negativa, a tela informa acréscimo. Percentual = diferença absoluta / sugerido × 100. Se sugerido for zero, o percentual é não aplicável.
- Resultado à referência = preço final − custo à referência. Não reaplica redução.
- Custos de máquina e de cada linha de filamento são arredondados em centavos, `ROUND_HALF_UP`, e depois somados. Percentuais e exibição monetária usam duas casas; não há float no domínio.

A tela também mostra a valoração pelo **custo de aquisição do material** separada da referência de precificação. Para material gratuito, o custo de aquisição é zero enquanto o preço pode usar referência positiva. Se o peso inicial necessário não estiver conhecido, a valoração de aquisição aparece como desconhecida, sem inventar um custo zero. Essa valoração inclui os componentes horários aprovados e auxiliares; não representa fluxo de caixa.

Salvar previsão congela parâmetros de máquina, compra, referência, preço final e consumo previsto em JSON no banco. Configurações futuras não reescrevem históricos. O carretel do último cálculo salvo é sugerido no próximo; pode ser alterado livremente.

## Custo confirmado

No Histórico, selecione uma previsão e confirme tempo, gramas por carretel, auxiliares e quantidade reais. A comparação usa **as referências preservadas da previsão** para mostrar a diferença de execução sem misturar alteração posterior de preços com mudança de consumo. A valoração de aquisição original é exibida separadamente. O preço final informado na previsão é preservado.

Uma transação única registra confirmação, consome saldo conhecido e soma minutos à impressora. Tentativa duplicada é recusada; saldo insuficiente reverte todos os carretéis, horas, auditoria e confirmação. Consumo de carretel desconhecido é registrado, mas seu saldo permanece NULL. Saldo conhecido zerado finaliza o carretel automaticamente.

Esta tela não é uma ordem de produção nem inspeção de qualidade. Ela registra **somente tempo e consumo já confirmados**, não cronômetro, fila, tentativas/falhas ou liberação de peças. O conjunto de carretéis de uma previsão é preservado; pode informar consumo real zero em uma linha. O fluxo de produção completo e alterações de materiais entre tentativas pertencem à Fase 5. Não há cobrança de modelagem.

Confirmação de custo não é venda, recebimento ou pagamento. Não há custo duplicado em caixa. A reconciliação completa com OPs e financeiro será integrada nas fases aprovadas correspondentes.

## Persistência e recuperação

Calculadora salva rascunho após 600 ms de inatividade e ao fechar, sem criar previsão automaticamente. Após falha, recupera o último rascunho salvo. Mudança de campos ou atualização de cadastros invalida o resultado exibido até novo cálculo. Cadastros e histórico ficam nos bancos separados de TESTES e PRODUÇÃO.

Esquema 2 acrescenta tabelas de impressoras, manutenções, filamentos, cálculos e consumos. Migração da Fase 1 faz snapshot SQLite prévio, aplica transacionalmente e preserva usuários, configurações, notas e auditoria. Backup ZIP antigo de esquema 1 pode ser validado e restaurado; na abertura seguinte o banco é migrado ao esquema 2. Um esquema futuro é recusado. Faça também backup completo antes de atualizar.

Alerta de saldo baixo é mostrado em Início e Estoque. Limite inicial 100 g, configurável. Carretéis desconhecidos, finalizados ou arquivados não geram alerta de baixo peso.

## Validação do proprietário

Validar no ambiente TESTES: cadastros reais de referência, A1 Mini/R$ 1,10, filamento gratuito, carretel aberto desconhecido, várias cores, custo 30/sugerido 90/final 35, comparação prevista/confirmada, limites de peso e rascunho após reinício. Confirmar apresentação clara de custo de aquisição e referência.

Ainda pendentes: homologação Windows, ícone e arquivo de logo original. Não avançar à Fase 3 sem aprovação expressa.
