# Homologação Windows — ainda não executada

Use Windows x64 em máquina de testes, sem dados reais. Não liberar só porque PyInstaller/Inno Setup concluíram.

- Execute build-windows.ps1: testes devem passar e impedir build quando falham.
- Instale Setup.exe, abra pelo atalho em usuário comum, sem Python instalado no computador de destino.
- Escolha TESTES, cadastre senha, confirme recusa de senha errada e sucesso com senha correta.
- Navegue por oito áreas; confirme todos os módulos integrados e as limitações declaradas.
- Mude tema, recolha menu, escreva anotação, feche e reabra; confirme persistência.
- Troque senha: antiga deve falhar, nova deve entrar após reinício.
- Importe logo original e verifique proporção, tema claro/escuro e resoluções 1366×768 e 1920×1080.
- Abra PRODUÇÃO e confirme banco/senha/dados independentes dos testes; a A1 Mini inicial é o único cadastro pré-configurado.
- Crie backup externo, altere notas e logo, restaure; confirme notas/logo/senha originais e preservação da pasta rollback.
- Backup corrompido ou de outro ambiente deve ser recusado sem mudança nos dados atuais.
- Confirme backup diário, integridade SQLite e logs de erro sem senha.
- Reinstale/atualize, confirme dados; desinstale, confirme preservação de C:\DrHeekLab.
- Registre Windows/build, resultado de cada item e eventuais erros. A Fase 8 foi autorizada. Aprovação de lançamento depende dos resultados deste roteiro.

A homologação deve também verificar permissões da pasta de dados e restauração com disco cheio, acesso negado e arquivo em uso. Feche outras instâncias antes de restaurar; uso concorrente não está suportado.

## Validação adicional da Fase 2

- Confira migração da versão 2.1.0/esquema 2 para 2.2.0/esquema 3. Atualize a partir de banco Fase 1 com notas/senha e confirme preservação e snapshot pré-migração.
- Confira A1 Mini: R$ 2.400; componentes 0,75/0,10/0,25; total R$ 1,10/h. Edite e reinicie: edição deve persistir.
- Cadastre material comprado, gratuito com referência positiva e aberto com saldo desconhecido. Confira custo de aquisição separado da referência.
- Calcule vários filamentos, auxiliares e múltiplas peças. Exemplo custo 30/sugerido 90/final 35 deve mostrar redução 55, 61,11% e resultado 5.
- Salve previsão: saldo/horas não devem mudar. Confirme tempo/gramas reais no Histórico: consumo/horas devem ocorrer uma única vez.
- Tente saldo insuficiente: nenhum saldo/hora deve mudar. Consuma carretel desconhecido: saldo deve permanecer desconhecido.
- Altere referências atuais: histórico confirmado deve continuar com preços originais.
- Confira alerta de 100 g e sua configuração; arquive/restaure cadastros mantendo histórico.
- Reinicie com rascunho de cálculo; confirme recuperação. Faça backup, restaure e confira cálculos, consumos, cadastros e horas.

## Validação adicional da Fase 3

- Cadastre produto, variante, parâmetros manuais, custos próprios e variante ligada a cálculo. Confira código crescente e persistência após reinício.
- Importe fotos PNG/JPEG reais e arquivos STL/3MF em duas versões. Confira principal/preferencial, versões antigas preservadas e busca na galeria.
- Configure executável Bambu Studio instalado e abra o projeto real. Confirme que nenhum tempo/consumo é extraído automaticamente.
- Cadastre auxiliares, registre consumo e ajuste justificado; recuse saldo insuficiente e unidade alterada com saldo positivo.
- Registre entrada de três peças por custo total R$ 10,01: custos unitários 3,34 / 3,34 / 3,33. Soma deve ser exata.
- Produção para estoque deve reaproveitar cálculo confirmado sem novo consumo/tempo; o mesmo cálculo não pode gerar outra entrada.
- Uso pessoal não pode ser reservado antes de nova verificação. Rejeição deve manter indisponibilidade.
- Reserve duas de três: físico 3 / reservado 2 / disponível 1. Libere: físico 3 / reservado 0 / disponível 3. Baixa posterior deve ocorrer uma vez.
- Descarte registra motivo/data/observação/custo existente; peça descartada não pode ser descartada novamente.
- Arquive/restaure sem apagar arquivos e estoque; arquivamento com reserva ativa deve ser bloqueado.
- Faça backup completo e restaure fotos, versões, variantes, peças, reserva e perdas. Arquivo atual ausente não pode impedir restauração de ZIP anterior íntegro; confirme preservação do estado anterior em rollback.
- Execute em tema claro/escuro e 1366×768/1920×1080. Inspeção formal com três fotos permanece pendente da Fase 5.

## Validação adicional da Fase 4

- Build deve passar pytest e DrHeekLab.exe --self-test antes de gerar instalador. Repita --self-test em máquina de destino sem Python; dados de produção não podem ser tocados.
- Migre esquema 3 para 4 e confira senha, produtos, arquivos, custos e estoque preservados.
- Cadastre cliente, orçamento com vários itens/anexos e validade sete dias/sem validade. Antes da aprovação, caixa e estoque não podem mudar.
- Aprove orçamento sem redigitar. Confira PED-AAAA-NNNN, preços preservados e reserva única; falta de estoque deve reverter a aprovação completa.
- Venda 100 com entrada 30 e duas parcelas 35: confira previsão versus recebido. Edite parcelas para 20/50 e teste soma inválida.
- Registre pagamento 35 com taxa 1,05: líquido 33,95, saldo do cliente reduzido em 35. Confira alocação aos itens mais antigos, frete e parcelas.
- Abra PDFs: logo original, cliente, frete/total/pagamentos/saldo/QUITADO; nenhum custo interno ou desconto automático. Novos recebimentos não sobrescrevem versões anteriores.
- Vincule produção/cálculo, receba peças e reserve; envie e entregue com rastreio/prova. Baixa ocorre uma vez e reserva vinculada não pode ser baixada pela área Estoque.
- Cancele com reembolso/crédito/retenção justificada: histórico/custos permanecem, saldo exigível zero, reservas ativas liberadas, peças já enviadas não retornam sozinhas.
- Aplique crédito em outro pedido sem nova entrada em caixa. Não converter crédito aplicado em reembolso de dinheiro não recebido.
- Confirme retorno físico de peças canceladas: custos antigos preservados, nova verificação obrigatória, repetição bloqueada.
- Confirme backup/restauração de clientes, pedidos, pagamentos, parcelas, crédito, PDFs e anexos. Reabra após falha/fechamento e verifique rascunho de venda.
- Homologue temas/resoluções, abrir PDF no visualizador Windows e operação sem Python.


## Validação adicional da Fase 5

- Criar OP para item aprovado e para estoque, selecionando versão STL/3MF, parâmetros, responsável e carretéis reais.
- Criar lote com dois modelos e conferir custo único de máquina e soma do rateio. Justificar rateio manual.
- Reordenar alta/normal/baixa sem alterar criação. Impedir duas OPs simultâneas na mesma impressora.
- Confirmar tempo e consumo uma vez; segunda confirmação bloqueada. Saldo insuficiente desfaz toda a tentativa.
- Falha parcial: ajustar gramas sugeridas pelo progresso, registrar motivo/perdidas e conferir custos sem somar perda novamente.
- Inspecionar individualmente: bloquear checklist incompleto, não aplicável sem justificativa, fotos ausentes/duplicadas/inválidas; aceitar frente/verso/detalhe reais.
- Produzir cinco, reprovar uma, aprovar quatro. Concluir e verificar custo efetivo das quatro e estoque disponível. Reprovada não pode ser reservada.
- Reimprimir com código novo, referências atuais e substituição de carretel; não alterar origem.
- Alterar produto/parâmetros: bloquear reserva/entrega até revalidação e nova inspeção. Não alterar custos de peças já entregues.
- Devolver uma entre duas peças entregues, reinspecionar e conferir que a outra permanece baixada.
- Abrir histórico/fotos no aplicativo padrão Windows; consultar problemas por produto e PO-001–012/FR-001.
- Backup completo/restauração com fotos, atualização de esquema 4 para 5 e isolamento TESTES/PRODUÇÃO.


## Validação adicional da Fase 6

- Conferir abertura, tema e navegação do Financeiro em 1100×700, incluindo rolagem das abas.
- Criar conta de R$ 10,01 em três parcelas; editar valores/datas, pagar parcial e verificar pendente/parcial/quitado/atrasado.
- Registrar pagamento com taxa e comprovante PDF/PNG/JPEG; abrir cópia gerenciada e conferir backup/hash.
- Comprar carretel com obrigação/pagamento; consumir em OP e conferir que caixa não sai novamente. Vínculo de carretel existente preserva saldo.
- Comprar material auxiliar; renomear categoria e repetir compra corretamente. Conta antiga mantém classificação.
- Registrar aporte e retirada, conferir que não mudam venda/despesa operacional; estornar mantendo ambos os registros.
- Vender peça pronta e conferir CPV da baixa histórica, sem novo consumo. Cancelar não inventa retorno; devolução real reverte CPV original.
- Conferir tentativa totalmente perdida na OP original e reimpressão em nova OP: resultado inclui custo da origem e CPV novo, sem nova saída de caixa. Retry na mesma OP reverte perda quando absorvida no custo das boas.
- Conferir falha de OP absorvida nas boas e descarte sem custo adicional. Descarte de estoque não absorvido baixa custo sem caixa.
- Filtrar datas/cliente/produto/impressora/situação; dívida anterior aparece no saldo final. Caixa/despesas gerais continuam explicitamente consolidados.
- Ratear um centavo recebido em item produzido em duas impressoras; somas de recebimento e saldo devem ser exatas.
- Exportar CSV/Excel e abrir no Excel Windows. Descrição começando por '=' permanece texto, sem fórmula; conferir inteiros monetários em centavos.
- Backup completo/restauração dos comprovantes e migração 5 → 6; ambientes TESTES/PRODUÇÃO separados.
- Executar `--self-test` no .exe gerado: contas/aportes/CPV/caixa/reconciliação, PDF de comprovante e reabertura de Excel/CSV devem passar antes do instalador.


## Validação adicional da Fase 7

- Abrir central de documentos e emitir PDF financeiro com filtros, relatório de OP com FR-001/fotos e catálogo somente das variantes selecionadas.
- Importar logo original e confirmar marca/identidade nos PDFs. Sem logo, revisão é explicitamente identificada. Conferir catálogo com preço escolhido, sem custo interno.
- Alterar cadastro/preço/logo/parâmetros e confirmar bytes/conteúdo do PDF antigo intactos; reemissão cria versão nova. Exportar cópia e compartilhar manualmente como PDF.
- Alertas de filamento conhecido baixo, recebimentos/contas vencidos/próximos, entrega pendente, manutenção e orçamento. Ler/adiar não paga nada; mudança/recorrência volta a alertar.
- Lixeira: arquivar/restaurar com motivo, manter arquivos, restaurar pai antes de dependentes e bloquear versão em OP ativa. Cancelamentos não revivem.
- Auditoria filtrável, valores anteriores/novos e CSV com texto literal.
- Backup diário/manual em pendrive/HD; conferir inclusão dos novos PDFs, mídias arquivadas e hashes.
- Atualizar banco 6 → 7: verificar backup completo anterior e original preservado em falha. Nunca apagar dados para resolver erro.
- Copiar backup para outro computador, restaurar com confirmação e senha, conferir caminhos relativos, documentos e dados.
- Simular banco corrompido em TESTES: recuperação pela tela inicial, sem comandos; confirmação negativa não substitui dados. Recuperação positiva preserva os bytes originais em rollback.
- Simular falha de cópia: árvore original retorna íntegra. Rejeitar backup de outro ambiente/esquema mais recente.
- Executar `--self-test` no pacote Windows gerado antes do instalador; conferir PDFs/backup/transferência além dos fluxos financeiros anteriores.

## Validação adicional da Fase 8

- Confirmar versão 2.8.0, histórico offline em Sobre, botão Buscar e atalho Nova produção. Busca deve localizar os sete tipos, tratar % e aspas literalmente e identificar arquivados.
- Conferir oito áreas em tema claro/escuro e resoluções aprovadas. Conferir legibilidade dos PDFs, datas, moeda e abertura dos projetos nos aplicativos padrão.
- Executar `--self-test --self-test-report C:\pasta-de-QA\resultado.json`; saída 0, status passed e versão 2.8.0. Usar pasta de QA gravável, sem dados reais.
- Conferir relatórios do runner de instalação/reinstalação/desinstalação, hashes, persistência e preservação dos dados; esse teste automatizado não substitui inspeção manual.
- Abrir pelo atalho como usuário comum em computador sem Python; importar logo original/ícone oficial, reiniciar, confirmar senha e operações principais. O runner de build tem Python, portanto não comprova sozinho esse requisito.
- Preencher `homologacao-windows.md` e registrar responsável/data/versão do Windows, hashes e cada resultado. Bloquear lançamento enquanto houver falha ou item não executado.

## Finalização autônoma — 2.8.0

- Criar/restaurar ZIP e .hbk; senha distinta do login, senha errada, arquivo adulterado, cancelamento e dados originais intactos.
- Agendar por usuário comum, conferir privilégio normal/sem senha no XML, fechar aplicativo e aguardar execução; registrar resultado real do Agendador. Usuário desconectado/PC desligado não são execução garantida; confirmar retomada ao entrar no Windows.
- Disco externo ausente/disco cheio: tarefa registra erro, preserva banco, não anuncia backup incompleto como válido.
- Atualizar com banco e mídias reais de TESTES: preflight deve gerar backup antes de substituir binários; banco danificado, esquema mais novo ou instância aberta bloqueiam instalação. Propriedades do .exe mostram versão 2.8.0.
- Conferir preservação das permissões de pasta existentes e operação como usuário comum. Instalação nova usa pasta padrão com escrita aos usuários locais; restrinja ACL para contas autorizadas conforme necessidade.
- Remover tarefa em Configurações antes de desinstalar; dados permanecem. Tarefas de usuário não são apagadas indiscriminadamente pelo instalador.
