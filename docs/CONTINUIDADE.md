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
