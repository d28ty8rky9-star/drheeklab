# Validação — ficha dentro do cadastro real

Código Windows: 9e4b7be817d10f7e9b017e03ec19d98afe8e213a.

- Suíte local: 294 testes aprovados, zero falhas/erros/pulos; linux-tests.xml.
- Após ajustes de apresentação/entrada pelo botão de ficha: 12 testes de cadastro/workspace aprovados; após guarda de variante ausente, 5 testes do formulário completo aprovados.
- Casos novos: abrir Nova peça, preencher duas bobinas/gramas, 10h e argolas, custo automático R$27; salvar sem outro diálogo e sem arquivo; reabrir todos os dados; importar STL pela mesma janela; gerar OP a partir da receita.
- Editar variante selecionada sem alterar ficha de outra variante; variante/nome/tamanho/cor/material e fotos/STL salvos no mesmo cadastro; rollback de cadastro/receita/arquivos em arquivo ou foto inválida.
- Nenhum consumo/peça/Financeiro no cadastro; OP sem arquivo é bloqueada. Tempo/dados históricos e schema 9 preservados.
- Capturas Qt reais com banco temporário descartado em ../capturas-cadastro-producao/.
- Windows: run 38508888418, suíte completa aprovada. Empacotamento ignorado, zero artefatos; resultados em windows-status.json/windows-artifacts.json.
- Sem gerar novo ZIP/instalador. ZIP anterior mantém cadastro antigo. Avaliação prática do proprietário permanece pendente.
