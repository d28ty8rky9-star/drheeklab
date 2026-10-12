# PROMPT PARA CODEX — FINALIZAÇÃO AUTÔNOMA DO DR. HEEK LAB 2.0

## OBJETIVO

Continue o desenvolvimento do **Dr. Heek Lab 2.0** a partir do estado atual do projeto, localizado em:

`/workspace/drheeklab`

O aplicativo está na versão **2.7.0**, com esquema SQLite 7, utilizando Python, PySide6, SQLite, ReportLab, OpenPyXL e PyInstaller.

As fases 1 a 7 foram relatadas como implementadas, e a fase 8 foi parcialmente concluída.

**Sua missão é corrigir as pendências, finalizar o desenvolvimento, testar o sistema e entregar uma versão Windows instalável e funcional.**

## 1. AUTONOMIA PARA EXECUÇÃO

A partir deste momento, você está autorizado a:

- Continuar o desenvolvimento sem solicitar minha aprovação a cada fase.
- Corrigir bugs identificados.
- Ajustar códigos, telas e funcionalidades que apresentem problemas.
- Refatorar trechos de código quando necessário.
- Criar e executar testes.
- Corrigir inconsistências financeiras e de estoque.
- Ajustar o banco de dados utilizando migrações seguras.
- Preparar e executar os processos de empacotamento disponíveis.
- Criar o instalador Windows.
- Atualizar a documentação.
- Avançar automaticamente até a conclusão de todas as tarefas.

**Não interrompa o desenvolvimento para solicitar aprovações intermediárias.**

Quando encontrar um problema técnico, investigue, implemente a solução adequada, execute os testes e continue.

Não faça perguntas sobre decisões técnicas rotineiras que possam ser resolvidas respeitando a especificação existente.

Somente solicite minha intervenção quando for indispensável fornecer credenciais, arquivos externos, autorizações de acesso ou quando uma decisão puder alterar significativamente as regras de negócio.

Não realize publicações públicas, compartilhamento de dados, operações destrutivas irreversíveis ou alterações em serviços externos sem autorização específica.

## 2. PRESERVAR O QUE JÁ FOI DESENVOLVIDO

Não comece o projeto do zero.

Primeiro, examine:

- Código-fonte atual.
- Estrutura do banco de dados.
- Testes existentes.
- Especificação mestre.
- Documentação das oito fases.
- Histórico de versões.
- Scripts de empacotamento.
- Scripts do instalador.
- Workflow do GitHub Actions.

Aproveite tudo o que estiver funcionando corretamente.

Não reescreva módulos apenas por preferência de arquitetura.

Preserve as regras comerciais já aprovadas, especialmente:

- Acréscimo padrão de 200% sobre o custo, resultando em preço sugerido igual a três vezes o custo.
- Custo horário inicial da Bambu Lab A1 Mini de R$ 1,10.
- Cálculo com vários filamentos.
- Preço final manual com desconto calculado automaticamente.
- Separação entre faturamento, recebimento, lucro e fluxo de caixa.
- Controle de custos históricos.
- Estoque físico, reservado e disponível.
- Controle de produção e inspeção individual.
- Histórico financeiro auditável.
- Funcionamento totalmente offline.

## 3. CORRIGIR AS PENDÊNCIAS IDENTIFICADAS

### 3.1. Compatibilidade com Windows

Garantir funcionamento real no Windows.

Verificar:

- PySide6 e bibliotecas Qt.
- Caminhos de arquivos.
- Permissões de leitura e gravação.
- Abertura de arquivos STL e 3MF.
- Geração de PDF.
- Exportação Excel e CSV.
- Funcionamento do SQLite.
- Temas claro e escuro.
- Atalhos.
- Login.
- Reinicialização do aplicativo.
- Persistência de dados.

O sistema deverá funcionar sem instalação manual de Python.

### 3.2. Instalador Windows

Concluir a configuração de PyInstaller e Inno Setup.

Preparar um instalador `.exe` com:

- Nome Dr. Heek Lab 2.0.
- Atalho na área de trabalho.
- Entrada no menu Iniciar.
- Desinstalador.
- Preservação de dados durante atualizações.
- Identificação da versão instalada.

Os dados permanentes deverão permanecer em:

`C:\DrHeekLab`

Não sobrescrever nem excluir dados reais durante instalação, atualização ou desinstalação.

Verificar o funcionamento com usuário Windows comum, sem privilégios administrativos permanentes.

Se houver necessidade de permissões específicas na instalação, implementar a solução mais segura e documentá-la.

### 3.3. Identidade visual

Manter a identidade visual preta, roxa e azul.

Preparar suporte ao logotipo oficial do Dr. Heek Lab e ao arquivo `.ico`.

Se os arquivos oficiais não estiverem disponíveis, não inventar outra marca.

Utilizar identificação provisória e registrar a substituição do logotipo como pendência externa, sem interromper o restante do desenvolvimento.

### 3.4. Backup automático

Aprimorar o sistema para permitir backup diário mesmo quando o aplicativo estiver fechado.

Avaliar e implementar integração com o Agendador de Tarefas do Windows, utilizando um processo seguro de backup SQLite.

Garantir:

- Backup automático.
- Backup manual.
- Backup para pendrive ou HD externo.
- Verificação de integridade.
- Restauração completa.
- Preservação de fotos, STL, 3MF, documentos e banco de dados.
- Registro de erros.
- Recuperação após falhas.

Caso a tarefa agendada não possa ser criada automaticamente, fornecer configuração assistida e documentação.

### 3.5. Segurança dos backups

Implementar opção de backup criptografado com senha, utilizando tecnologia criptográfica reconhecida.

Não utilizar criptografia caseira.

Não armazenar a senha de criptografia em texto puro.

Manter a possibilidade de backup local não criptografado, desde que essa condição seja claramente informada ao usuário.

Testar restauração dos backups criptografados e não criptografados.

### 3.6. Atualizações seguras

Antes de atualizar o sistema:

1. Verificar a versão instalada.
2. Criar backup.
3. Verificar integridade.
4. Validar compatibilidade do banco.
5. Executar migrações necessárias.
6. Confirmar funcionamento.
7. Preservar os dados anteriores em caso de falha.

Implementar recuperação segura quando uma atualização não for concluída.

Não apagar dados existentes.

## 4. AUDITORIA FINANCEIRA COMPLETA

Revisar cuidadosamente os cálculos e corrigir possíveis inconsistências.

Testar:

- Custo de filamentos.
- Custo por hora de impressora.
- Custo por peça.
- Custo de lotes.
- Acréscimo de 200%.
- Descontos.
- Preço final.
- Pagamentos parciais.
- Parcelamentos.
- Taxas de cartão.
- Contas a pagar.
- Contas a receber.
- Cancelamentos.
- Reembolsos.
- Créditos.
- Lucro comercial.
- Fluxo de caixa.
- Compras de materiais.
- Custo dos produtos vendidos.
- Perdas de produção.

**Regra obrigatória:** nenhum custo ou pagamento pode ser contabilizado duas vezes.

Exemplo: comprar filamento representa saída de caixa e entrada de estoque; consumir esse filamento representa custo de produção e baixa de estoque, sem uma segunda saída de caixa.

Preservar valores históricos mesmo quando preços atuais forem alterados.

Utilizar transações SQLite para garantir consistência das operações.

## 5. AUDITORIA DO ESTOQUE E DA PRODUÇÃO

Testar situações reais, incluindo:

- Impressão com um filamento.
- Impressão com vários filamentos.
- Lotes de peças iguais.
- Lotes mistos.
- Impressão parcialmente concluída.
- Impressão com falha.
- Reimpressão.
- Produção para estoque.
- Venda de peça já pronta.
- Reserva de produto.
- Cancelamento de pedido.
- Devolução.
- Descarte.
- Ajuste manual.
- Filamento com peso desconhecido.
- Inspeção de qualidade.
- Rejeição de peça.
- Bloqueio de entrega de produto rejeitado.

Garantir rastreabilidade e consistência dos custos.

## 6. TESTES AUTOMATIZADOS

Manter os 227 testes anteriormente relatados, corrigindo os que eventualmente apresentarem falhas.

Adicionar testes para as correções realizadas.

Executar:

- Testes unitários.
- Testes de integração.
- Testes de banco de dados.
- Testes financeiros.
- Testes de estoque.
- Testes de produção.
- Testes de backup e restauração.
- Testes de atualização.
- Testes de interface, quando possível.
- Testes de empacotamento.

Não considerar o sistema aprovado apenas porque funciona em Linux.

É obrigatório buscar validação no Windows.

## 7. GITHUB ACTIONS E BUILD WINDOWS

Utilizar os workflows existentes e corrigir o que for necessário.

Se houver ambiente Windows disponível, executar o build e os testes nele.

Caso seja necessário GitHub Actions:

- Preparar o workflow Windows.
- Configurar execução automatizada dos testes.
- Configurar geração do executável.
- Configurar geração do instalador.
- Gerar relatório de testes.
- Gerar checksum SHA-256 dos arquivos finais.

Você pode preparar commits locais e arquivos de workflow necessários.

Não faça push, publicação de release nem torne o repositório público sem minha autorização.

Se o build remoto depender de um push que não esteja autorizado, continue com todas as etapas locais possíveis e deixe somente essa ação externa identificada como bloqueio.

**Nunca afirme que executou testes Windows se apenas preparou os scripts.**

## 8. REVISÃO DA INTERFACE

Verificar todas as oito áreas:

1. Início.
2. Vendas.
3. Produção.
4. Produtos.
5. Estoque.
6. Financeiro.
7. Impressoras.
8. Configurações.

Corrigir:

- Botões sem funcionamento.
- Formulários incompletos.
- Erros de navegação.
- Textos cortados.
- Campos desalinhados.
- Problemas de rolagem.
- Tabelas difíceis de visualizar.
- Falhas nos temas claro e escuro.
- Mensagens de erro confusas.
- Problemas de usabilidade.

Priorizar uma interface profissional, mas não gastar tempo excessivo em mudanças puramente estéticas antes de resolver os problemas funcionais.

## 9. EXECUÇÃO CONTÍNUA ATÉ A CONCLUSÃO

Organize internamente as tarefas em uma sequência lógica.

Para cada problema:

1. Identifique a causa.
2. Corrija.
3. Execute os testes relevantes.
4. Confirme que não houve regressão.
5. Atualize a documentação.
6. Continue automaticamente para a próxima tarefa.

**Não pare para perguntar se pode continuar. A continuidade do desenvolvimento já está autorizada.**

Caso haja limite de execução ou contexto, registre o estado atual em um arquivo de continuidade no repositório, com tarefas concluídas, pendências e comandos necessários para retomar.

Não marque tarefas incompletas como concluídas.

## 10. CRITÉRIOS PARA CONSIDERAR O SISTEMA FINALIZADO

O Dr. Heek Lab 2.0 somente poderá ser declarado pronto para utilização real quando:

- As oito áreas estiverem funcionais.
- Os cálculos financeiros estiverem validados.
- O estoque estiver consistente.
- As ordens de produção funcionarem.
- Os documentos forem gerados corretamente.
- O backup e a restauração estiverem testados.
- O banco preservar os dados após reinicialização.
- A atualização não apagar registros.
- O aplicativo executar no Windows.
- O instalador Windows tiver sido gerado.
- O instalador tiver sido testado.
- O aplicativo funcionar sem Python instalado.
- Os testes críticos forem aprovados.
- Não existirem defeitos críticos conhecidos.

Se alguma dessas condições não puder ser verificada por limitação do ambiente, informe expressamente a pendência. Não invente resultados.

## 11. ENTREGA FINAL

Ao concluir, apresente:

**A. Resumo do trabalho**

- Problemas encontrados.
- Correções realizadas.
- Funcionalidades finalizadas.
- Melhorias implementadas.

**B. Resultados dos testes**

- Quantidade de testes aprovados.
- Quantidade de testes com falha.
- Ambiente em que foram executados.
- Evidências de validação Windows.

**C. Arquivos finais**

- Instalador Windows `.exe`, se gerado.
- Executável Windows, se gerado.
- Código-fonte atualizado.
- Checksums SHA-256.
- Documentação.

**D. Instruções para o proprietário**

Explique de forma simples:

1. Como instalar.
2. Como abrir.
3. Como cadastrar os primeiros dados.
4. Como fazer backup.
5. Como atualizar.
6. Como restaurar os dados.

**E. Pendências restantes**

Informe apenas o que realmente depender de acesso externo, arquivo fornecido pelo proprietário ou validação em equipamento Windows indisponível no ambiente.

## ORDEM FINAL

**INICIE AGORA.**

Continue a partir da versão atual do Dr. Heek Lab 2.0.

Audite, corrija, teste, integre, empacote e finalize o sistema.

Não solicite aprovações intermediárias para tarefas técnicas rotineiras.

Não interrompa a execução após concluir uma etapa.

Trabalhe até entregar a versão mais completa, estável e validada possível.

**Depois que o programa estiver pronto, eu farei a avaliação prática e solicitarei eventuais ajustes de funcionalidades e aparência.**