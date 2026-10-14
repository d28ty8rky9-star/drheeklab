# Evidências do novo fluxo — Dr. Heek Lab 2.9.1

Código testado: b4799b2c94470531d454c3913853b4ce1a4b6328.

- Linux/PySide6 offscreen: 266 testes aprovados; 0 falhas, 0 erros, 0 pulos. Relatório linux-tests.xml.
- Dependências: pip check sem incompatibilidades.
- Migração de todas as versões anteriores, incluindo schema 7, preservação/backup e novo schema 8 cobertos pela suíte.
- Planejamento sem estoque/caixa, OP sem reconhecimento antecipado, inspeção/fotos/observações, publicação/custo únicos, filtros por data da conclusão, congelamento de preços, perdas/reimpressão, venda/CPV sem duplicação, peças compradas e registros legados cobertos.
- Formulários reais: salvar/reabrir ficha, gerar OP mínima, confirmar, inspecionar, concluir, visualizar Estoque/Financeiro e reservar pela unidade selecionada.
- Capturas em ../capturas-fluxo-producao/ são Qt real com banco temporário descartado. Custos ilustrativos: duas unidades a R$ 4,60; total R$ 9,20; caixa R$ 0,00.
- Workflow Windows automático somente de testes: run 38502081384. Aprovado, incluindo preparação/dependências e suíte completa. Empacotamento ignorado e zero artefatos; resultado final em windows-status.json e windows-artifacts.json.
- Não executado empacotamento, instalação/reinstalação ou nova qualificação manual nesta alteração; nenhum ZIP/instalador novo solicitado ou gerado. O pacote anterior não contém estas mudanças.
