# Matriz dos critérios obrigatórios — Fase 8

Testes reais sobre serviços e interface, SQLite temporário e arquivos/PDFs/Excel verificáveis. Suíte inteira bloqueia empacotamento em falha; não substitui homologação Windows. Resultados da execução atual em `resultados-fase8.md`.

| Critério da especificação | Evidência automatizada |
|---|---|
| Custo por grama e aquisição/referência | `test_phase2.py::test_cost_per_gram_and_free_material` |
| Vários filamentos, auxiliares e quantidade | `test_phase2.py::test_multiple_filaments_auxiliary_and_units` |
| Custo horário por impressora | `test_phase2.py::test_different_printers_have_independent_rates` |
| Acréscimo 200%, final manual, desconto único | `test_phase2.py::test_manual_final_price_discount_is_not_applied_twice` |
| Pagamentos parciais, taxas, recebíveis | `test_phase4.py::test_partial_payments_fees_fifo_freight_and_installments_reconcile` |
| Parcelas, centavos e atraso | `test_phase4.py::test_installments_rounding_month_ends_and_overdue_partial_status` |
| Consumo atômico e uma única vez | `test_phase2.py::test_confirmed_consumption_and_hours_are_atomic_and_once_only` |
| Reserva/liberação e baixa física | `test_phase3.py::test_stock_cost_allocation_reconciles_and_reservation_does_not_reduce_physical`, `test_phase4.py::test_cancellation_refund_credit_retention_releases_stock_and_preserves_cost` |
| Produção para estoque | `test_phase3.py::test_production_for_stock_reuses_confirmed_cost_without_consuming_again`, `test_phase5.py` e QA integrado |
| Falhas/perdas e rateio de lotes | `test_phase5.py`, `test_phase6.py::test_actual_op_failure_cpv_and_printer_results_no_double_cash` |
| Cancelamentos/reembolsos | `test_phase4.py::test_cancellation_refund_credit_retention_releases_stock_and_preserves_cost` |
| Previsto versus real e histórico | `test_phase2.py::test_historical_rates_remain_frozen_after_catalog_changes`, `test_phase5.py` |
| Integridade financeira e CPV | `test_phase6.py::test_cash_sale_cpv_fees_and_capital_are_separate`, `test_reconciliation_detects_corruption_instead_of_claiming_ready` |
| Persistência após reiniciar | `test_core.py::test_restart_persistence`, `test_phase8.py::test_self_test_report_has_real_integrated_result` e QA empacotado |
| Backup/restauração | `test_core.py`, `test_phase7.py::test_backup_general_pdfs_transfer_and_corrupt_database_recovery` |
| Migração/atualização sem perda | `test_phase8.py::test_update_every_previous_schema_preserves_login_drafts_and_settings` (esquemas 1–6), testes de falha em `test_core.py`/`test_phase7.py` |
| Busca literal, sete tipos, sem alteração | `test_phase8.py::test_global_search_locates_all_seven_types_without_changes` |
| Arquivados, navegação e histórico offline | `test_phase8.py::test_search_archived_history_and_ui_navigation`, `test_about_contains_packaged_history_and_current_version` |
| QA não usa dados reais; falha não vira sucesso | `test_phase8.py::test_qa_rejects_user_data_and_report_without_qa`, `test_failed_self_test_cannot_produce_success_report` |
| Windows / instalação / ícone / ausência de Python | Workflow/scripts preparados; execução e homologação pendentes em `homologacao-windows.md` |

Os demais testes anteriores de domínio/interface permanecem ativos. Capturas offscreen e binário Linux são evidências limitadas a essa plataforma.

## Finalização 2.8.0

`test_finalization.py`: criptografia/transferência, senha incorreta/adulteração/truncamento, preservação de arquivo existente, symlink, erro de disco/saída parcial, backup diário/CLI/trava/deduplicação, separação de ambientes, preflight/versionamento, XML/registro assistido, interface e invariância financeira/estoque após backup. 21 novos casos em Linux; 227 anteriores preservados. Resultado total e limitações Windows em `resultados-2.8.0.md`.
