# Modernização visual — Dr. Heek Lab 2.9.0

Esta revisão aplica uma identidade compartilhada às oito áreas. As capturas usam dados fictícios criados pelas APIs reais em um diretório temporário de TESTES; nenhum dado do usuário foi utilizado ou alterado.

| Área | Apresentação |
|---|---|
| Início | Indicadores de vendas/recebimentos do mês, contas a receber totais, produção por estado, gráfico comparativo e atalhos existentes |
| Vendas | Resumo financeiro, filtros locais por tabela, clientes/orçamentos/pedidos/recebíveis e precificação preservados |
| Produção | Quatro estados com cores, fila filtrável, progresso de peças aprovadas contra planejadas, inspeção e histórico |
| Produtos | Galeria, categoria e preço, botão Nova peça, alternância para tabela com seleção sincronizada, variantes/fotos/STL/3MF |
| Estoque | Carretéis cadastrados, filamento baixo, peças reservadas/disponíveis, tabelas e movimentações |
| Financeiro | Oito indicadores extraídos do relatório existente, gráfico de vendas/recebimentos/despesas no período, filtros e relatórios |
| Impressoras | Cartões com identificação/modelo/estado/horas/custo por hora, seleção da impressora e manutenção na tabela existente |
| Configurações | Seções para segurança, aparência/integrações, precificação, backup/restauração, documentos, auditoria, fornecedores e informações |

## Componentes

`visual.py` centraliza paleta, fontes, espaçamento, temas claro/escuro, cartões, faixas de indicadores, gráficos, estilo dos botões, ícones vetoriais e tabelas. `FormDialog` mantém formulários e validações comuns com espaçamento padronizado. Confirmações existentes usam o tema compartilhado e conservam seus critérios de segurança. `presentation.py` integra os componentes às páginas e utiliza exclusivamente relatórios de domínio e consultas de leitura. Os filtros de texto apenas ocultam linhas; não reordenam nem trocam os identificadores dos registros.

Os gráficos exibem valores reais do período e uma mensagem quando não há movimentações. As barras comparam a magnitude; o rótulo conserva o sinal e o valor monetário exato. Não há estimativa artificial de produtividade. O progresso da produção é a contagem real de peças aprovadas contra planejadas, não uma previsão de tempo.

## Preservação

Nenhuma migração, fórmula financeira, regra de estoque/produção, senha, criptografia, auditoria ou documento histórico foi alterado. Os caminhos de cadastro, edição, arquivamento/restauração, pagamentos, entregas, inspeção, compras, exportações, backup e atualização continuam existentes. Fornecedores são consultados dos registros atuais; continuam editados nas compras/filamentos de origem.

## Capturas

Os arquivos abaixo mostram a aplicação Qt executada, não mockups.

### Início
![Início](capturas-modernizacao/01.png)
### Vendas
![Vendas](capturas-modernizacao/02.png)
### Produção
![Produção](capturas-modernizacao/03.png)
### Produtos
![Produtos](capturas-modernizacao/04.png)
### Estoque
![Estoque](capturas-modernizacao/05.png)
### Financeiro
![Financeiro](capturas-modernizacao/06.png)
### Impressoras
![Impressoras](capturas-modernizacao/07.png)
### Configurações
![Configurações](capturas-modernizacao/08.png)

## Limitações de referência

A segunda imagem de referência não estava disponível nesta tarefa. A paleta e a hierarquia seguem a descrição textual. O logotipo oficial permanece importável; não foi substituído por uma imagem inventada. As peças de demonstração das capturas não possuem fotos importadas; a importação de fotos é coberta pelos testes existentes. A avaliação no computador do proprietário continua necessária para conferir DPI, monitor e uso prático.
