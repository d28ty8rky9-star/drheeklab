# Dr. Heek Lab — versão 2.9.1

Aplicativo **desktop offline**, Python + PySide6 + SQLite, para Windows. As sete áreas estão implementadas; peças/modelos e ordens ficam juntos em Produção. O instalador e os fluxos de instalação/reinstalação, backup e preservação de dados passaram pela validação automatizada Windows; a avaliação prática no computador do proprietário permanece pendente.

Disponível: login, ambientes separados, temas, menu recolhível, configurações, rascunhos, auditoria, backups, cadastro de impressoras/manutenções e filamentos, precificação com vários materiais, comparação previsto/confirmado e atualização única de consumo e tempo.

O novo fluxo salva os dados técnicos na ficha de Produção, cria OPs simples e libera Estoque/custo financeiro na conclusão com fotos e observações, sem pagamento automático. Veja [como usar e limites](docs/fluxo-producao-estoque.md). Código atualizado; o pacote anterior não contém esta alteração.

Também disponível: valor demonstrativo da peça em Produção, entrada de peça comprada diretamente no Estoque e tempo informado em horas. [Como usar](docs/valor-producao-estoque-horas.md).

A ficha de Produção também oferece [extras detalhados e cálculo automático](docs/extras-producao.md), como argolas com quantidade e custo unitário.

## Executar a partir do código

Windows (Python 3.12 para desenvolvimento):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.lock
.venv\Scripts\python -m pip install --no-build-isolation --no-deps -e .
.venv\Scripts\python -m drheeklab
```

Linux, neste ambiente:

```bash
cd /workspace/drheeklab
python -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/python -m drheeklab --data-dir /workspace/drheeklab-data
```

Escolha **TESTES** ou **PRODUÇÃO** na abertura. No primeiro acesso de cada ambiente, crie uma senha de pelo menos oito caracteres. Não existe senha padrão. O último ambiente é lembrado, mas a seleção continua explícita em cada abertura.

Abra diretamente com `--environment test` ou `--environment production`. O padrão Windows é `C:\DrHeekLab`; `--data-dir` ou `DRHEEKLAB_DATA_DIR` permitem pasta alternativa para desenvolvimento. Testes automatizados usam apenas diretórios temporários.

## Usar a Fase 2

1. Em **Impressoras**, revise a Bambu Lab A1 Mini: investimento R$ 2.400, custo horário R$ 0,75 + R$ 0,10 + R$ 0,25 = R$ 1,10. Edite parâmetros ou cadastre outras máquinas. Datas não conhecidas ficam vazias.
2. Em **Estoque → Filamentos**, cadastre carretéis. O custo real de compra é separado da referência por grama para precificação. Marque saldo desconhecido nos carretéis abertos sem pesagem.
3. Em **Vendas → Precificação**, selecione máquina, tempo em minutos, carretéis/gramas, materiais auxiliares, quantidade e preço final total opcional.
4. Clique em **Calcular**. Acréscimo padrão 200% significa custo × 3. Custo R$ 30, sugerido R$ 90 e final R$ 35 resultam em redução R$ 55 (61,11%) e resultado à referência R$ 5; o desconto não é reaplicado.
5. **Salvar previsão** preserva valores históricos e não altera estoque, horas ou caixa. Em **Histórico**, confirme tempo/consumo reais somente depois da impressão: saldos conhecidos diminuem, desconhecidos permanecem desconhecidos e minutos confirmados são somados à máquina. A confirmação não pode ser repetida.
6. Em **Configurações → Precificação e alerta de filamento**, altere acréscimo padrão e limite de saldo baixo (inicial 100 g). A calculadora aberta só troca o percentual informado ao clicar em Atualizar parâmetros; históricos não mudam.

Veja `docs/fase2.md` para critérios de custo, arredondamento e limites do fluxo.

## Usar a Fase 3

1. Em **Produtos**, cadastre modelos (MOD-0001) e variantes. Importe fotos reais e versões STL/3MF; selecione principal/preferencial. Dados do fatiamento são manuais.
2. Em **Estoque → Auxiliares**, registre materiais, saldo, consumo, ajustes e perdas com justificativa.
3. Em **Peças prontas**, registre peças existentes ou selecione um cálculo real confirmado para produção sem cliente, reaproveitando custo sem consumir filamento novamente.
4. Registre a verificação prévia ou mantenha peças aguardando verificação. Peças pessoais precisam de nova verificação para disponibilidade.
5. Reserve disponíveis, libere ou faça baixa física justificada; físico, reservado e disponível são distintos. Descarte registra custo existente apenas uma vez.
6. Consulte **Movimentos** e **Perdas**. Configure Bambu Studio em Configurações se desejar abrir projetos no software já instalado.

Veja `docs/fase3.md` para custos, arquivos, estoques e limites da verificação preliminar; resultados em `docs/resultados-fase3.md`.

## Usar a Fase 4

1. Em **Vendas → Clientes**, cadastre nome e contatos opcionais.
2. Crie orçamento com produtos ou itens personalizados, preços finais unitários e frete. PDF é emitido; não há reserva nem receita antes da aprovação.
3. Aprove sem redigitar ou crie pedido direto. Registre entrada opcional e parcelas do saldo; a tabela permite valores/datas personalizados.
4. Em **Pedidos → Detalhes**, registre pagamentos/taxas, veja alocações e PDFs versionados. Crédito do cliente pode ser aplicado sem novo recebimento em caixa.
5. Vincule cálculos e reserve peças disponíveis. Envio/retirada baixa estoque uma vez; entrega posterior não duplica baixa.
6. Cancelamento preserva custos/histórico e registra reembolso, crédito futuro ou retenção justificada. Peças já baixadas só retornam após confirmação física e nova verificação.

Leia `docs/fase4.md` e `docs/resultados-fase4.md`. Configure o logo oficial antes de emitir documentos finais. Produção formal está na Fase 5; financeiro e relatórios estão na Fase 6.

## Usar a Fase 5

1. Em **Produção**, crie OP para estoque ou item de pedido, com arquivo/versão, parâmetros, responsável e modelos/carretéis do lote.
2. Priorize e reordene a fila; inicie na impressora. Confirme minutos e gramas reais incluindo falhas; cronômetro/progresso somente sugerem valores.
3. Inspecione cada peça com checklist e três fotos distintas (frente, lateral/verso, detalhe). Conclua a OP para liberar aprovadas ao estoque.
4. Reimpressão gera nova OP com referências atuais e substituição de carretéis. Problemas e fotos permanecem no histórico. Alterações exigem revalidação.
5. Consulte procedimentos PO-001 a PO-012 e FR-001 na tela ou em `docs/procedimentos-internos.md`.

Leia `docs/fase5.md` e `docs/resultados-fase5.md` para custos com perdas, entradas preexistentes e limites. Pacote de revisão: `dist/DrHeekLab-2.4.0-source.zip`. O executável em `dist/DrHeekLab/DrHeekLab` é Linux; mantenha toda a pasta.

## Usar a Fase 6

1. Em **Financeiro**, filtre período e relatório comercial por cliente/produto/impressora/situação.
2. Cadastre contas e parcelas; registre pagamentos parciais, taxas e comprovantes. Criar obrigação não paga caixa.
3. Compre filamentos/materiais no fluxo integrado ou vincule carretel existente, sem duplicar saldo. Consumo não paga a compra novamente.
4. Registre aportes/retiradas/saldo inicial e estornos justificados, separados de venda/despesa operacional.
5. Consulte CPV, custo de produção, perdas, resultado provisório, caixa e reconciliação; exporte CSV/Excel.

Leia `docs/fase6.md` e `docs/resultados-fase6.md`. Revisão em `dist/DrHeekLab-2.5.0-source.zip`; pacote de teste Linux em `dist/DrHeekLab-2.5.0-linux.zip`. Instalador Windows ainda pendente de geração/homologação.

## Usar a Fase 7

1. Em **Configurações**, abra a central de documentos para PDFs financeiros/de produção, catálogo, auditoria e lixeira.
2. Configure o logo original; selecione variantes/fotos e confirme preço da oferta. Exporte a cópia PDF para compartilhar manualmente pelo WhatsApp.
3. Consulte o botão **Notificações** para estoque baixo, contas/recebimentos, entregas, manutenção e validade dos orçamentos. Ler/adiar não resolve a obrigação.
4. Arquive/restaure registros com motivo e vínculos preservados; arquivos não são apagados.
5. Backup completo é verificado antes da atualização. Se a abertura falhar, use **Recuperar de backup**, com senha e confirmação; estado original permanece em rollback.

Leia `docs/fase7.md` e `docs/resultados-fase7.md`. Código: `dist/DrHeekLab-2.6.0-source.zip`; pacote de teste Linux: `dist/DrHeekLab-2.6.0-linux.zip`. Windows continua pendente de geração/homologação.

## Finalização autônoma — versão 2.8.0

Backup criptografado opcional (.hbk), backup sem interface/agendamento Windows e verificação de dados antes de instalar/atualizar. Leia `docs/finalizacao-autonoma.md`, `docs/resultados-2.8.0.md` e `docs/CONTINUIDADE.md`. Código: `dist/DrHeekLab-2.8.0-source.zip`; teste Linux: `dist/DrHeekLab-2.8.0-linux.zip`. Windows ainda precisa ser gerado e homologado; push/release não autorizados.

## Fase 8 — candidato à homologação

Busca global no cabeçalho, atalho Nova produção e histórico de versões em Sobre. Leia `docs/fase8.md`, `docs/matriz-testes.md` e `docs/resultados-fase8.md`. Pacotes 2.7.0 em `dist/DrHeekLab-2.7.0-source.zip` e `dist/DrHeekLab-2.7.0-linux.zip`. Linux não executa no Windows.

## Testar

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.venv\Scripts\python -m pytest -q
Remove-Item Env:QT_QPA_PLATFORM
```

Linux: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q`.

## Estrutura

- `storage.py`: migrações, pastas isoladas, transações, configurações, auditoria e rascunhos.
- `security.py` / `backup.py`: senha, backup consistente, arquivos e restauração.
- `pricing.py`: cálculos Decimal e formatação brasileira.
- `catalog.py`: validação, cadastros, manutenção, snapshots, consumo e tempo confirmados.
- `sales.py` / `sales_documents.py` / `transactions.py` / `migration4.py`: clientes, fluxo comercial, pagamentos, PDFs e transações integradas.
- `products.py` / `inventory.py` / `journal.py` / `migration3.py`: produtos, arquivos, peças, materiais e diário transacional.
- `phase2_ui.py` / `phase3_ui.py` / `phase4_ui.py` / `ui.py` / `app.py`: formulários e interface desktop.
- `tests/`: testes matemáticos, integração e Qt offscreen.
- `packaging/` e `.github/workflows/windows.yml`: preparação do empacotamento Windows.
- `docs/`: especificação mestre, manual, oito fases, resultados e checklist Windows.

O logotipo da conversa é a referência oficial. Como a imagem não está disponível como arquivo no checkout, há espaço reservado identificado. Importe o original em **Configurações → Marca**; ele será armazenado e incluído nos backups. Não foi criado substituto.

## Verificar o pacote instalado

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m drheeklab --self-test
# Após empacotar em Linux:
QT_QPA_PLATFORM=offscreen dist/DrHeekLab/DrHeekLab --self-test
```

No Windows empacotado: `DrHeekLab.exe --self-test`. Usa somente dados temporários; não aceita `--environment` ou `--data-dir` nesse modo. Para gravar evidência, use `--self-test --self-test-report C:\caminho\qa.json`. Código de saída 0 e JSON status passed/versão correta indicam sucesso funcional; não equivalem à homologação da interface Windows.

## Empacotar

Neste ambiente Linux, o pacote de testes fica em `dist/DrHeekLab/DrHeekLab`. Mantenha toda a pasta `dist/DrHeekLab`, pois inclui dependências; esse binário **não executa no Windows**.

Em Windows x64, com Python 3.12 e Inno Setup 6:

```powershell
./packaging/build-windows.ps1
# Com ícone oficial .ico fornecido:
./packaging/build-windows.ps1 -IconPath C:\caminho\marca-oficial.ico
```

Saídas esperadas: `dist\DrHeekLab\DrHeekLab.exe` e `dist\installer\DrHeekLab-2.8.0-Fase8-Setup.exe`. Usuário final não precisa de Python. Binários ficam em Program Files; dados em `C:\DrHeekLab` não são removidos pela desinstalação. Execute `docs/validacao-windows.md` antes de distribuir. Scripts e workflow estão preparados, mas **não foram executados em Windows**.
