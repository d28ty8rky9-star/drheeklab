# Validação — extras na Produção

Código testado: fa06628883476f8547982ac9ed31c73fc8486605.

- Linux/Qt offscreen: 289 testes aprovados, zero falhas/erros/pulos; linux-tests.xml.
- Novos testes: quantidade × custo de extras, gravação/reabertura/remoção e atualização automática, prévia sem STL, validação de campos inválidos, OP com quantidades multiplicadas e extras congelados mesmo após editar ficha, custo reconhecido somente na conclusão sem caixa automático.
- Compatibilidade: auxiliares antigos mantidos como base, extras ausentes tratados como lista vazia; schema 9 e versão 2.9.1 preservados. Nenhum dado histórico reescrito.
- Capturas Qt reais em ../capturas-extras-producao/, somente banco temporário. Exemplo: material R$2,50 + máquina R$1,65 + extras R$1,50 = R$5,65 por peça (planejamento).
- Windows: run 38504392901, suíte completa aprovada, pacote ignorado, zero artefatos. Resultado em windows-status.json e windows-artifacts.json.
- Sem gerar ZIP/instalador ou executar qualificação manual do proprietário nesta alteração.
