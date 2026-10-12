# Windows 2.8.1 — instalador gerado e validação automatizada aprovada

Execução real GitHub Actions em Windows x64: [run 38299222677](https://github.com/d28ty8rky9-star/drheeklab/actions/runs/38299222677), commit `74ae16be9eec28b0039f2c7019f21cc3aeb6e860`, resultado **success**.

- **250 testes aprovados; 0 falhas, 0 erros, 0 ignorados.** Evidência JUnit em `evidencias-windows-2.8.1/test-results.xml`.
- PyInstaller gerou GUI Windows e verificador de atualização independente; Inno Setup gerou `DrHeekLab-2.8.1-Fase8-Setup.exe`.
- QA do executável e de duas instalações: status passed, versão 2.8.1, dados exclusivamente temporários. Inclui fluxo financeiro/estoque/produção/inspeção, PDFs/Excel/CSV, reinício, backup e restauração criptografada.
- Instalador executado, reinstalado e desinstalado em runner descartável. Rascunho/banco/mídia preservados; backup pré-atualização verificado; backup sem interface e criação/remoção de tarefa Windows aprovados.
- SHA-256 de Setup, GUI e helper conferidos após download; formato PE Windows confirmado. Não são binários Linux renomeados.

## Correções encontradas na execução real

A primeira execução travou após falhas de backup; foi cancelada. O segundo run registrou falhas e timeout. O contexto SQLite transacional não fecha conexões: acrescentado fechamento explícito aos snapshots/verificações/migrações, com regressão mantendo referências vivas.

Depois dessa correção, 237 testes Windows passaram antes da falha no QA de PDF: a última instância nativa Qt mantinha o arquivo aberto durante limpeza temporária. O verificador passou a destruir explicitamente o documento nativo após fechar, com regressão de liberação do arquivo. Essas correções deram origem à 2.8.1. Nenhuma regra financeira ou esquema 7 foi alterado; testes não foram desativados.

## Entrega

Instalador: `dist/windows-2.8.1/installer/DrHeekLab-2.8.1-Fase8-Setup.exe`. Checksum simples: `SHA256-verificado.txt` na mesma pasta. Aplicativo completo: `dist/windows-2.8.1/DrHeekLab/`; manter toda a pasta se usar a distribuição portátil. Artefatos também disponíveis no run acima.

Execute Setup no Windows, abra pelo atalho, escolha **TESTES** e crie sua senha. Valide seus dados e operações antes de usar **PRODUÇÃO**. Não existe senha padrão. Atualização e desinstalação preservam `C:\DrHeekLab`; faça backup externo antes de atualizar.

## Limites da homologação

A validação automatizada Windows foi concluída. Ainda dependem da avaliação prática do proprietário: computador de destino sem Python, usuário comum, comportamento visual em sua máquina, acionamento da tarefa no horário real e arquivos oficiais do logo/ícone. O runner contém Python para compilar e preparar dados; execução do .exe empacotado não comprova sozinha um computador sem Python instalado.

Não houve publicação de release nem mudança de visibilidade do repositório. Builds/correções foram enviados para o repositório autorizado. Relatórios de fases anteriores que indicam ausência de execução Windows são registros históricos; este documento é o estado atual.
