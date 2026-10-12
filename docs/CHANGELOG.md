# Histórico

## 2.8.0 — finalização autônoma (candidato à homologação Windows)

- Backup opcional criptografado com AES-256-GCM/scrypt; senha não persistida, integridade autenticada antes da restauração e suporte .hbk na interface/recuperação.
- Saída de backup por arquivo temporário verificado e publicação local atômica; falhas não deixam um ZIP parcial apresentado como válido; links simbólicos gerenciados bloqueados.
- Backup sem interface com trava do ambiente, deduplicação diária e logs; tarefa Windows do usuário conectado, privilégio normal, configuração assistida XML e destino externo. Agendamento cria ZIP sem criptografia, explicitamente informado.
- Verificador pré-instalação independente: protege todos os ambientes existentes, cria backups completos antes de substituir binários, bloqueia ambientes em uso/banco mais novo ou danificado.
- Versão nas propriedades do .exe, bloqueio de downgrade de binários versionados, preservação de permissões existentes e relatórios/checksums de build.
- Restauração com senha incorreta rejeitada antes de confirmação/substituição, mantendo a janela e os dados atuais.
- Esquema SQLite permanece 7. Windows/instalador/Agendador ainda pendentes de execução e homologação; push e publicação não autorizados.

## 2.7.0 — Fase 8 (candidato à homologação)

- Busca global literal por clientes, pedidos, orçamentos, produtos, projetos, filamentos e produção; arquivos e histórico arquivado permanecem identificados.
- Tela Sobre com histórico de versões disponível também no pacote offline.
- Verificação funcional exercita reinício/persistência; relatório JSON verificável mesmo no executável Windows sem console.
- Regressão de atualização de todos os esquemas anteriores, preservando senha, preferências e rascunhos.
- Build Windows bloqueia instalador em falha de dependências, testes ou QA; validação automatizada de instalação, reinstalação e desinstalação em runner descartável.
- Documentação final, matriz de testes e pacotes de revisão. Esquema SQLite permanece 7. Geração/homologação Windows e ícone oficial ainda pendentes.

## 2.6.0 — Fase 7

- PDFs financeiros/de produção com marca configurada, dados congelados, versões/códigos, fotos FR-001 e hash; catálogo público com seleção, fotos e preço escolhido.
- Cópia PDF portátil para compartilhamento manual; original preservado. Documento de revisão explícito quando logo ainda ausente.
- Notificações persistentes de saldo baixo, vencimentos, entregas, manutenção e orçamentos; leitura/adiação sem efeito financeiro e recorrência como alerta novo.
- Central de documentos, auditoria filtrável/CSV e lixeira de cadastros, mídias e PDFs, sem exclusão física nem reviver cancelamentos.
- Backup completo verificado antes de migração, migração transacional com falha registrada, recuperação gráfica/CLI com senha/confirmacão, banco corrompido e transferência de computador.
- Rollback preserva árvore original e bytes de banco corrompido; erro de cópia recompõe estado anterior.
- SQLite 6 → 7; novos PDFs e arquivos arquivados no backup. Homologação Windows permanece pendente para a Fase 8.


## 2.5.0 — Fase 6

- Financeiro com contas/parcelas, pagamentos parciais, comprovantes, categorias editáveis e classificação histórica preservada.
- Caixa por fontes, aportes/retiradas/saldo inicial e estornos justificados, sem confundir financiamento do proprietário com venda.
- Compras integradas de carretéis/materiais e vínculo de compra existente sem duplicar saldo; consumo não cria saída de caixa.
- CPV congelado na baixa física, retorno com custo original, perdas absorvidas/baixas de estoque sem duplicação.
- Indicadores por período e filtros comerciais, resultado gerencial provisório, saldo até data final e rateio de centavos entre impressoras.
- Relatórios/reconciliação e exportação CSV/Excel com proteção de texto contra fórmulas.
- Migração SQLite 5 → 6, backup de comprovantes e teste funcional empacotado ampliado.
- OpenPyXL 3.1.5 e et_xmlfile 2.0.0 fixados; limpeza Qt por teste. Homologação Windows permanece pendente.


## 2.4.0 — Fase 5

- OP-AAAA-NNNN, fila com prioridades/reordenação, quatro estados, cronômetro sugerido e confirmação real única de tempo/consumo.
- Lotes mistos, carretéis por modelo, custo de máquina único com rateio por gramas ou pesos justificados; falhas/progresso e tentativas preservados.
- Inspeção individual, checklist por categoria, três fotos verificadas, notas leves/reprovação, revalidação e liberação das boas ao concluir.
- Custos com perdas absorvidos nas boas sem duplicação; nova OP de reimpressão com referências atuais e troca de carretéis.
- Histórico de problemas por modelo/OP, inspeções/fotos anteriores, procedimentos PO-001–012 e FR-001.
- Integração com pedidos, estoque e devoluções; backup das evidências e migração SQLite 4 → 5.
- Pacote/validação Linux; geração e homologação Windows pendentes.


## 2.3.0 — Fase 4

Clientes e histórico, orçamentos com validade/PDF e conversão transacional, pedidos aprovados imutáveis, múltiplos itens/personalizados/anexos, entrada e parcelas editáveis, pagamentos parciais, taxas/líquido, alocação FIFO rastreável, contas a receber, crédito do cliente sem caixa fictício, cancelamentos/reembolso/retenção, vínculo a custos incorridos, reservas protegidas, envio/entrega sem baixa duplicada, retorno físico com custo preservado e nova verificação, PDFs versionados com identidade configurada e sem custos internos, migração do esquema 3 para 4 e backups completos compatíveis.

Dependências ReportLab/Pillow para documentos e pypdf para verificação. CLI --self-test valida o pacote em dados temporários; empacotamento Windows bloqueia instalador se testes ou verificação funcional falharem. Windows ainda não homologado; Fases 5–8 aguardam aprovação e implementação.

## 2.2.0 — Fase 3

Produtos MOD-0001, variantes com custos próprios/snapshot, galeria pesquisável com fotos reais, foto principal, versões STL/3MF imutáveis com checksum e preferência, abertura opcional no Bambu Studio, materiais auxiliares, diário de estoque integrado ao consumo de filamentos, peças físicas com custo rateado em centavos, entradas de produção sem novo consumo, reservas/liberação/baixa única, verificação preliminar para peças pessoais e perdas sem duplicação. Migração aditiva de esquema 2 para 3, backups antigos compatíveis e validação dos arquivos vinculados.

Restauração de ZIP íntegro também permite reparar arquivo atual ausente, preservando estado anterior em rollback e registrando sua incompletude. Windows ainda não homologado; Fases 4–8 aguardam aprovação e implementação.

## 2.1.0 — Fase 2

Cadastros auditados de impressoras, manutenção e filamentos; A1 Mini com valores aprovados; referências independentes da aquisição; saldo desconhecido preservado; precificação Decimal com vários filamentos, auxiliares, quantidade e acréscimo padrão 200%; preço final sem desconto duplicado; snapshots históricos; comparação de tempo/consumo reais; confirmação transacional única de consumo e tempo; alerta de saldo baixo; rascunho da calculadora e migração do esquema 1 para 2.

Inclui correção do callback de backup agendado após fechar a janela. Backups de esquema 1 permanecem restauráveis. Windows continua sem homologação; Fases 3–8 pendentes de aprovação e implementação.

## 2.0.0 — Fase 1

Base modular desktop, login PBKDF2-SHA256 com sal aleatório, senha editável, temas e menu persistentes, bancos físicos isolados, migração versionada/transacional, rascunho recuperável, auditoria, logs, backup SQLite consistente com arquivos e checksums, restauração preservando estado anterior e instruções de empacotamento Windows.

Não é lançamento final das oito fases. Instalador Windows e identidade com ícone original ainda não homologados.
