# Início — produção e posição de estoque

Início remove Pedidos em andamento, mantém Vendido no mês, Recebido líquido no mês e A receber total, gráfico e atalhos. Estados da produção mantidos: Aguardando, Imprimindo, Aguardando inspeção e Concluído.

Nova linha de cartões: Filamentos (valor de aquisição restante conhecido, número de carretéis ativos, kg conhecidos restantes e número de saldos desconhecidos), Acessórios (custo e unidades em mãos), Estoque total (filamentos + acessórios + peças, com valor das peças detalhado). Saldo desconhecido contribui zero ao valor e peso, sem transformar seu registro desconhecido em zero conhecido. Carretéis finalizados e arquivados não entram no estoque atual.

Totais usam o mesmo serviço do Estoque, incluindo disponíveis/reservados/a verificar/uso pessoal e excluindo baixadas/descartadas. Atualização ao abrir Início; sem pagamento, despesa ou escrita contábil nova. Funcionalidades financeiras e atalhos preservados. Teste real comprova rolo desconhecido fora do valor/kg e atualização após venda/saída.

Validação local: 8 testes de interface/valoração aprovados. Captura com dados de demonstração: capturas-inicio-estoque/inicio.png. Versão 2.9.1/schema10 mantidos. ZIP somente mediante pedido explícito.

Suíte Windows aprovada no run38674361176, código edf3be6d2db825d2b46c32080b9d427d74357f59; pacote ignorado.
