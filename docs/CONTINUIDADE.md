# Estado atual — Produção unificada; pacotes somente a pedido

Produtos e Produção agora são uma área única Produção, em uma tela com catálogo à esquerda e fila/inspeção à direita. Selecionar peça → Produzir esta peça abre formulário preenchido com variante, arquivo preferencial e recomendações; ficha de variantes/fotos/STL/3MF permanece acessível. Dados, schema, custos, estoque e inspeção preservados. Variante arquivada selecionada é bloqueada, sem substituir por outra. Menu com sete áreas e busca/navegação ajustadas.

257 testes locais completos e três testes finais de fluxo aprovados. Windows run 38483313429: testes aprovados sobre 2ebc0b40cf40b7bc29eaa166dc0bfa8e932a823a. Pacote ignorado e zero artefatos criados. Nenhum ZIP/instalador gerado. Relatório docs/producao-unificada.md e capturas docs/capturas-producao-unificada/. Código no GitHub; o último instalador entregue mantém a interface anterior.

PREFERÊNCIA ATUAL, que substitui a antiga: implementar/testar/enviar alterações ao GitHub, mas somente gerar ZIP ou instalador quando o usuário pedir explicitamente. Workflow push/PR apenas testa; pacote só via workflow_dispatch com gerar_pacote=true e pedido explícito. Não disparar esse input sem autorização. Usar checkout existente; preservar C:\DrHeekLab e dados, versões e documentos históricos. Versão do código continua 2.9.1 em desenvolvimento.

Notas seguintes são históricas.

# Nome atual — Dr. Heek Lab, versão 2.9.1

Pedido de 13/10/2026: nome do produto Dr. Heek Lab, sem “2.0”; versão continua 2.9.1. Nome atualizado em interface, instalador, propriedades do executável e novos documentos. PDFs e dados históricos preservados. A cada alteração, o usuário exige ZIP completo para reinstalar, sem copiar modificações para uma pasta antiga. Preservar C:\DrHeekLab (dados), excluir somente a pasta extraída da entrega anterior. LEIA-ME.txt incluído no pacote.

Validação: 65 testes locais relacionados aprovados; 255 testes Windows aprovados, zero falhas/erros/pulos. Instalação/reinstalação/backup/preservação/agendamento/desinstalação aprovados. Run 38403682558; build a36711e0d22e9a743695cdc3bb2e1e8a73b1fa51; artifact 11817081703 (DrHeekLab-Windows-2.9.1-NomeAtualizado). Nome no metadata do GUI e hashes verificados. ZIP completo local: dist/DrHeekLab-2.9.1-NomeAtualizado-Windows.zip. Notas seguintes históricas.

# Estado atual — marca oficial e revisão final 2.9.1

Logotipo fornecido no ZIP incorporado no canto superior esquerdo, nome e versão abaixo; oito ícones da folha original no menu. Início sem os blocos inferiores/alerta amarelo; informações e anotações preservadas em Configurações → Sobre. Ícone oficial incorporado no executável, instalador e janela. Menu com rolagem em janelas menores. Nenhuma regra, fórmula ou migração alterada.

Linux 255 testes aprovados; Windows 255 aprovados e instalação/reinstalação/backup/preservação/agendamento/desinstalação aprovados. Run 38319542522, commit compilado 09423e0ea372a16911a2c766348d688b9ec08dfc, artifact 11779025415 (DrHeekLab-Windows-2.9.1). Hashes verificados, sete frames do ICO presentes no GUI e Setup e três assets com hashes iguais aos do source. Installer local dist/windows-2.9.1/installer/DrHeekLab-2.9.1-Fase8-Setup.exe. A pendência de arquivo oficial foi resolvida. Avaliação prática do proprietário continua pendente.

Veja docs/ajustes-marca-2.9.1.md, docs/capturas-2.9.1/ e docs/evidencias-2.9.1/. Notas seguintes são históricas.

# Estado atual — modernização visual 2.9.0

As oito áreas foram modernizadas com tema compartilhado, cartões, botões/ícones/tabelas/formulários padronizados, filtros, gráficos sobre dados reais, galeria/tabela sincronizada, progresso por peças aprovadas e configurações por assunto. Nenhuma fórmula, migração ou regra de negócio foi alterada.

Linux: 254 testes aprovados. Windows: 254 testes aprovados, pacote e instalação/reinstalação/backup/preservação/agendamento/desinstalação aprovados. Run 38306782123, código compilado c37b967a04fd227771a74cd86dcee5aec31659f3, artifact 11772568668 (DrHeekLab-Windows-2.9.0). Installer local dist/windows-2.9.0/installer/DrHeekLab-2.9.0-Fase8-Setup.exe; hashes verificados. Avaliação manual do proprietário e importação do logotipo oficial permanecem pendentes. As capturas usam somente dados demonstrativos temporários.

Veja docs/modernizacao-visual-2.9.0.md e docs/evidencias-2.9.0/. Os registros seguintes são históricos.

## Atualização mais recente — Windows 2.8.1

Instalador gerado e validação automatizada Windows aprovada no run 38299222677 / commit74ae16b: 250 testes, zero falhas/erros/ignorados. Artefatos e hashes conferidos em dist/windows-2.8.1. Correções SQLite e QtPdf implementadas. Push e execução para homologação foram autorizados; release/mudança de visibilidade não. Avaliação prática do proprietário e marca oficial permanecem pendentes. Leia resultados-windows-2.8.1.md; estados anteriores abaixo são históricos.

# Continuidade — Dr. Heek Lab 2.8.0

## Estado preservado

- Checkout: `/workspace/drheeklab`; versão 2.8.0, esquema 7.
- Autonomia técnica concedida; não exigir nova aprovação por fase. Preservar regras e dados, não recomeçar o projeto.
- Implementados backup AES-GCM/scrypt, suporte .hbk/ZIP, agendamento Windows assistido, CLI de backup com trava, preflight de atualização e proteção de saída parcial/symlinks.
- Suíte Linux: 248 testes aprovados, saída 0. QA do código e binário GUI Linux aprovado, incluindo criptografia/restauração. Executável de preflight Linux gerado para verificar o mesmo código independentemente do pacote GUI.
- Pip check aprovado. Dependências fixadas, incluindo cryptography/cffi/pycparser. Documentação e evidências preservadas.
- Preparar/preservar commit local autorizado pelo proprietário. Não fazer push, release ou publicação externa sem autorização específica.

## Comandos reproduzíveis

```bash
cd /workspace/drheeklab
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/python -m pip check
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q -o faulthandler_timeout=20
QT_QPA_PLATFORM=offscreen .venv/bin/python -m drheeklab --self-test --self-test-report /tmp/qa.json
QT_QPA_PLATFORM=offscreen .venv/bin/python -m PyInstaller --noconfirm --clean --windowed --onedir --name DrHeekLab --paths src --collect-all drheeklab packaging/launcher.py
.venv/bin/python -m PyInstaller --noconfirm --clean --onefile --console --name DrHeekLabUpdate --paths src packaging/update_preflight.py
QT_QPA_PLATFORM=offscreen dist/DrHeekLab/DrHeekLab --self-test --self-test-report /tmp/qa-binario.json
```

Não repetir testes/builds já aprovados sem alteração, falha ou motivo novo. Dados de QA sempre temporários, sem abrir PRODUÇÃO real. Não usar credenciais em texto/argumentos.

## Pendências externas

1. Disponibilizar Windows ou autorizar envio do código ao GitHub para executar `.github/workflows/windows.yml`. Nenhum push/runner/Windows build ocorreu; ambiente atual é Linux.
2. Gerar executável/instalador Windows, investigar qualquer falha real e repetir somente verificações afetadas. Não confundir Linux ELF com .exe Windows.
3. Homologar usuário comum, máquina sem Python, atalhos, resoluções, tarefas com aplicativo fechado, criptografia, atualização/preflight, mídias e erros de disco/permissão. Preencher evidências, não apenas marcar scripts como aprovados.
4. Importar logo PNG/JPEG e ícone .ico oficiais quando fornecidos. Ausência não bloqueia desenvolvimento; não inventar marca.

Rascunho de nuvem não equivale a publicação, execução automática ou restauração comprovada em nova tarefa. Código/pacotes locais permanecem disponíveis; consultar `git log` para commits locais. Não declarar o sistema Windows pronto até cumprir os critérios da solicitação.
