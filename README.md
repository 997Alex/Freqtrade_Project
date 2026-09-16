# Freqtrade Project - EmaRsiTrendStrategy

## Struttura del progetto

```
C:\Users\Ale\Desktop\Freqtrade_Project\
├── user_data/
│   ├── config.json              # Configurazione principale (dry_run: true)
│   ├── strategies/
│   │   └── ema_rsi_trend_strategy.py  # Strategia EmaRsiTrendStrategy
│   ├── data/
│   │   └── binance/             # Dati storici Binance (9000 candele x coppia)
│   │       ├── BTC-EUR-1h.csv
│   │       ├── ETH-EUR-1h.csv
│   │       └── SOL-EUR-1h.csv
│   ├── backtest_results/        # Risultati backtest
│   └── tradesv3.dryrun.sqlite  # DB dry-run
```

## Comandi utili

### Backtest
```bash
cd C:\Users\Ale\Desktop\Freqtrade_Project
freqtrade backtesting --strategy EmaRsiTrendStrategy --timerange 20230101-20240110 --breakdown month -c user_data\config.json
```

### Dry-run (simulazione, zero soldi reali)
```bash
freqtrade trade -c user_data\config.json --dry-run --strategy EmaRsiTrendStrategy
```

### Scaricare nuovi dati
```bash
freqtrade download-data --exchange binance --pairs BTC/EUR ETH/EUR SOL/EUR -t 1h --timerange 20230101-20240110 -c user_data\config.json
```

### Hyperopt (ottimizzazione parametri)
```bash
freqtrade hyperopt --strategy EmaRsiTrendStrategy --hyperopt-los-cutoff 100 -c user_data\config.json
```

## Risultati Backtest (2023-01-09 → 2024-01-10)

| Metric | Value |
|--------|-------|
| Trade totali | 74 |
| Win Rate | 73% (54W/20L) |
| Profitto totale | +8.079 EUR (+0.81%) |
| Max Drawdown | 3.52% |
| Sharpe | 0.07 |
| Sortino | 0.10 |
| Profit Factor | 1.05 |
| Best Pair | SOL/EUR (+5.06%) |
| Worst Pair | BTC/EUR (-2.53%) |

## Prossimi passi

1. **Dry-run prolungato**: eseguire `freqtrade trade -c user_data\config.json --dry-run --strategy EmaRsiTrendStrategy` per almeno 1-2 settimane
2. **Creare chiavi API su Binance**: [api.binance.com](https://api.binance.com) → API Keys → solo "Read/Write" (NO withdrawal)
3. **Aggiornare config.json**: inserire key e secret nel file `secrets.json` separato
4. **Passare a trading reale**: impostare `"dry_run": false` in config.json
5. **Ottimizzazione**: usare `freqtrade hyperopt` per affinare i parametri

## Note importanti

- ⚠️ **dry_run è su true** nel config.json - nessun soldo reale coinvolto
- ⚠️ Le API keys sono vuote - non inserirle finché non sei in dry-run testato
- ⚠️ La strategia ha avuto risultati molto conservativi (+0.81% su 1 anno)
- ⚠️ **Non è consulenza finanziaria** - il trading comporta il rischio concreto di perdere tutto il capitale
