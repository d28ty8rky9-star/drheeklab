# Pacote completo solicitado e entregue

[Download do ZIP no GitHub](https://github.com/d28ty8rky9-star/drheeklab/actions/runs/38506019047/artifacts/11868460181). Cópia local: `dist/DrHeekLab-2.9.1-Extras-Producao-Windows.zip`.

Inclui as alterações de Produção, Extras, Estoque de peças compradas e tempo em horas. Extrair em pasta nova e executar `installer/DrHeekLab-2.9.1-Fase8-Setup.exe`. Preservar `C:\DrHeekLab` e fazer backup antes de reinstalar. 289 testes Windows aprovados e instalação/reinstalação/preservação de dados verificadas; hashes/CRC do ZIP conferidos. Avaliação prática do proprietário permanece pendente. Novos pacotes somente sob pedido explícito.

# Produção com extras e cálculo automático — 2.9.1

Em **Produção → Ficha de produção / custos**, o custo muda automaticamente ao escolher filamentos, alterar gramas, horas ou outros custos adicionais. Não precisa clicar em Calcular nem selecionar um STL para visualizar a prévia; o arquivo continua obrigatório para salvar a ficha e gerar uma OP.

A aba **Extras • argolas e acessórios** permite adicionar/remover itens com nome, quantidade por peça e custo unitário. Exemplo: 2 argolas × R$ 0,50 = R$ 1,00 por peça. O total dos extras é somado ao material, à máquina e aos outros custos adicionais. Não informe novamente no campo Outros custos adicionais um item que já detalhou em Extras.

Os extras são salvos por variante, reaparecem ao editar a ficha e integram a cópia usada pela OP. A quantidade da OP multiplica o total por peça. Alterações posteriores na ficha não alteram os extras/custos de uma OP existente. Fichas antigas sem extras conservam seu custo adicional original.

A OP continua usando a ficha salva para controlar quantidade, prioridade, espera, impressão, inspeção e conclusão, sem repetir o cadastro dos materiais ou dos extras. O custo é demonstrativo em Produção; só é reconhecido no Financeiro após a conclusão e entrada das peças no Estoque, sem pagamento automático. Os extras detalham custo; cadastrar uma argola aqui não baixa automaticamente materiais auxiliares do estoque.

Banco continua no schema 9; novos detalhes ficam no JSON versionado da ficha, sem reescrever OPs/dados históricos. Versão permanece 2.9.1. ZIP/instalador somente quando solicitados; o pacote anterior não contém estas alterações.

Capturas Qt com dados descartáveis:

- [Filamentos, horas e valor automático](capturas-extras-producao/filamentos-horas.png)
- [Extras com quantidade e custo](capturas-extras-producao/extras.png)

289 testes locais aprovados, zero falhas/erros/pulos. Suíte completa [Windows aprovada](https://github.com/d28ty8rky9-star/drheeklab/actions/runs/38504392901); pacote ignorado e zero artefatos. Evidências de testes em `evidencias-extras-producao/`. Avaliação prática do proprietário no Windows permanece pendente.
