# Fase 8 — finalização / 2.8.0 / esquema 7

Avanço autorizado pelo proprietário. Finalização implementada e validada em Linux; **conclusão para uso real no Windows permanece pendente de geração e homologação do instalador, computador de destino sem Python e ícone oficial**. Não há mudança nas regras financeiras nem no esquema 7.

## Funcionalidades integradas

O programa reúne oito áreas: Início, Vendas, Produção, Produtos, Estoque, Financeiro, Impressoras e Configurações. Os fluxos de cadastro, precificação, venda/pagamento/entrega, produção/inspeção individual, custos/caixa/obrigações, documentos, alertas, auditoria/lixeira e backup/recuperação estão descritos no manual e nas Fases 2–7.

**Buscar**, no cabeçalho, localiza clientes, pedidos, orçamentos, produtos, arquivos STL/3MF, filamentos e OPs por nome/código/telefone/texto. Busca literal, sem interpretar `%`, aspas ou comandos SQL; mantém identificação de arquivados. Até 200 resultados, refináveis pelo texto. Selecione o resultado e use **Abrir área do selecionado**; o ID/código encontrado permite localizar o registro no módulo. Não altera dados nem abre arquivo sem verificação.

**Nova produção**, em Início, abre o formulário de OP. **Sobre o programa**, em Configurações, apresenta versão atual e histórico de alterações disponível offline no pacote.

## Instalação Windows (após gerar e homologar)

1. Confira versão e SHA-256 do instalador. Use Windows x64, mantenha backup externo e feche o aplicativo.
2. Execute `DrHeekLab-2.8.0-Fase8-Setup.exe`; instalação pede administrador, operação diária usa usuário comum. Arquivos ficam em Program Files; atalhos no menu e na área de trabalho.
3. Abra pelo atalho, escolha TESTES e crie senha própria. Para dados reais, escolha PRODUÇÃO: banco e senha separados, sem transferência automática dos testes.
4. Importe o logo original PNG/JPEG em Configurações. Não existe senha padrão. O ícone oficial `.ico` precisa ser fornecido para finalizar a identidade do instalador.

O pacote Linux não executa no Windows. O usuário final do instalador não precisa instalar Python. Este requisito ainda precisa ser comprovado em máquina de destino sem Python.

## Atualização e recuperação

Crie backup completo verificado e externo do ambiente correto, feche o aplicativo e instale a nova versão. A reinstalação substitui binários, preservando `C:\DrHeekLab`. A versão 2.8.0 mantém esquema 7; abertura de esquemas anteriores exige backup completo antes de migração transacional. Confira senha, cadastros, estoque, financeiro e documentos após abrir; nunca apague banco para solucionar falha.

Desinstalação remove arquivos do programa/atalhos, preservando dados permanentes. Não apaga fotos, projetos, documentos ou backups. Para transferência ou falha de abertura, use restauração verificada com senha/confirmacão; veja `fase7.md`. Estado anterior permanece em rollback. Não rebaixe automaticamente banco mais novo nem restaure backup de TESTES em PRODUÇÃO.

## Verificação técnica e liberação

`--self-test` usa exclusivamente diretório temporário. `--self-test --self-test-report caminho/qa.json` grava resultado verificável, inclusive quando o executável Windows não possui console. Não aceita `--environment`/`--data-dir`. Falha retorna saída 1 e resultado failed; escrita do relatório também precisa funcionar. O teste verifica reinício/persistência de senha/tema/rascunho, consistência financeira, documentos e transferência de backup.

`packaging/build-windows.ps1` instala dependências fixadas, executa pip check e a suíte completa, compila, executa QA do binário e confere status/versão/persistência. Só então gera instalador e SHA-256. Ícone original opcional para build técnico, obrigatório para identidade final:

```powershell
./packaging/build-windows.ps1 -IconPath C:\caminho\marca-oficial.ico
```

Workflow Windows também prepara Inno Setup e testa instalação/reinstalação, QA do aplicativo instalado, desinstalação e preservação de arquivo sentinela em dados permanentes. `test-windows-installer.ps1` só executa em runner CI Windows descartável; não é ferramenta para o computador do negócio. Gera relatórios/logs como artefatos. Nenhum workflow foi disparado nesta sessão e não houve push.

Homologação manual continua obrigatória: Windows sem Python, usuário comum, atalhos, oito áreas, resoluções/temas, fotos reais, logo/ícone oficiais, PDFs/Excel, impressora e arquivos, atualização e cenários de erro. Registre evidências em `homologacao-windows.md`, seguindo `validacao-windows.md`. Geração ou QA automatizado sozinho não autoriza lançamento.

## Limitações conhecidas

- Windows e instalador ainda não gerados/homologados neste ambiente Linux; script PowerShell/Inno Setup revisado, sem execução local.
- Logo da conversa não disponível como arquivo no checkout. Importação aceita original; documento sem logo indica revisão. Nenhuma marca substituta criada.
- Backup automático funciona com aplicativo aberto ou por tarefa Windows configurada, enquanto usuário conectado. Veja `finalizacao-autonoma.md`. Arquivos não são criptografados pelo login; proteja backups e acesso ao computador.
- Operação concorrente no mesmo ambiente bloqueada. Bambu Studio opcional; fatiamento e medições são manuais.
- Relatórios gerenciais/comprovantes não são fiscais; procedimentos não declaram certificação ISO. Exceções de revalidação, perdas e CPV estão nos manuais das fases.
- Exclusões da especificação permanecem: modelagem cobrada, pausas detalhadas, edição de pedidos aprovados, pequenos retrabalhos financeiros, QR/etiquetas, integração obrigatória com máquinas/serviços online e migração do programa antigo.

Resultados reproduzíveis em `resultados-fase8.md`; cobertura dos critérios obrigatórios em `matriz-testes.md`. A liberação Windows exige completar a homologação pendente.

A finalização autônoma acrescentou criptografia, agendamento e verificação pré-instalação: veja `finalizacao-autonoma.md` e `resultados-2.8.0.md`.
