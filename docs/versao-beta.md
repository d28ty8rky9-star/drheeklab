# Dr. Heek Lab — versão 2.9.10 Beta

Identificação da nova etapa beta definida pelo proprietário. Versão técnica 2.9.10, texto visível 2.9.10 Beta. Título/menu/Sobre/ajuda CLI, metadados Windows e identificação do instalador atualizados. FileVersion numérica2.9.10, ProductVersion2.9.10 Beta e flag prerelease Windows. pyproject mantém a versão numérica compatível com a ferramenta de compilação.

Futuro instalador: DrHeekLab-2.9.10-Beta-Setup.exe; futuro artefato: DrHeekLab-Windows-2.9.10-Beta. Retirado Fase8 do nome da nova entrega. AppId do instalador, nome dos atalhos, Program Files/DrHeekLab e C:\DrHeekLab preservados para atualização da instalação existente. Schema10 e dados/PDFs históricos intactos.

Inclui todos os ajustes anteriores de produção, vendas, estoque, Financeiro, Clientes, Início e limpeza. Teste cruza versão da aplicação/configuração/instalador/workflow/metadados e interface. Captura real com dados temporários: capturas-beta/inicio-beta.png.

Esta alteração define a identificação beta no código; não cria release pública, ZIP ou instalador. Empacotamento somente mediante pedido explícito. A nova instalação beta e avaliação prática do proprietário aguardam uma entrega solicitada.

Validação local: 311 testes aprovados, zero falhas/erros/pulos.

Suíte Windows aprovada no run38833805978 sobre2ba57d62df769965c551593a0fc1e24b9e5e7d41. Etapa de pacote ignorada; instalador Beta ainda não compilado.

Primeira tentativa de pacote run38834443314 compilou, mas a reinstalação foi bloqueada por comparação de versão antiga (2.9.1) fixa no Inno. Corrigido para derivar os componentes numéricos de AppVersion na verificação, preservando a proteção contra downgrade. Nova geração e testes de instalação obrigatórios antes da entrega.
