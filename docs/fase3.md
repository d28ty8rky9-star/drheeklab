# Fase 3 — produtos, estoque e arquivos 3D

Versão 2.2.0, esquema SQLite 3 — registro da Fase 3. A Fase 4 já foi autorizada e implementada; consulte `fase4.md` para vendas e reservas vinculadas a pedidos.

## Produtos e variantes

Em **Produtos**, cadastre nome, descrição, categoria decorativa/funcional/mista, impressora e filamento recomendados, parâmetros manuais de fatiamento, tempo estimado, custo/preço por peça e observações de qualidade. Campos monetários vazios significam **não informados**, não custo zero. O código automático é `MOD-0001`, crescente e não reutilizado; cada modelo inicia com variante Padrão.

Use Variantes para tamanhos, cores e materiais com custos próprios. Custo/preço vazios herdam os dados atuais do produto e são identificados na tabela; valores próprios prevalecem. Ao selecionar um cálculo da Fase 2, os valores unitários são copiados e o snapshot original é preservado. Alterações futuras no produto ou nas referências não mudam esses valores copiados nem os custos já atribuídos a peças físicas.

A galeria mostra as fotos reais importadas e pesquisa código, nome, descrição, observações e atributos das variantes, com filtro por categoria. Modelos sem foto são identificados explicitamente. Não há fotos artificiais cadastradas automaticamente.

Produtos e variantes podem ser arquivados e restaurados na lixeira com justificativa. Arquivar não apaga fotos, versões, custos ou peças. Reservas ativas devem ser liberadas antes de arquivar. Estoque físico de registros arquivados continua visível; restaure antes de novas entradas/reservas/liberações por verificação.

## Fotos e arquivos

Na aba Fotos, importe PNG/JPEG válido; a primeira foto é principal e a escolha pode ser alterada. Cada importação cria uma cópia própria no armazenamento do ambiente. O arquivo original escolhido permanece intacto.

Na aba STL/3MF, cada importação cria uma versão numerada, com data, nome original, observações, caminho próprio e SHA-256. A última versão é sugerida como preferencial; é possível escolher uma versão anterior. O programa não sobrescreve as anteriores. Arquivos STL/3MF são armazenados como documentos fornecidos pelo usuário; não há análise automática universal de malha, validade do fatiamento, tempo ou consumo.

**Abrir no Bambu Studio** utiliza o executável instalado, configurável em Configurações. A integração é opcional; não instala Bambu Studio nem exige serviço online. Parâmetros do fatiamento são informados manualmente no produto/cálculo. Se Bambu Studio não estiver presente, os arquivos e demais funcionalidades continuam disponíveis. Na transferência entre computadores, revise o caminho do executável.

Abrir arquivos valida o checksum e a localização no armazenamento. Arquivo alterado externamente deve ser importado como nova versão; nunca substitua diretamente a cópia vinculada. O backup inclui todas as fotos e versões, inclusive de produtos arquivados.

## Filamentos e auxiliares

A aba **Estoque → Filamentos** mantém os cadastros da Fase 2 e acrescenta descarte documentado. Saldo desconhecido permanece desconhecido mesmo após consumo/perda; não há pesagem obrigatória. Descarte usa custo de aquisição por grama quando conhecido e referência quando a aquisição por grama é desconhecida, com valoração identificada.

**Auxiliares** cadastra nome, unidade, saldo e referência por unidade. Entrada/ajuste exige justificativa. Consumo e descarte recusam saldo insuficiente e registram movimento com quantidade, antes/depois e custo de referência. Unidade não pode ser alterada com saldo positivo. Lixeira conserva materiais arquivados e permite restaurar.

Valores de materiais auxiliares na calculadora continuam sendo informados para o lote. O consumo físico de auxiliares é registrado nesta aba e não é repetido automaticamente pela calculadora. São registros diferentes: um apropria custo informado, outro controla quantidade; nenhum lança caixa nesta fase.

## Peças físicas e produção para estoque

Em **Peças prontas → Entrada manual / produção para estoque**:

- Selecione produto/variante e registre origem/justificativa, quantidade e condição reais.
- Entrada manual usa custo total existente informado pelo proprietário; não fabrica novamente nem lança compra/venda. Serve para cadastro inicial e ajustes positivos documentados.
- Produção para estoque seleciona um cálculo já **confirmado** da Fase 2. A entrada deve corresponder à quantidade confirmada e copia o custo existente. O mesmo cálculo só pode gerar uma entrada; filamento e horas não são baixados novamente.
- Valoração da produção usa aquisição + máquina + auxiliares do snapshot confirmado quando conhecida; caso contrário usa referência, identificada no recibo de estoque interno. Valores gratuitos zero são preservados.
- Custo total em centavos é distribuído entre peças: quociente inteiro e centavos restantes nas primeiras peças. A soma corresponde exatamente ao custo original, sem dinheiro criado/perdido por arredondamento.

Cada peça física tem ID interno, origem, condição, estado e custo preservado. Não são etiquetas nem QR Codes. Limite operacional de 10.000 peças por entrada; entradas maiores devem ser divididas em registros documentados, sem reutilizar o mesmo cálculo confirmado.

Destinos de entrada: **Aguardando verificação**, **Uso pessoal** ou **Disponível com verificação prévia registrada**. Para entrada disponível, o proprietário deve confirmar que cada peça foi verificada e informar responsável/condição. A opção padrão é indisponível, aguardando verificação.

Peças pessoais podem ficar disponíveis futuramente apenas após nova verificação manual registrada com responsável, condição e resultado. Rejeição mantém indisponibilidade. Peças reservadas, baixadas ou descartadas não podem ser reintroduzidas pela verificação.

Esta é a verificação preliminar da Fase 3, **não a inspeção formal com três fotos da Fase 5**. Não há declaração de certificação ISO. OPs, fila, tentativas, controle de qualidade completo e revalidações serão integrados na fase aprovada correspondente.

## Reservas e baixas

O resumo distingue físico, reservado, disponível, pessoal, aguardando verificação e descartado. Físico = disponíveis + reservadas + pessoais + aguardando verificação. Descartadas e baixadas não estão no físico.

Reserve apenas peças disponíveis, priorizando as mais antigas pelo ID. Informe uma referência da reserva; a Fase 3 ainda **não cria pedidos de venda**. Reserva reduz disponível e aumenta reservado, sem reduzir físico e sem novo custo.

Liberar devolve disponibilidade sem entrada física duplicada. **Baixar peças reservadas** registra saída física justificada com os custos já atribuídos. Reserva liberada/baixada não pode ser processada outra vez. A baixa não registra venda, entrega comercial, receita, recebimento ou pagamento; esses fluxos dependem das Fases 4 e 6.

## Perdas e auditoria

Selecione peças físicas para descartar; informe motivo, data e observações. Custo é a soma do custo existente das peças, sem recriar fabricação. Reservas precisam ser liberadas antes. Peça descartada não pode ser descartada novamente nem voltar pela verificação.

Perdas de filamento/auxiliares também registram quantidade, custo, data, motivo e observações; operações repetidas com o mesmo identificador são recusadas. Ajustes manuais exigem justificativa. Registros de perda não são uma segunda despesa de caixa.

Movimentos e auditoria são gravados na mesma transação da alteração. Saldo insuficiente ou falha de gravação reverte a operação completa. Cada diálogo de entrada/consumo/descarte/reserva mantém identificador próprio contra repetição da mesma confirmação. Registros manuais distintos devem corresponder a fatos físicos distintos; o programa não identifica uma peça externa sem cadastro.

O diário unificado começa no esquema 3 com os saldos de filamento preservados como abertura. O histórico anterior da Fase 2 permanece na auditoria e nos cálculos/consumos originais; não é relançado como nova saída. Consumos confirmados da Fase 2 passam a aparecer também no diário a partir do esquema 3.

## Backup, atualização e limitações

Migração 2 → 3 é aditiva, transacional e cria snapshot SQLite prévio. Preserva contas, senhas, preferências, cálculos, saldos e horas. Backups dos esquemas 1 e 2 continuam restauráveis e são migrados na próxima abertura.

Backup completo verifica banco, manifesto e hashes dos arquivos vinculados aos produtos. Foto/projeto ausente ou alterado externamente impede chamar o backup atual de íntegro. Ainda é possível restaurar um **ZIP anterior íntegro**: o programa preserva snapshot consistente do banco e todos os arquivos existentes na pasta rollback, registrando que o estado anterior estava incompleto. Não inventa os arquivos que já estavam ausentes. O ZIP selecionado só é restaurado após verificação completa.

Persistem os limites documentados das fases anteriores: dados não criptografados, backup diário apenas com programa aberto, recuperação manual de rollback em interrupção de energia e instalador Windows não homologado. Testes de Bambu Studio verificam argumentos e ausência de shell; a abertura real do software externo deve ser validada no Windows com Bambu Studio instalado.

A integração comercial da Fase 4 está documentada em `fase4.md`. A Fase 5 está documentada em `fase5.md`; Fases 6–8 continuam pendentes e exigem aprovação expressa.
