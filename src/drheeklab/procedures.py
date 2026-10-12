"""Internal operating procedures, inspired by quality-management practices."""
TEXT = '''DR. HEEK LAB — PROCEDIMENTOS INTERNOS • Revisão 1 • Fase 5
Referência de organização inspirada em práticas ISO. Não constitui certificação ISO.
Aplicação: responsável da OP executa; responsável da inspeção registra evidências; proprietário revisa desvios. Revisões dos procedimentos exigem aprovação do proprietário e registro na auditoria.

PO-001 — Controle de documentos e arquivos
Antes da OP, importar STL/3MF em Produtos, conferir nome, versão e hash; selecionar explicitamente a versão. Não sobrescrever arquivos gerenciados. Registrar parâmetros na OP. Mudanças de modelo/variante ou parâmetros exigem revalidação; preservar revisões anteriores na auditoria.

PO-002 — Análise do pedido e autorização
Conferir item, variante, quantidade, prazo e pedido aprovado. Vincular o item à OP; pedidos cancelados não autorizam nova produção. OP para estoque deve identificar o responsável. Condições comerciais são preservadas em Vendas.

PO-003 — Preparação da impressora
Verificar máquina operacional, mesa limpa, nivelamento, bico e manutenção. Conferir identificador e filamentos. Registrar parâmetros: camada, preenchimento, temperaturas e suportes. Máquina em manutenção/inativa não inicia OP.

PO-004 — Identificação e controle dos materiais
Conferir carretel, marca/material/cor, saldo conhecido ou desconhecido. Registrar gramas previstas por modelo e carretel. Confirmar gramas totais reais antes de consolidar; saldo desconhecido permanece desconhecido. Ajuste manual de saldo exige motivo. Auxiliares entram no custo da tentativa.

PO-005 — Planejamento da fila e lotes
Selecionar prioridade alta, normal ou baixa; reordenar dentro da prioridade sem mudar criação. Identificar todos os modelos da mesa e arquivos. Ratear custo único de máquina pelas gramas previstas; rateio manual exige peso por modelo e justificativa. Conferir soma dos centavos.

PO-006 — Execução e confirmação do tempo
Iniciar somente OP aguardando em máquina disponível. Cronômetro fornece uma sugestão; operador confirma minutos reais. Não há subsistema de pausas. Cada tentativa adiciona horas e debita filamentos uma única vez, atomicamente. Falha sem peça aproveitável pode retornar a aguardando para nova tentativa.

PO-007 — Falhas e não conformidades
Registrar motivo, progresso, consumo real e unidades perdidas sem peça aproveitável. Sugestão proporcional ao progresso deve ser conferida e pode ser ajustada. Defeitos em peças físicas seguem para inspeção individual. Percentual de custo perdido é informativo e já está incluído no total; nunca somá-lo novamente. Associar problemas à OP e ao produto.

PO-008 — Reimpressão
Usar Reimprimir para gerar nova OP vinculada à origem com novo código e referências atuais. Conferir parâmetros, arquivo, quantidade e material antes de iniciar. Carretel finalizado/arquivado deve ser substituído por um disponível. Não reutilizar consumo ou horas consolidados da origem.

PO-009 — Inspeção decorativa
Inspecionar cada peça: superfície, suportes, adesão/camadas, detalhes delicados e aparência. Preencher FR-001 com frente, lateral/verso e detalhe crítico em três fotos distintas. Registrar responsável e observações. Não aplicável e reprovado exigem justificativa.

PO-010 — Inspeção funcional ou mista
Verificar superfície, suportes, adesão, detalhes, dimensões, encaixe/função e resistência adequada ao uso. Categoria mista também avalia aparência. Registrar método/resultado de medição ou teste nas observações. A aprovação depende de todos os itens conformes ou justificadamente não aplicáveis.

PO-011 — Liberação, segregação e revalidação
Resultados: aprovada, aprovada com observações leves ou reprovada. Reprovada permanece segregada; nunca disponível. Concluir somente após inspeção de todas as peças e pelo menos uma aprovada. Ao concluir, custo com perdas é distribuído nas boas de cada modelo; custo não é cobrado novamente. Nenhuma boa de um modelo mantém custo segregado nas suas reprovadas. Alterar parâmetros/modelo/variante invalida liberação; revalidar e reinspecionar. Peças devolvidas exigem nova inspeção. Não alterar peças já baixadas; preservar histórico e abrir nova OP quando necessário.

PO-012 — Rastreabilidade, guarda e recuperação
Guardar fotos, arquivos, tentativas, custos, auditoria e códigos de OP. Consultar histórico por produto e produção. Gerar backup completo verificado com banco e arquivos; não excluir fotos manualmente. Testar restauração em ambiente de testes; produção e testes permanecem separados. Encerrar o aplicativo antes da atualização/restauração.

FR-001 — Registro individual de inspeção
Identificação: OP, revisão, peça física, modelo/variante, arquivo/versão.
Execução: responsável, data/hora de registro, categoria e checklist aplicável.
Para cada item: conforme / reprovado / não aplicável; justificativa obrigatória nos dois últimos.
Evidências: foto frontal, lateral ou verso, detalhe crítico; arquivos copiados e hash registrados.
Decisão: aprovada / aprovada com observações leves / reprovada; observações e defeitos.
Liberação: conclusão da OP após inspeções; vínculo à peça, custo existente e movimentação auditada.
Retificação: nova inspeção preserva registro e fotos anteriores; alterações de parâmetros criam revisão e exigem revalidação.
'''
