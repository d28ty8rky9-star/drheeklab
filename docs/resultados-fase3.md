# Validação da Fase 3 — versão 2.2.0 / esquema 3

Registro histórico. Resultados atuais da versão 2.3.0 em `resultados-fase4.md`.

Ambiente: Linux, Python 3.12.14, PySide6 6.8.3, pytest 8.3.5. Todos os dados de validação são temporários; nenhum banco de produção foi utilizado.

## Testes

`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q -o faulthandler_timeout=15`: **97 testes passaram**, incluindo as fases anteriores.

Evidências específicas:

- Produtos com código automático crescente, campos validados, categoria, recomendação, configuração manual, variantes, pesquisa literal/casefold e lixeira.
- Snapshot de custo/preço unitário da calculadora permanece congelado após editar o produto.
- PNG/JPEG validado e copiado sem tocar no original; foto principal alterável. STL/3MF em versões numeradas, com preferência e conteúdo antigo preservado.
- Arquivo de outro produto, caminho fora do armazenamento, foto inválida e arquivo alterado externamente são recusados. Falha na auditoria reverte registro e remove só a cópia recém-criada.
- A invocação opcional de Bambu Studio foi testada com argumentos separados e `shell=False`; a execução do aplicativo externo real não foi realizada.
- Entrada de três peças com custo 10,01 atribui 3,34 / 3,34 / 3,33; soma exata.
- Reservar não reduz físico; liberar não duplica entrada; baixa física usa custo existente e não pode repetir.
- Peças de uso pessoal precisam de verificação nova; rejeição mantém indisponibilidade. Peças reservadas/baixadas/descartadas não voltam pela verificação.
- Perdas preservam motivo, data, observações e custo já atribuído; a mesma peça e a mesma operação não são contabilizadas novamente.
- Saldo insuficiente, peça reservada no descarte e falha na auditoria revertem toda a operação sem alterar outras peças/saldos.
- Auxiliares: cadastro, saldo, ajuste justificado, consumo, descarte e diário. Filamentos: consumo da Fase 2 integrado ao diário, perda documentada, aquisição/referência diferenciadas e saldo desconhecido preservado.
- Produção para estoque usa cálculo confirmado, mesma quantidade/custo, sem nova baixa de filamento ou horas; um cálculo não pode gerar entrada duplicada.
- Arquivamento não oculta estoque físico do resumo e é bloqueado com reservas ativas.
- Migração real de esquema 2 → 3 preserva cálculos, consumo, saldo e horas, criando saldo de abertura sem relançar saídas antigas. Backups de esquema 2 restauram e migram; testes anteriores também cobrem esquema 1.
- Backup/restauração cobre fotos, projetos, variantes, custos, peças, reservas e perdas. Arquivo atual ausente/alterado invalida novo backup completo, mas ZIP anterior íntegro pode reparar o estado, mantendo rollback e registro da incompletude anterior.
- Qt offscreen: formulários de produto/variante/material, galeria com foto real de teste, pesquisa, importação, entrada física, verificação, reserva, liberação, perda, confirmação/cancelamento e persistência após reabrir.

## Pacote

Instalação editável atualizada para 2.2.0. PyInstaller gera o pacote Linux completo em `dist/DrHeekLab`; o binário depende dos arquivos dessa pasta. `pip check` não encontrou dependências incompatíveis.

Verificação do pacote congelado: `--help` retorna sucesso; inicialização Qt offscreen permanece no primeiro login, cria esquema 3 e a A1 Mini aprovada, sem cadastrar produtos/peças/usuário fictícios. O processo foi encerrado após essa verificação. Os fluxos autenticados foram testados pelo pytest no código, não automatizados no pacote congelado.

## Ainda não verificado

- Windows, execução sem Python, geração/homologação de .exe/instalador, reinstalação/atualização/desinstalação: scripts e checklist atualizados; nenhum desses resultados foi alegado como concluído.
- Bambu Studio instalado e abertura real: opcional e pendente no Windows.
- Logo/ícone original como arquivo: importe a marca oficial, sem substituto gerado.
- Inspeção formal com três fotos, pedidos, fluxo comercial/financeiro completo, relatórios/documentos e demais Fases 4–8: não implementados nesta entrega.

O registro preliminar de verificação de peças da Fase 3 não equivale ao controle de qualidade formal da Fase 5. Movimentos de estoque não são caixa ou venda. A Fase 4 depende da aprovação expressa do proprietário.

`start_skill` foi atualizado no rascunho do ambiente; `install_script` anterior foi preservado. Salvar esse rascunho não publicou nem atualizou outras tarefas. Revise e salve as configurações e publique o ambiente para preservar esta preparação.
