# ZIP atualizado solicitado e verificado

[Download no GitHub](https://github.com/d28ty8rky9-star/drheeklab/actions/runs/38651226605/artifacts/11935270883). Cópia local: `dist/DrHeekLab-2.9.1-CadastroCompleto-Windows.zip`.

Este ZIP inclui a ficha completa dentro de Nova peça / Editar peça. 294 testes Windows aprovados e instalação/reinstalação/preservação de dados verificadas. ZIP e hashes verificados; integração do formulário confirmada dentro do executável. Extrair em pasta nova e executar `installer/DrHeekLab-2.9.1-Fase8-Setup.exe`. Preservar `C:\DrHeekLab`. Avaliação prática do proprietário ainda pendente.

# Ficha completa dentro de Nova peça / Editar peça — 2.9.1

Correção da entrega anterior: cálculo e Extras tinham ficado numa janela separada da janela Nova peça/Editar peça mostrada pelo usuário. Agora estão dentro da própria janela de cadastro.

**Produção → Nova peça** abre nome, categoria, impressora, parâmetros, horas, custo automático e preço sugerido. Na mesma janela:

- **Filamentos e arquivos**: vários carretéis, gramas por peça, outros custos adicionais, STL/3MF existente ou importação de novo arquivo.
- **Extras**: argolas, acessórios, quantidade e custo unitário, somados automaticamente.
- **Variante**: nome, tamanho, cor e material. Ao editar, corresponde à variante selecionada na lista.
- **Fotos**: fotos do cadastro, sem precisar sair da janela.
- **Descrição e qualidade**: observações e informações da peça.

O custo atualiza ao alterar carretéis, gramas, horas, adicionais ou extras. Quando a ficha está preenchida, o campo de custo é calculado e não precisa de digitação manual. Campos incompletos exibem o dado que falta, sem mostrar custo antigo como se fosse novo. O botão superior de ficha também abre essa mesma janela completa.

Pode salvar apenas a ideia, ou uma ficha de custos ainda sem STL/parâmetros. Arquivo e parâmetros válidos são obrigatórios para criar a OP. Cadastro, cálculo, importação de fotos/arquivo e extras não movimentam o saldo dos materiais, das peças ou o Financeiro. A OP aproveita os dados salvos; reconhecimento do custo e disponibilidade seguem na conclusão/entrada no Estoque.

Salvar ocorre em uma transação: se arquivo, foto, variante ou ficha falhar, cadastro e arquivos copiados nesta tentativa são desfeitos. Arquivos anteriores e originais do usuário são preservados. Fichas/OPs antigas permanecem intactas; schema 9 e versão 2.9.1 mantidos.

Capturas reais da janela Nova peça, com dados temporários:

- [Ficha completa e custo automático](capturas-cadastro-producao/nova-peca-completa.png)
- [Extras dentro de Nova peça](capturas-cadastro-producao/extras-na-nova-peca.png)

294 testes locais aprovados, zero falhas/erros/pulos; suíte completa [Windows aprovada](https://github.com/d28ty8rky9-star/drheeklab/actions/runs/38508888418). Empacotamento ignorado, zero artefatos. Evidências em `evidencias-cadastro-producao/`. Pacote completo atualizado gerado após pedido explícito: ver download abaixo. Novos ZIPs/instaladores somente sob pedido explícito. Avaliação prática do proprietário no Windows permanece pendente.
