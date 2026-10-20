# Database-backed fractional LSTM research

Run the database-backed experiment from `backend`:

```powershell
python -m tools.run_fractional_research --output .\fractional-lstm-results.json
```

The CLI writes Chinese JSON field names and descriptive text. Technical
identifiers, ticker symbols, GPU names, and model weight keys remain unchanged.
The existing simulator reports annualized return using its 252-trading-day
convention. Sample-comparison reports also summarize average, minimum, and
maximum annualized returns.

## Execution-fee sensitivity replay

Replay saved forecasts without retraining:

```powershell
python -m tools.replay_fractional_execution `
  .\fractional-lstm-results-seed-43-zh.json `
  .\fractional-lstm-results-seed-44-zh.json `
  --output .\fractional-lstm-execution-current-fees-zh.json
```

Default assumptions for this sensitivity test:

- Broker commission: 0.03% per side, minimum RMB 5 per order. For this run,
  the user confirmed that the commission includes exchange handling and
  regulatory fees; the handling fee is not charged twice. Real account rates
  vary by broker and account contract.
- Shanghai A-share transfer fee: 0.001% per side.
- Stock sale stamp duty: 0.05% on sells only.
- Buys are in 100-share lots; sells are limited to settled shares.

These current fees are applied uniformly across the historical test period,
not claimed as the actual rate paid during each historical year. The result
reports commission, transfer fee, and stamp duty separately. The database does
not supply verified historical daily limit prices/ST status or dividend
payment dates. The simulator does not model price-limit fills or tax on
dividends; dividends remain non-spendable receivables. The nominal price data
also has not been externally verified. Treat results as sensitivity analysis,
not executable backtest or live-trading returns.
