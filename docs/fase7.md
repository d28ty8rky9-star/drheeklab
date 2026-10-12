# Fase 7 — documentos, catálogo, alertas e recuperação

Versão 2.6.0, SQLite 7. Avanço autorizado pelo proprietário. O avanço para a Fase 8 foi autorizado; veja `fase8.md` para finalização e pendências Windows. Aplicativo offline; geração e homologação do instalador Windows ainda pendentes.

## Documentos e catálogo

Em **Configurações → Documentos, catálogo, auditoria e lixeira**, abra a central de documentos. Orçamentos e comprovantes comerciais permanecem em **Vendas**, com seu histórico de versões e preços finais.

- **PDF financeiro**: período, indicadores, CPV, caixa, contas, produção, perdas/absorção, resultados por produto/impressora e critérios de reconciliação. O botão **Financeiro → Emitir PDF** preserva os filtros de cliente, produto, impressora e situação atualmente selecionados. Relatório interno e gerencial, sem documento fiscal.
- **PDF produção**: OP, responsável, estado/revisão, parâmetros, impressora, tempo previsto, custos previstos/reais, modelos/versões, tentativas, consumo, falhas e inspeções individuais FR-001 com fotos/checklists/históricos/problemas. Também disponível no botão **Produção → Emitir relatório PDF da OP**. Não é certificação ISO.
- **Catálogo PDF**: selecione as variantes, confira preço escolhido e descrição resumida. Exige foto de cada produto selecionado, importada em Produtos; não inventa fotografia nem preço. Valores sugeridos podem ser alterados explicitamente para essa oferta, sem mudar o cadastro ou pedidos. Não imprime custos internos.

**Marca:** importe o arquivo original PNG/JPEG do logo em Configurações. Documentos usam a marca configurada com a identidade visual roxa/ciano do aplicativo. Se o original ainda não estiver configurado, a ausência é explicitamente marcada como documento de revisão. Não foi criada uma cópia fictícia do logo enviado na conversa; importe o arquivo original antes de compartilhar documentos finais.

Os novos PDFs são arquivos próprios com código, versão, data/hora, versão do aplicativo, snapshot dos dados/marca e SHA-256. Alterar cadastro, preços, logo ou OP não muda o arquivo emitido anteriormente. Emissão repetida da mesma seleção/período/OP cria nova versão; arquivar não reinicia a numeração. Abrir/exportar confere o hash. Se o PDF estiver ausente/alterado, restaure backup completo.

**Exportar cópia para compartilhar** salva um PDF portátil idêntico ao emitido. Anexe manualmente pelo WhatsApp ou outro canal; não há integração obrigatória nem envio automático. A cópia original permanece no armazenamento gerenciado. PDFs internos financeiros/de produção devem ser tratados como internos; o catálogo é a oferta pública com preço escolhido.

## Notificações

O botão **Notificações** no cabeçalho mostra a quantidade de alertas novos não adiados. Atualização periódica a cada minuto ou manual no diálogo:

- Filamento baixo com saldo conhecido; saldo desconhecido não é convertido em zero.
- Recebimentos e contas a pagar vencidos ou próximos do vencimento, com saldo pendente.
- Entregas aguardando saída/recebimento; prazo passado recebe prioridade urgente.
- Impressoras em manutenção ou com manutenção programada próxima/vencida; a programação mais recente substitui a anterior.
- Orçamentos pendentes vencidos ou próximos da validade. Aprovados/rejeitados saem do alerta.

Próximos vencimentos usam sete dias por padrão. **Abrir área** leva ao módulo correspondente; **Marcar lido** e **Adiar um dia** apenas alteram o alerta, sem pagar, entregar ou executar manutenção. Adiados ficam ocultos por padrão, mas podem ser consultados. Mudança relevante de saldo/prazo/condição volta a alertar; condição resolvida encerra o alerta e uma recorrência pode aparecer como nova. Estado de leitura/adiação persiste em SQLite e é auditado.

## Auditoria e lixeira

A central possui **Auditoria**, com filtros de datas, operação, registro e justificativa, valores anteriores/novos e exportação CSV. Busca é literal, sem curingas SQL; texto de fórmula em CSV permanece literal. Consulta mostra até 1.000 eventos por filtro na interface.

Em **Lixeira**, escolha arquivados para restaurar ou ativos para arquivar. Cadastros suportados: produtos, variantes, impressoras, filamentos, materiais, clientes, categorias de despesas; também fotos, versões STL/3MF e os novos PDFs emitidos. Toda ação exige motivo e mantém arquivos e vínculos históricos.

- Restaure o produto antes da variante/foto/arquivo dependente.
- Reservas existentes continuam protegidas pelos serviços de estoque/produto.
- Versão STL/3MF usada por OP ativa não pode ser arquivada. Após conclusão, histórico/arquivo continuam preservados; nova OP exige versão ativa/restaurada.
- Arquivo/PDF restaurado precisa existir e conferir com o hash.
- Arquivar mídia retira da seleção/galeria, sem apagá-la fisicamente. Definir principal/preferencial exige mídia ativa.
- Cancelamentos financeiros, perdas e peças entregues não são revividos pela lixeira. Use os fluxos documentados de Vendas/Estoque para novos pedidos e retorno físico real. Não há exclusão física automática.

## Backup, atualização e outro computador

Backup diário automático, manual e local/externo continuam disponíveis. **Criar backup completo (local ou externo)** permite escolher pasta, HD ou pendrive. Inclui SQLite consistente pela API `backup`, fotos/projetos, comprovantes, novos PDFs, marca e demais pastas permanentes. Manifesto verifica arquivos, integridade, vínculos, esquema e hashes. Arquivados permanecem no backup. Backups não são simplesmente cópias inseguras do banco ativo.

Antes de migração, a abertura cria **backup completo verificado**, além da preservação SQLite anterior. Se algum vínculo estiver ausente/alterado, não avança o esquema. Migração é transacional; falha preserva esquema/registros originais, mantém backup e registra resultado em Logs. Versão de banco mais recente exige aplicativo compatível; não é rebaixada automaticamente.

Para transferir, copie o ZIP completo para o outro computador e restaure no mesmo ambiente TESTES ou PRODUÇÃO. Caminhos de arquivos são relativos; não dependem da antiga pasta absoluta. A senha do backup acompanha os dados. Faça teste no ambiente correto e mantenha o ZIP original preservado.

## Recuperação com confirmação

Pelo aplicativo aberto: **Configurações → Restaurar backup deste ambiente**. Confirme a substituição; o estado anterior permanece em uma pasta de rollback. O programa fecha; abra novamente usando a senha do backup.

Se a abertura normal falhar, a tela de erro oferece **Recuperar de backup**, sem exigir comandos. Selecione o ZIP, entre com a senha da cópia verificada e confirme o ambiente/destino. Antes da confirmação, os dados atuais não são substituídos. Backup sem senha ainda configurada permite criar uma senha na cópia temporária verificada; a senha escolhida acompanha a restauração.

Também há comando opcional para suporte técnico:

```powershell
DrHeekLab.exe --environment test --data-dir C:\DrHeekLab --restore-backup E:\backup.zip
```

Linux/desenvolvimento: `.venv/bin/python -m drheeklab --environment test --data-dir /caminho/dos/dados --restore-backup /caminho/backup.zip`.

O backup é validado em pasta temporária antes de tocar no destino. Recuperação aceita banco atual corrompido ou arquivos ausentes, mantendo a árvore anterior em rollback, incluindo os bytes do banco corrompido. Estado danificado não é anunciado como backup verificado. Falha durante cópia retorna à árvore original. Backup de outro ambiente ou esquema incompatível é rejeitado. Nunca apague banco ou arquivos para resolver erro.

Teste funcional e pacote: `resultados-fase7.md`. Roteiro Windows: `validacao-windows.md`. A Fase 8 foi autorizada; finalização e pendências de homologação estão em `fase8.md`.
