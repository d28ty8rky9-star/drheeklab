# Fase 4 — clientes, orçamentos, pedidos, recebimentos e entregas

Versão 2.3.0, esquema SQLite 4. Registro histórico da Fase 4. A Fase 5 já foi autorizada e implementada; consulte `fase5.md`.

## Clientes

Em Vendas → Clientes, cadastre nome obrigatório, telefone/e-mail opcionais e observações. O Histórico mostra pedidos, pagamentos e crédito disponível. Arquivar/restaurar conserva os vínculos; novos registros exigem cliente ativo. Nome e contatos ficam congelados nos orçamentos/pedidos: editar o cadastro não reescreve documentos antigos.

## Orçamentos

Crie itens de produto/variante ou descrição personalizada, quantidade, **preço final unitário**, frete total e observações. Validade começa em sete dias; edite ou deixe vazia. Estados: pendente, aprovado, rejeitado ou vencido (calculado pela data atual). Foto PNG/JPEG e arquivos STL/3MF podem acompanhar itens personalizados.

Salvar orçamento gera PDF versionado, mas **não cria receita, pagamento, reserva ou consumo**. Aprovar copia os dados para pedido `PED-AAAA-NNNN`, sem redigitar. Itens marcados como estoque são reservados nessa aprovação. Se não houver estoque suficiente, toda a aprovação é revertida e o orçamento permanece pendente. Orçamento vencido/rejeitado/aprovado não é convertido outra vez; gere novo registro quando necessário.

Aprovação/rejeição emite nova versão do orçamento. PDFs antigos continuam intactos; Nova versão PDF permite registrar o estado atual sem sobrescrever. Documentos do cliente mostram preços finais, frete e total, **sem custos internos ou linha automática de desconto**.

## Pedidos e rascunhos

Novo pedido aprova definitivamente os itens/preços. Não há botão de edição/versionamento comercial após aprovação. Alterações excepcionais exigem cancelamento e novo registro, preservando o histórico. Reservas, produção, pagamentos e entregas são eventos operacionais adicionais, não reescrita de itens/preços.

O editor salva rascunho após 600 ms de inatividade e ao cancelar/fechar, sem criar registros comerciais. O último rascunho é recuperado no próximo editor. Anexos de rascunho ainda referem os originais; só são copiados para o armazenamento quando o orçamento/pedido é confirmado. Se o original não existir mais, selecione-o novamente.

Pedido aceita múltiplos itens, produto cadastrado ou personalizado, referência fotográfica/STL/3MF, frete, prazo opcional e observações. A cópia de anexos conserva originais, nome, checksum e vínculo. Tipos permitidos são identificados; não há análise automática de fatiamento.

## Entrada, parcelas e pagamentos

No pedido ou aprovação do orçamento, informe entrada efetivamente recebida se houver e número de parcelas do saldo. **Gerar parcelas editáveis** cria a entrada + parcelas restantes; valores e vencimentos podem ser alterados na tabela, e parcelas podem ser adicionadas/removidas. Sem preparação manual, o programa calcula a mesma divisão ao salvar. As parcelas positivas devem somar exatamente o total do pedido. Vencimento pode ficar vazio.

Resto em centavos é distribuído nas primeiras parcelas; vencimentos mensais mantêm o dia de referência, ajustando ao último dia de meses menores. Exemplo: venda 100, entrada 30 e duas parcelas do saldo → 30 recebido + 35 + 35 previstos. Planejar parcela não recebe dinheiro. Entrada e aprovação são uma transação única: entrada inválida não deixa pedido/reserva/PDF parcial.

Em Detalhes → Pagamentos, registre integral/parcial, data efetiva, meio e taxa em reais. Pix, dinheiro, débito, crédito, transferência e outros são aceitos. Pagamento não pode ser negativo, exceder saldo ou ter taxa maior que o valor; data futura deve ser previsão, não recebimento efetivo.

- Saldo do cliente usa valor **bruto pago/aplicado**. Taxa não é cobrada novamente do cliente.
- Líquido em caixa = pagamento bruto − taxa. Pagamento por crédito do cliente não cria entrada em caixa e não tem taxa.
- Pagamentos são alocados aos itens em ordem de criação, priorizando os mais antigos; após eles, ao frete. A alocação das parcelas prioriza vencimentos mais antigos, depois parcelas sem data, com desempate pelo ID. Ver alocação mostra rastreabilidade.
- Contas a receber exibe previsto, aplicado, saldo e situação pendente/parcial/quitada/atrasada. Canceladas têm saldo exigível zero, preservando os valores históricos.

A cada pagamento é emitido **novo PDF comercial**, sem substituir versões anteriores. PDF inclui cliente, pedido, data, itens, preços finais, frete, total, pagamentos com datas/meios/valores, total recebido, crédito aplicado quando houver e saldo. QUITADO aparece apenas em pedido ativo sem saldo. O documento declara que **não é nota fiscal**; taxas internas não são expostas.

## Produção, peças e entrega

Pedidos de estoque reservam peças aprovadas/disponíveis ao criar/aprovar. Pedidos para produção aguardam atendimento. Detalhes permite vincular cálculo previsto/confirmado da Fase 2, preservando custo e mostrando confirmação. **OPs, fila, impressão em tempo real e inspeção formal da Fase 5 ainda não existem.**

Após produção e verificação preliminar da Fase 3, registre peças em Estoque, reaproveitando o cálculo confirmado, e reserve-as no item. Para personalizado sem modelo inicial, selecione uma variante física para atendimento; esse vínculo operacional não muda descrição, quantidade ou preço aprovado. Variante de um item já cadastrado não pode ser trocada.

Reservas vinculadas a pedido só são liberadas/canceladas/baixadas por Vendas. A área Estoque recusa processamento direto dessas reservas, evitando saída fora do histórico comercial.

Registrar envio/entrega exige reserva de **todos os itens**. Envio muda para Enviado e baixa peças uma vez; confirmação posterior de entrega não repete baixa. Retirada presencial pode ser entregue diretamente. Registre transportadora, rastreio, datas efetivas e comprovante opcional PDF/foto. Frete cobrado é o aprovado no pedido; zero indica gratuito. Entrega pode ocorrer com saldo financeiro pendente, que continua em contas a receber.

## Cancelamentos, crédito e retorno

Cancelar exige motivo/justificativa e destinação de valores: reembolso + crédito futuro + retenção justificada = tudo já pago/aplicado. Se nada foi pago, essas parcelas financeiras são zero. Crédito aplicado não pode virar reembolso de dinheiro que não entrou. Reembolso efetivo não pode anteceder pagamentos nem ter data futura.

Cancelamento preserva pedido, pagamentos, PDFs, custos/calculações, consumo, horas e histórico. Libera apenas reservas ainda ativas; peças já enviadas/entregues continuam fora do estoque. Não desfaz fabricação nem inventa retorno físico.

Crédito futuro entra no saldo do cliente. Na próxima compra, registre pagamento por Crédito do cliente: reduz crédito/saldo devido, sem fingir novo dinheiro recebido. Reembolso registra saída própria; o histórico original de recebimentos continua visível. Repetir cancelamento/pagamento com a mesma operação é recusado.

**Retorno físico após cancelamento** exige selecionar as peças efetivamente recebidas e registrar condição. Mantém o ID/custo original, sem novo custo de fabricação e sem entrada duplicada. Elas ficam aguardando nova verificação antes da disponibilidade. A mesma peça não retorna duas vezes pelo mesmo pedido. O histórico de envio/entrega não é apagado.

Peça concluída após cancelamento pode entrar no estoque pelo cálculo confirmado, ainda com a unicidade de entrada da Fase 3; não consome filamento/horas novamente. Não vincule novos custos ao pedido cancelado: preserve vínculos anteriores e registre produção adicional para estoque.

## Documentos, integridade e atualização

PDFs usam preto, roxo e azul e o logotipo oficial configurado. Sem arquivo da marca, há texto explícito de logotipo não configurado, sem símbolo inventado. Configure a marca antes de emitir documentos finais para clientes. PDFs e anexos ficam nas pastas do ambiente e participam do backup completo, com hash validado. Valores/contatos emitidos não mudam após alteração de cadastros.

Esquema 4 acrescenta clientes, orçamentos, pedidos, parcelas, pagamentos/alocações, crédito, cancelamentos/reembolsos, entregas, documentos, anexos e vínculos operacionais. Migração preserva os dados anteriores e cria snapshot SQLite prévio. Backups de esquemas 1–3 continuam restauráveis e são migrados ao reabrir.

Eventos financeiros, reservas e PDFs compartilham transação. Falha na geração do documento/auditoria/estoque reverte o evento inteiro e remove somente os arquivos recém-criados. O pedido nunca permanece pago sem seu novo comprovante por uma falha de geração.

## Validação e limites

Valide em TESTES: cliente → orçamento → aprovação com entrada/parcelas → pagamentos → reserva → envio/entrega, seguido de cancelamento/reembolso/crédito e retorno físico quando real. Confira que orçamento não altera caixa/estoque, taxa não cria saldo artificial, versões anteriores permanecem intactas e custo é preservado.

128 testes automatizados e verificação funcional do pacote Linux estão documentados em `resultados-fase4.md`. O comando `--self-test` usa exclusivamente diretório temporário, sem abrir dados do usuário; exercita autenticação, PNG/logo de QA, orçamento/pedido, pagamentos/taxas, PDFs versionados e baixa física.

Windows e instalador ainda não homologados. O build Windows agora bloqueia instalação caso pytest ou o teste funcional do pacote falhem; executar o script/gerar pacote não substitui homologação visual e persistência no Windows sem Python. Marca original, qualidade formal, financeiro completo (despesas/aportes/contas a pagar/relatórios) e demais fases continuam pendentes conforme planejamento.
