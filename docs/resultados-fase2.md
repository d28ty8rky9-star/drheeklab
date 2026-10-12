# Resultados de validação — Fase 2 / versão 2.1.0

Registro histórico da entrega anterior. Resultados atuais da versão 2.2.0 em `resultados-fase3.md`.

Ambiente: Linux, Python 3.12.14, PySide6 6.8.3, pytest 8.3.5. Dados de testes sempre temporários; nenhum banco de produção foi utilizado.

## Resultado

`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q -o faulthandler_timeout=15`: **67 testes passaram**.

Inclui os testes da base, os cenários matemáticos/domínio da Fase 2 e a integração com a interface Qt:

- A1 Mini com parâmetros exatos e preservação de edições após reinício/migração idempotente.
- Custo por grama, componentes horários independentes por máquina, vários filamentos, auxiliares e quantidade.
- Padrão 200% = custo × 3; final 35 / sugerido 90 / custo 30 → redução 55 / 61,11% / resultado à referência 5, sem desconto duplicado.
- Preço final acima, igual e abaixo do sugerido; preço final zero; bases zero com percentual explicitamente não aplicável.
- Arredondamento HALF_UP e soma reconciliável dos componentes; entrada brasileira; rejeição de NaN, infinito, float, números malformados, excesso de precisão, negativos e quantidade inválida.
- Aquisição gratuita independente da referência; custo de aquisição desconhecido não é tratado como zero.
- Cadastro, validação e edição via formulários Qt; manutenção, correção justificada de tempo e configuração persistente.
- Arquivamento/restauração de cadastros conservando histórico; alerta de saldo baixo sem inventar saldo de carretel aberto desconhecido.
- Previsão não consome saldo nem soma tempo; confirmação real única, consumo auditado e atualização de minutos.
- Saldo insuficiente e falha na auditoria revertem toda a transação, incluindo carretéis anteriores, horas e snapshot real.
- Carretel de saldo desconhecido permanece NULL após consumo; conhecido zerado é finalizado.
- Referências e preços históricos não são alterados por edições futuras.
- Rascunho de cálculo salvo após inatividade e recuperado após reiniciar; sugestão do último carretel.
- Migração real do esquema 1 para 2 preserva senha, configuração e anotações. Backup de esquema 1 restaura e migra na próxima abertura; backup de esquema 2 preserva cadastros, cálculos, consumos e minutos.
- Correção do callback de backup que podia consultar banco fechado: o encerramento para os timers e callbacks pendentes verificam o estado da janela.

## Pacote e dependências

Instalação editável atualizada para 2.1.0; `pip check` não encontrou dependências incompatíveis. PyInstaller gerou `dist/DrHeekLab/DrHeekLab`, com suas dependências na mesma pasta.

O pacote congelado Linux foi iniciado com Qt offscreen: CLI retornou sucesso, login permaneceu aberto, banco foi criado com esquema 2, A1 Mini e parâmetros aprovados, sem senha/usuário padrão. Processo encerrado após essa verificação. Login autenticado, cadastros e cálculos foram exercitados no código via pytest; o teste do pacote não automatizou esses fluxos autenticados.

## Limitações e próximas validações

- Executável Linux não é .exe Windows. Scripts PyInstaller/Inno Setup e workflow Windows foram atualizados, mas ainda não executados em Windows.
- Homologação do instalador, Windows sem Python, atualização/desinstalação e ícone oficial seguem pendentes. Use `validacao-windows.md`.
- Logo da conversa continua como referência; importe o arquivo original em Configurações → Marca. Não foi criado substituto.
- Confirmação da Fase 2 consolida custos/consumos informados; não substitui OP, falhas, qualidade ou módulos de caixa. A comparação de execução usa referências congeladas; a valoração de aquisição é apresentada separadamente.
- Datas de aquisição/compra não conhecidas ficam vazias; tempo usa resolução de um minuto; gramas até três casas e referência por grama até seis.
- Confirmação de consumo é única e preservada; correções de saldo/tempo são feitas com justificativa e auditoria. Fluxo controlado de correção de OPs pertence à Fase 5.
- Fases 3–8 não iniciadas. Fase 3 depende da aprovação expressa do proprietário, conforme a especificação mestre.

`start_skill` foi atualizado no rascunho do ambiente; `install_script` existente foi preservado. Salvar o rascunho não publicou nem atualizou outras instâncias. Revise e salve as configurações e publique o ambiente quando desejar preservar esta preparação.
