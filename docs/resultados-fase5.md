# Validação — Fase 5 / versão 2.4.0 / esquema 5

Validação no ambiente Linux com Python 3.12.14, PySide6 6.8.3, SQLite e dependências fixadas em `requirements-dev.lock`. Dados exclusivamente temporários de QA. Windows não executado.

## Suíte

Comando: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q -o faulthandler_timeout=20`.

Resultado final: **160 passed in 29.81s**, código de saída **0**, sem testes ignorados. Inclui os 128 testes anteriores e 32 novos casos de domínio/interface da Fase 5.

Cobertura funcional:

- Cinco produzidas, uma reprovada, quatro boas; total existente R$ 6,10, referência R$ 11,10, efetivo R$ 1,53/boa e centavos físicos conservados, sem custo duplicado no descarte.
- Falha parcial com progresso ajustável, zero boas sem custo unitário inventado, nova tentativa com custo acumulado e horas debitadas uma vez.
- Lotes mistos com materiais separados, rateio automático/manual documentado, máquina compartilhada; mesmo carretel em dois modelos debitado uma única vez pela soma.
- Saldo insuficiente combinado desfaz tentativas, horas, entradas e consumo. Saldo desconhecido e base de referência preservados.
- Prioridades/reordenação conservam criação; ocupação única por impressora e confirmação repetida bloqueada.
- Inspeção exige checklist completo, justificativa para não aplicável/reprovado, observações leves e três fotos distintas decodificáveis. Falha desfaz registros e limpa cópias de fotos.
- Históricos/invalidade de inspeções preservados. Revalidação de produto/categoria devolve à quarentena. Fotos ausentes/alteradas e dados de produto alterados bloqueiam conclusão/reserva/entrega, inclusive após reserva.
- Reimpressão com código novo/referências atuais, substituição de carretel finalizado e preservação da origem.
- Pedido personalizado associa variante de produção antes de existir estoque, preserva descrição/preço aprovados e permite reserva/entrega após inspeção.
- Cancelamento conserva custo e pode terminar OP existente para estoque; pedido cancelado bloqueia nova OP vinculada.
- Retorno real de uma entre duas peças entregues exige reinspeção, preserva custos/horas e mantém a outra baixada.
- Fotos no backup, restauração de evidência ausente, hash/caminho seguro, problemas vinculados ao produto/OP e migração 4 → 5 com backup prévio.
- Interface real: criação, confirmação, inspeção/fotos e conclusão por formulários; modelos múltiplos e falta de cadastros geram erro recuperável.

Execuções anteriores passaram nas asserções, mas apresentaram código 139 na finalização nativa do Qt. Foram corrigidos o cronômetro de Produção no fechamento e o descarte explícito de todas as janelas Qt antes do encerramento do interpretador no ambiente de testes (`tests/conftest.py`). O erro reapareceu após a primeira correção, portanto aquela execução isolada não foi usada como resultado final. Com ambas as correções, a suíte terminou normalmente com 160 testes e código 0, conforme o resultado final acima. Nenhuma asserção foi removida ou desativada.

## Aplicativo empacotado

PyInstaller gerou novamente `dist/DrHeekLab` com as dependências. Comando de compilação:

`QT_QPA_PLATFORM=offscreen .venv/bin/python -m PyInstaller --noconfirm --windowed --onedir --name DrHeekLab --paths src --collect-all drheeklab packaging/launcher.py`

`QT_QPA_PLATFORM=offscreen dist/DrHeekLab/DrHeekLab --self-test` verifica autenticação, codec PNG/logo temporário de QA, orçamento/pedido, pagamentos parciais/taxas, PDFs versionados, OP com tempo/consumo confirmado, inspeção individual com três fotos e entrega. Resultado: `status: passed`, `version: 2.4.0`, saída 0. Usa exclusivamente diretório temporário; as imagens de QA não representam logo nem fotos reais do negócio.

`pip check`: nenhuma dependência incompatível.

Capturas Qt offscreen de fila e nova OP em 1100×700/850×750 foram inspecionadas visualmente. Não equivalem à homologação visual Windows.

## Entrega e configuração

Código completo em `dist/DrHeekLab-2.4.0-source.zip`, sem banco, dados, credenciais, .venv ou caches. Pacote Linux em `dist/DrHeekLab-2.4.0-linux.zip`; extrair toda a pasta, executar `DrHeekLab/DrHeekLab`. Checksums em `dist/DrHeekLab-2.4.0-SHA256.txt`. Não são instaladores Windows.

Configuração reutilizável da nuvem: `install_script` e `start_skill` salvos como rascunho, com instruções da Fase 5. A persistência não publica nem aplica scripts automaticamente; revisão/publicação pertencem à interface do ambiente.

`packaging/build-windows.ps1`, Inno Setup e workflow Windows atualizados para a versão 2.4.0/Fase 5. Geração do .exe/instalador e homologação em máquina Windows permanecem pendentes; confira `validacao-windows.md`. Não foi feito commit, push ou publicação nesta entrega. Financeiro completo permanece na Fase 6, condicionada à aprovação expressa do proprietário.
