# PROMPT MESTRE — DR. HEEK LAB 2.0
## Desenvolvimento completo de aplicativo desktop Windows para gestão de impressão 3D

Você é um engenheiro de software sênior especializado em Python, PySide6, SQLite, arquitetura de aplicativos desktop Windows, gestão financeira, estoque, produção e controle de qualidade.

Sua missão é **desenvolver do zero o Dr. Heek Lab 2.0**, um aplicativo profissional, moderno, completo e simples de utilizar, destinado à administração de um pequeno negócio de impressão 3D.

O projeto foi planejado previamente. As regras e funcionalidades abaixo já foram aprovadas pelo proprietário e devem ser respeitadas.

**IMPORTANTE:** Este é um projeto de desenvolvimento real. Não entregue apenas protótipos, telas ilustrativas, pseudocódigo ou funcionalidades simuladas. Implemente funcionalidades operacionais, persistência de dados, cálculos verificáveis, testes e executáveis Windows.

---

# 1. DIRETRIZES GERAIS

## 1.1. Tecnologia obrigatória

- Linguagem: Python.
- Interface gráfica: PySide6.
- Banco de dados: SQLite.
- Plataforma: Windows.
- Funcionamento: totalmente offline.
- Distribuição: aplicativo empacotado, com instalador `.exe`.
- Não exigir Python instalado no computador do usuário.
- Utilizar arquitetura modular, com separação entre interface, regras de negócio, persistência e geração de documentos.
- Utilizar migrações versionadas do esquema do banco.
- Utilizar valores monetários com `Decimal` ou representação inteira em centavos, evitando erros de ponto flutuante.

Não utilizar navegador como interface principal, nem depender de servidor remoto.

## 1.2. Identidade visual

Nome: **Dr. Heek Lab 2.0**.

Utilizar a identidade visual oficial da marca, com predominância de preto, roxo e azul, em estilo tecnológico/geek.

O logotipo oficial será fornecido pelo proprietário. **Não inventar nem substituir a marca por um logotipo genérico.** Caso o arquivo ainda não esteja disponível, utilizar um espaço reservado claramente identificado até receber o original.

Implementar:

- Tema claro e tema escuro.
- Alternância manual entre temas.
- Persistência da preferência escolhida.
- Menu lateral recolhível, exibindo apenas ícones quando fechado.
- Interface moderna, organizada e adaptável a diferentes resoluções.
- Formulários simples, com validação de dados.
- Formatação monetária brasileira: `R$ 1.234,56`.
- Datas no formato brasileiro: `DD/MM/AAAA`.

## 1.3. Estrutura de armazenamento

Utilizar a pasta principal:

`C:\DrHeekLab`

Organizar os arquivos em subpastas:

- Banco de Dados
- Projetos STL e 3MF
- Fotos dos Produtos
- Orçamentos
- Pedidos e Comprovantes
- Catálogos
- Relatórios
- Backups

Separar arquivos do aplicativo dos dados permanentes. O instalador nunca deverá apagar essas pastas durante atualizações.

Criar na interface um botão para abrir a pasta de armazenamento.

## 1.4. Ambientes independentes

Manter dois ambientes:

**Testes:** dados fictícios, destinados à validação das funcionalidades.

**Produção:** dados reais do negócio.

Os bancos de dados devem ser fisicamente separados, com identificação visual clara do ambiente ativo.

Não permitir que testes alterem dados reais.

## 1.5. Segurança

Implementar:

- Login com senha na abertura.
- Alteração de senha nas configurações.
- Armazenamento seguro do hash da senha, nunca em texto puro.
- Confirmação antes de operações destrutivas.
- Registro de auditoria de alterações importantes.
- Exclusão lógica e lixeira recuperável onde aplicável.
- Salvamento automático de rascunhos.
- Recuperação de rascunhos após fechamento inesperado.
- Tratamento de erros sem perda de dados.

---

# 2. ESTRUTURA PRINCIPAL DA INTERFACE

O programa deverá ter exatamente oito áreas principais de navegação:

1. **Início**
2. **Vendas**
3. **Produção**
4. **Produtos**
5. **Estoque**
6. **Financeiro**
7. **Impressoras**
8. **Configurações**

Submenus podem ser criados dentro dessas áreas.

## 2.1. Painel inicial

Exibir:

- Total de vendas do mês.
- Total efetivamente recebido.
- Valores ainda a receber.
- Pedidos em andamento.
- Impressões em produção.
- Produtos aguardando entrega.
- Alertas de pagamentos atrasados.
- Alertas de filamento baixo.
- Manutenções pendentes.
- Orçamentos próximos do vencimento.

Criar três atalhos principais:

- Nova venda.
- Nova produção.
- Calcular preço.

## 2.2. Busca global

Permitir localizar clientes, pedidos, orçamentos, produtos, arquivos de projetos, filamentos e registros de produção.

## 2.3. Central de notificações

Criar ícone de sino com notificações internas e possibilidade de marcar como lidas.

---

# 3. FASE 1 — ESTRUTURA INICIAL DO APLICATIVO

Implementar primeiro a base do software:

- Organização modular do projeto.
- Janela principal PySide6.
- Oito áreas de navegação.
- Temas claro e escuro.
- Menu lateral recolhível.
- Tela de login.
- Alteração de senha.
- Banco SQLite e esquema inicial.
- Separação de ambientes.
- Configurações persistentes.
- Estrutura de pastas.
- Sistema centralizado de erros.
- Logs técnicos.
- Controle de versão do aplicativo.
- Tela Sobre o programa.
- Infraestrutura para backups e auditoria.

**Entrega da fase:** aplicativo executável que abre, autentica o usuário, navega pelas oito áreas e mantém suas configurações após reiniciar.

As áreas ainda não implementadas devem ser identificadas como pendentes, nunca apresentadas como prontas.

---

# 4. FASE 2 — IMPRESSORAS, FILAMENTOS E PRECIFICAÇÃO

## 4.1. Cadastro de impressoras

Cadastrar múltiplas impressoras, com:

- Fabricante.
- Modelo.
- Número ou identificação.
- Data de aquisição.
- Valor de aquisição.
- Horas acumuladas.
- Custo operacional por hora.
- Histórico de manutenção.
- Situação operacional.

Cadastrar inicialmente uma **Bambu Lab A1 Mini**.

Parâmetros iniciais aprovados:

| Componente | Valor |
|---|---:|
| Recuperação do investimento | R$ 0,75/h |
| Energia elétrica | R$ 0,10/h |
| Manutenção e desgaste | R$ 0,25/h |
| **Total** | **R$ 1,10/h** |

Valor de referência do investimento: **R$ 2.400,00**.

Todos esses parâmetros devem ser editáveis, inclusive individualmente por impressora.

Não substituir automaticamente esses valores por estimativas externas.

## 4.2. Cadastro de filamentos

Permitir cadastrar:

- Marca.
- Material: PLA, PLA Silk, PETG, TPU, ABS e outros.
- Cor.
- Nome comercial.
- Preço de compra.
- Peso inicial.
- Data de compra.
- Fornecedor.
- Custo de referência por grama.
- Quantidade estimada restante, quando conhecida.
- Estado: novo, aberto ou finalizado.

Distinguir obrigatoriamente:

**Filamento com peso conhecido:** controlar consumo e saldo estimado automaticamente.

**Filamento aberto com peso desconhecido:** permitir uso sem exigir pesagem e sem inventar saldo.

Filamentos recebidos gratuitamente podem ter custo real de aquisição igual a zero, mas manter um custo de referência para precificação.

Criar alerta de saldo baixo, inicialmente em **100 gramas**, configurável.

Sugerir o último carretel utilizado, permitindo alteração.

## 4.3. Calculadora de precificação

A calculadora deverá permitir:

- Selecionar impressora.
- Informar tempo estimado de impressão.
- Adicionar um ou vários filamentos.
- Informar a quantidade em gramas de cada filamento.
- Acrescentar materiais auxiliares, quando aplicável.
- Informar quantidade de peças produzidas.
- Calcular custo total e custo unitário.

**REGRA FUNDAMENTAL: O ACRÉSCIMO PADRÃO É DE 200% SOBRE O CUSTO.**

Isso significa:

`Preço sugerido = Custo total × 3`

Exemplo:

- Custo: R$ 30,00.
- Acréscimo de 200%: R$ 60,00.
- Preço sugerido: R$ 90,00.

O percentual deve ser configurável, mas iniciar em 200%.

## 4.4. Preço final e desconto automático

Permitir informar diretamente o preço final da venda.

O sistema deverá calcular automaticamente a diferença entre o preço sugerido e o preço final.

Exemplo:

- Custo: R$ 30,00.
- Preço sugerido: R$ 90,00.
- Preço efetivamente vendido: R$ 35,00.
- Redução comercial: R$ 55,00.
- Percentual de redução sobre o preço sugerido: 61,11%.
- Resultado comercial antes de outras despesas: R$ 5,00.

**Não aplicar o desconto duas vezes.**

O preço final informado é o valor efetivo da venda, não um valor ao qual se deve aplicar novamente a redução calculada.

Se o preço final for superior ao sugerido, indicar acréscimo em vez de desconto.

## 4.5. Custos planejados e reais

Registrar custo previsto antes da impressão.

Após a produção, registrar tempo e consumo confirmados, comparando:

- Custo previsto.
- Custo real.
- Diferença em reais.
- Diferença percentual.

Preservar o histórico dos valores utilizados em cada operação.

**Não incluir cobrança por horas de modelagem ou criação de arquivos 3D nesta versão.**

**Entrega da fase:** cadastro funcional de impressoras e filamentos, calculadora completa e testes matemáticos automatizados.

---

# 5. FASE 3 — PRODUTOS, ESTOQUE E ARQUIVOS 3D

## 5.1. Cadastro de produtos

Cada modelo deverá receber código único:

`MOD-0001`

Informações:

- Nome.
- Descrição.
- Categoria: decorativo, funcional ou misto.
- Fotos reais.
- Foto principal.
- Arquivo STL ou 3MF.
- Histórico de versões dos arquivos.
- Versão preferencial.
- Impressora recomendada.
- Filamento recomendado.
- Configurações recomendadas.
- Tempo estimado.
- Custo previsto.
- Preço sugerido.
- Observações de qualidade.

Permitir diferentes variantes de tamanho, cor e material, com custos próprios.

Criar galeria visual pesquisável.

Os arquivos devem ser armazenados nas pastas do sistema e referenciados no banco.

Não assumir que o programa consegue analisar automaticamente todos os dados internos de arquivos STL/3MF.

Permitir abrir o projeto no Bambu Studio, quando instalado, e registrar manualmente os dados obtidos no fatiamento.

## 5.2. Estoque de materiais

Controlar:

- Filamentos.
- Materiais auxiliares.
- Peças prontas.
- Produtos reservados.
- Produtos disponíveis.
- Produtos descartados.

Manter movimentos de estoque auditáveis.

Exigir justificativa em ajustes manuais.

## 5.3. Estoque de produtos acabados

Distinguir:

- Quantidade física.
- Quantidade reservada.
- Quantidade disponível.

Reservar peças para pedidos sem duplicar baixas.

Permitir produção para estoque sem pedido de cliente.

Peças produzidas para uso pessoal poderão ser vendidas futuramente, após nova inspeção e registro adequado da condição.

## 5.4. Perdas e descarte

Registrar:

- Motivo.
- Quantidade.
- Custo.
- Data.
- Observações.

Impedir que o mesmo prejuízo seja lançado duas vezes.

**Entrega da fase:** galeria de produtos, gestão de arquivos, estoque de materiais e peças acabadas, movimentações auditáveis.

---

# 6. FASE 4 — CLIENTES, ORÇAMENTOS E VENDAS

## 6.1. Clientes

Cadastro simples:

- Nome obrigatório.
- Telefone opcional.
- E-mail opcional.
- Observações.
- Histórico de pedidos e pagamentos.

## 6.2. Orçamentos

Criar orçamentos com:

- Cliente.
- Produtos.
- Quantidades.
- Preços.
- Frete.
- Total.
- Validade.
- Observações.

Validade padrão: sete dias, podendo ser alterada ou deixada em branco.

Estados:

- Pendente.
- Aprovado.
- Rejeitado.
- Vencido.

Gerar PDF com identidade visual oficial.

**Não mostrar custos internos nem uma linha explícita de desconto no documento do cliente.**

Converter orçamento aprovado em pedido sem redigitar os dados.

Orçamento ainda não aprovado não deve movimentar caixa, reconhecer receita ou consumir estoque.

## 6.3. Pedidos

Identificação:

`PED-AAAA-NNNN`

Permitir:

- Múltiplos produtos por pedido.
- Produto já cadastrado.
- Produto personalizado.
- Foto de referência.
- Descrição personalizada.
- Anexos STL/3MF.
- Quantidades.
- Preço final.
- Frete.
- Prazo opcional de entrega.
- Acompanhamento da produção.
- Histórico de pagamentos.

Não implementar edição/versionamento de pedido após aprovação nesta versão. Alterações excepcionais deverão seguir fluxo controlado de cancelamento e novo registro, preservando o histórico.

## 6.4. Pagamentos

Permitir:

- Pagamento integral.
- Entrada opcional.
- Pagamentos parciais.
- Parcelamentos.
- Recebimentos em datas diferentes.
- Valores previstos.
- Valores efetivamente recebidos.
- Saldo pendente.

Formas de pagamento:

- Pix.
- Dinheiro.
- Débito.
- Crédito.
- Transferência.
- Outros.

Registrar taxas de cartão e valor líquido recebido.

Em pedidos com vários itens, distribuir pagamentos segundo a regra de alocação aprovada, priorizando os itens mais antigos, mantendo rastreabilidade.

## 6.5. Cancelamentos

Registrar motivo e consequências financeiras.

Permitir:

- Reembolso.
- Crédito para compra futura.
- Retenção justificada de valores.

Se a impressão já começou, os custos incorridos devem permanecer registrados.

Se uma peça for concluída e aprovada após o cancelamento, permitir entrada em estoque, sem duplicar seu custo.

## 6.6. Entregas

Controlar:

- Aguardando envio.
- Enviado.
- Entregue.

Registrar:

- Retirada presencial ou envio.
- Transportadora, quando aplicável.
- Código de rastreio.
- Frete pago pelo cliente ou gratuito.
- Data de envio.
- Data de entrega.
- Comprovante opcional.

## 6.7. Comprovante comercial

Gerar PDF com:

- Logotipo oficial.
- Cliente.
- Número do pedido.
- Data.
- Itens e quantidades.
- Preços finais.
- Frete.
- Total.
- Histórico de pagamentos com datas e valores.
- Total recebido.
- Saldo restante.
- Indicação QUITADO quando aplicável.

O comprovante não é nota fiscal.

A cada novo pagamento, emitir uma nova versão do PDF sem sobrescrever documentos anteriores.

**Entrega da fase:** fluxo operacional de cliente → orçamento → pedido → pagamentos → entrega.

---

# 7. FASE 5 — PRODUÇÃO E CONTROLE DE QUALIDADE

## 7.1. Ordens de produção

Código:

`OP-AAAA-NNNN`

Cada OP deverá conter:

- Pedido vinculado ou indicação de produção para estoque.
- Produto.
- Quantidade.
- Impressora.
- Arquivo e versão.
- Filamentos e quantidades.
- Parâmetros de impressão.
- Tempo previsto.
- Custo previsto.
- Responsável.
- Histórico de execução.

## 7.2. Fila de produção

Prioridades:

- Alta.
- Normal.
- Baixa.

Permitir reorganização manual da fila.

Preservar datas originais de criação.

## 7.3. Etapas da produção

Utilizar quatro estados principais:

1. Aguardando produção.
2. Em impressão.
3. Aguardando inspeção.
4. Concluída.

A conclusão depende de aprovação na inspeção.

## 7.4. Tempo de impressão

Permitir cronômetro, mas exigir confirmação do tempo real antes de consolidar os custos.

Atualizar horas acumuladas da impressora a partir do tempo confirmado.

Permitir correção manual de horas com justificativa e auditoria.

**Não criar módulo específico de registro de pausas e motivos de pausas.**

## 7.5. Impressões em lote

Permitir lotes com:

- Várias peças iguais.
- Peças diferentes na mesma mesa.
- Filamentos diferentes por modelo.

Para lotes mistos, distribuir inicialmente o custo compartilhado de máquina proporcionalmente ao consumo estimado de material, permitindo ajuste manual documentado.

## 7.6. Falhas e reimpressões

Registrar:

- Quantidade planejada.
- Quantidade aprovada.
- Quantidade rejeitada.
- Custo do material perdido.
- Tempo consumido.
- Motivo da falha.
- Tentativas adicionais.

Quando uma impressão falhar parcialmente, permitir estimar o custo consumido por percentual de progresso, ajustável pelo usuário.

Exemplo: produzir cinco peças, perder uma e aprovar quatro. O sistema deverá demonstrar o custo total do lote e o custo efetivo das quatro peças boas, sem duplicar a perda.

Criar função **Reimpressão rápida**, copiando os parâmetros de uma OP anterior para uma nova OP, com custos recalculados pelas referências atuais.

## 7.7. Controle de qualidade

Criar inspeção obrigatória por peça física.

Exigir pelo menos três fotografias:

1. Frente.
2. Verso ou lateral.
3. Detalhe crítico.

Criar listas de verificação conforme a categoria do produto.

Resultados:

- Aprovado.
- Aprovado com observações menores.
- Rejeitado.

Itens marcados como não aplicáveis exigem justificativa.

Peças rejeitadas não podem ser liberadas para entrega ou estoque disponível.

Registrar responsável, data, fotos e observações.

Adotar processos internos inspirados na ISO 9001, sem declarar certificação.

Organizar procedimentos e registros internos em sequência, com identificadores PO-001 a PO-012 e FR-001, documentando o conteúdo de cada um.

Mudanças em etapas anteriores devem exigir revalidação das etapas posteriores afetadas.

Não criar módulo específico para custos de pequenos retrabalhos nesta versão.

## 7.8. Histórico de problemas

Permitir registrar observações úteis para futuras impressões, por exemplo:

- Defeitos de acabamento superficial.
- Suportes insuficientes em extremidades pequenas.
- Problemas de aderência.
- Falhas em detalhes delicados.

Essas observações devem ficar associadas ao produto e à produção.

**Entrega da fase:** fila de produção, OPs, lotes, falhas, reimpressões, horas de máquina e inspeção individual com fotos.

---

# 8. FASE 6 — FINANCEIRO, RECEBIMENTOS E RELATÓRIOS

## 8.1. Conceitos financeiros obrigatórios

Distinguir claramente:

**Custo de produção:** custo dos materiais e recursos utilizados para fabricar peças.

**Resultado comercial:** receita de vendas menos os custos atribuíveis aos produtos vendidos e outras despesas pertinentes.

**Fluxo de caixa:** dinheiro efetivamente recebido menos dinheiro efetivamente pago.

**Contas a receber:** valores de vendas ainda não recebidos.

**Contas a pagar:** compromissos ainda não quitados.

Não confundir faturamento com recebimento.

## 8.2. Evitar dupla contabilização

Regras fundamentais:

- Comprar filamento gera saída de caixa e entrada de estoque.
- Consumir filamento gera custo de produção e redução de estoque.
- Não registrar a mesma compra novamente como saída de caixa quando o filamento for consumido.
- Produzir para estoque não significa vender.
- Vender uma peça pronta reconhece o custo atribuído à peça, sem recriar custo de fabricação.
- Registrar falha sem duplicar despesas.
- Pagamento de manutenção e apropriação de reserva de manutenção devem ser identificados separadamente para não distorcer os relatórios.
- Aportes do proprietário não são receitas de vendas.
- Retiradas do proprietário não são despesas operacionais.

## 8.3. Controle de recebimentos

Registrar:

- Valor previsto.
- Data prevista.
- Valor recebido.
- Data efetiva.
- Meio de pagamento.
- Taxas.
- Saldo.
- Situação: pendente, parcial, quitado ou atrasado.

## 8.4. Contas a pagar

Permitir cadastrar:

- Descrição.
- Categoria.
- Fornecedor.
- Valor.
- Vencimento.
- Parcelas.
- Pagamento efetivo.
- Comprovante.
- Situação.

## 8.5. Despesas

Categorias editáveis, como:

- Filamentos.
- Materiais auxiliares.
- Energia.
- Manutenção.
- Equipamentos.
- Embalagens.
- Fretes.
- Taxas de pagamento.
- Outras despesas.

Os relatórios deverão distinguir despesas efetivamente pagas de custos de produção apropriados.

## 8.6. Indicadores

Exibir por período:

- Total vendido.
- Total recebido.
- Total a receber.
- Despesas pagas.
- Custo dos produtos vendidos.
- Resultado comercial.
- Fluxo líquido de caixa.
- Quantidade de peças vendidas.
- Ticket médio.
- Resultados por produto.
- Resultados por impressora.
- Descontos comerciais concedidos.
- Perdas de produção.

## 8.7. Relatórios

Permitir filtros por datas, cliente, produto, impressora e situação financeira.

Exportar dados em Excel e CSV.

Preservar histórico de custos e preços das vendas antigas mesmo quando as configurações atuais forem alteradas.

**Entrega da fase:** financeiro operacional completo, relatórios verificáveis e reconciliação entre vendas, recebimentos, estoque e produção.

---

# 9. FASE 7 — DOCUMENTOS, CATÁLOGOS, BACKUPS E NOTIFICAÇÕES

## 9.1. Documentos PDF

Gerar:

- Orçamentos.
- Comprovantes comerciais.
- Relatórios financeiros.
- Relatórios de produção.
- Catálogos de produtos.

Aplicar logotipo e identidade visual oficial.

Os documentos emitidos deverão preservar seu conteúdo original, mesmo após alterações posteriores nos cadastros.

## 9.2. Catálogo de produtos

Criar catálogo PDF com:

- Logo.
- Fotos.
- Nome.
- Descrição resumida.
- Preço de venda.
- Produtos selecionados pelo usuário.

Preparar o arquivo para compartilhamento por WhatsApp, sem exigir integração com a plataforma.

## 9.3. Backup

Implementar:

- Backup local automático diário.
- Backup manual.
- Backup completo para HD externo ou pendrive.
- Inclusão do banco de dados e dos arquivos vinculados.
- Verificação de integridade.
- Restauração com confirmação.
- Possibilidade de transferência para outro computador.

Utilizar método consistente de backup SQLite, sem simplesmente copiar um banco ativo de maneira insegura.

## 9.4. Proteção durante atualizações

Antes de atualizar:

1. Criar backup verificável.
2. Conferir compatibilidade de esquema.
3. Executar migrações necessárias de forma controlada.
4. Preservar o banco original caso ocorra falha.
5. Registrar resultado da atualização.

Nunca apagar automaticamente os dados do usuário.

## 9.5. Notificações

Alertar sobre:

- Filamento baixo.
- Pagamentos vencidos.
- Pagamentos próximos do vencimento.
- Entregas pendentes.
- Manutenções necessárias.
- Orçamentos vencidos ou próximos do vencimento.

## 9.6. Auditoria e lixeira

Registrar alterações importantes com:

- Data e hora.
- Operação.
- Registro afetado.
- Valor anterior.
- Valor novo.
- Justificativa, quando exigida.

Implementar recuperação de registros excluídos logicamente quando tecnicamente aplicável, respeitando vínculos históricos.

**Entrega da fase:** PDFs, catálogo, backups completos, notificações e mecanismos de recuperação.

---

# 10. FASE 8 — TESTES, FINALIZAÇÃO E INSTALADOR

## 10.1. Testes obrigatórios

Criar testes automatizados para:

- Cálculo de custo por grama.
- Uso de vários filamentos.
- Custo horário por impressora.
- Acréscimo de 200%.
- Preço final informado manualmente.
- Cálculo automático de desconto.
- Pagamentos parciais.
- Parcelamentos.
- Taxas de cartão.
- Contas a receber.
- Consumo de estoque.
- Reserva e liberação de produtos.
- Produção para estoque.
- Falhas e perdas.
- Rateio de custos em lotes.
- Cancelamentos e reembolsos.
- Custo previsto versus real.
- Integridade financeira.
- Persistência dos dados após reiniciar.
- Backup e restauração.
- Migrações de banco.
- Atualização sem perda de registros.

Testes críticos devem impedir a liberação de uma versão defeituosa.

## 10.2. Controle de versões

Utilizar versões como:

- 2.0.0 — versão inicial.
- 2.1.0 — novas funcionalidades.
- 2.1.1 — correções.

Criar tela Sobre o programa com número da versão e histórico de alterações.

## 10.3. Instalador Windows

Gerar instalador `.exe` que:

- Instale o programa.
- Crie atalho na área de trabalho.
- Utilize o ícone oficial.
- Não exija instalação manual de Python.
- Preserve dados em `C:\DrHeekLab`.
- Permita reinstalação e atualização.
- Não apague arquivos pessoais do projeto.

Não considerar um instalador válido apenas por ter sido gerado: testar a abertura, a persistência de dados e as principais operações no Windows.

## 10.4. Documentação

Entregar:

- Instruções de instalação.
- Manual básico de utilização.
- Descrição das pastas.
- Instruções de backup e restauração.
- Procedimento de atualização.
- Registro de versões.
- Lista de funcionalidades concluídas.
- Limitações conhecidas.

**Entrega da fase:** sistema integrado, validado e pronto para utilização real no Windows.

---

# 11. REGRAS DE IMPLEMENTAÇÃO

## 11.1. Desenvolvimento incremental

Apesar de este prompt conter as oito fases, o desenvolvimento deverá ser organizado e verificável.

**Não tentar substituir todas as entregas por um protótipo superficial.**

Para cada fase:

1. Implementar as funcionalidades previstas.
2. Criar ou atualizar o banco.
3. Integrar com os módulos existentes.
4. Executar os testes correspondentes.
5. Gerar uma versão executável de testes.
6. Informar claramente o que foi concluído.
7. Informar eventuais limitações.
8. Aguardar aprovação do proprietário antes de avançar para a próxima fase.

O objetivo é construir um único sistema integrado, não oito programas independentes.

## 11.2. Persistência e integridade

- Utilizar transações para operações financeiras e de estoque.
- Aplicar integridade referencial.
- Evitar duplicidade de lançamentos.
- Usar identificadores únicos.
- Não apagar histórico financeiro consolidado.
- Separar rascunhos de registros confirmados.
- Registrar alterações críticas.
- Preservar preços e custos históricos.
- Garantir consistência entre estoque, produção, vendas e financeiro.

## 11.3. Experiência do usuário

O proprietário não deve precisar conhecer programação para utilizar o aplicativo.

Evitar telas excessivamente complexas.

Utilizar botões claros, mensagens em português e fluxos intuitivos.

Não exigir preenchimento de campos desnecessários.

## 11.4. Funcionalidades expressamente excluídas

Não implementar nesta versão:

- Módulo específico de cobrança de modelagem 3D.
- Módulo detalhado de pausas de impressão.
- Versionamento de pedidos já aprovados.
- Controle financeiro específico de pequenos retrabalhos.
- Etiquetas ou sistema de QR Code.
- Integração automática obrigatória com impressoras.
- Dependência de serviços online.
- Assistente de migração de dados do programa antigo.

O cadastro inicial dos poucos dados antigos será feito manualmente.

---

# 12. INSTRUÇÕES FINAIS AO CODEX

Considere este documento como a **especificação mestre do Dr. Heek Lab 2.0**.

Não altere regras de negócio já definidas sem solicitar autorização.

Priorize:

1. Integridade dos dados.
2. Correção dos cálculos financeiros.
3. Funcionamento real das funcionalidades.
4. Facilidade de utilização.
5. Qualidade visual.
6. Desempenho e manutenção do código.

Não apresente como concluído aquilo que ainda não funciona.

**Comece pela Fase 1**, preparando a estrutura real do projeto, a arquitetura, o banco de dados, a interface inicial e os testes correspondentes.

As oito fases deverão permanecer no planejamento do projeto, mas **não avance para a fase seguinte sem minha aprovação expressa**.

Ao concluir a Fase 1, apresente os arquivos gerados, as instruções para executar e testar o programa, os resultados dos testes e os pontos que precisam da minha validação.

**O objetivo final é ter o Dr. Heek Lab 2.0 funcionando como um programa Windows de verdade, com todas as oito fases integradas, e não apenas uma demonstração visual.**