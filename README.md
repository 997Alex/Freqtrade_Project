# Freqtrade Project — EmaRsiTrendStrategy Suite

> Progetto completo di trading automatizzato con **Freqtrade**, basato su una famiglia di strategie **trend-following con pullback RSI** per coppie BTC/EUR, ETH/EUR e SOL/EUR su timeframe 1h.

---

## 📋 Indice

- [Descrizione Generale del Progetto](#descrizione-generale-del-progetto)
- [Struttura del Progetto](#struttura-del-progetto)
- [Strategie Implementate](#strategie-implementate)
- [Strumenti e Script Utilità](#strumenti-e-script-utility)
- [Configurazioni](#configurazioni)
- [Risultati Backtest e Hyperopt](#risultati-backtest-e-hyperopt)
- [Comandi Utili](#comandi-utili)
- [Protezioni e Risk Management](#protezioni-e-risk-management)
- [Prossimi Passi](#prossimi-passi)
- [Note Importanti](#note-importanti)

---

## 📖 Descrizione Generale del Progetto

Questo repository contiene un progetto di **trading algoritmico** sviluppato con [Freqtrade](https://www.freqtrade.io/), un framework open-source per il trading automatizzato di criptovalute. Il cuore del progetto è una famiglia di strategie di tipo **trend-following con pullback basate su RSI**, evolute attraverso più versioni e ottimizzazioni.

### Filosofia di Progetto

- **Trasparenza**: le strategie sono completamente leggibili e documentate — per ogni trade si conosce esattamente la condizione di ingresso e di uscita (attraverso `enter_tag` e `exit_tag`).
- **Simplicità controllata**: poche condizioni parametriche per ridurre il rischio di overfitting rispetto a strategie con centinaia di regole ottimizzate su dati storici.
- **Risk Management integrato**: protezioni automatiche contro drawdown eccessivi, cooldown tra trade consecutivi, e stop loss rigorosi.
- **Progressione logica**: si parte da una strategia base, si ottimizza con hyperopt, si valida su dati out-of-sample, e solo in un secondo momento si passa al dry-run e al trading reale.

### Coppie e Mercati Coperti

- **Coppie**: BTC/EUR, ETH/EUR, SOL/EUR
- **Exchange**: Binance (spot) / Binance Futures (configurazione separata)
- **Timeframe**: 1 ora (1h)
- **Valuta di riferimento**: EUR (spot) / USDT (futures)
- **Capitali**: testato con 1.000€ virtuali (dry-run)

---

## 📂 Struttura del Progetto

```
C:\Users\PC\Desktop\Freqtrade_Project\
│
├── README.md                          # Questo file
├── analizza_hyperopt.py               # Script di analisi automatica dei risultati hyperopt
├── verifica_drawdown_fix.py           # Script di verifica del calcolo drawdown
├── create_futures_config.py           # Genera config_futures_test.json (EUR pairs, futures)
├── create_futures_config2.py          # Genera config_futures.json (USDT pairs, futures)
├── fix_config.py                      # Rimuove margin_mode dal config.json
├── revert_config.py                   # Riporta il config.json a spot mode
├── avvio.txt                          # Comando rapido per avviare il dry-run
├── hyperopt_all_epochs.csv            # CSV con i risultati di tutti gli epoch di hyperopt
├── hyperopt_summary.csv               # Riepilogo aggregato delle ottimizzazioni hyperopt
│
├── .gitignore                         # File esclusi dal versionamento
│
├── user_data/
│   ├── config.json                    # Configurazione principale (spot, dry_run: true, 1000€)
│   ├── config_futures.json            # Configurazione futures con coppie USDT e leverage 3x
│   ├── config_futures_test.json       # Configurazione futures con coppie EUR e leverage 3x
│   │
│   ├── strategies/                    # Strategie Freqtrade
│   │   ├── ema_rsi_trend_strategy.py              # Strategia base (V1)
│   │   ├── ema_rsi_trend_strategy_hyperopt.py     # Strategia ottimizzabile con IntParameter (V2)
│   │   ├── ema_rsi_trend_strategy_hyperopt_v3.py  # Strategia con split ADX entry + exit differenziato (V3)
│   │   ├── conservative_calmar_loss.py            # Loss function conservativa per hyperopt
│   │   ├── conservative_calmar_loss.json          # Parametri della loss function
│   │   └── ema_rsi_trend_strategy_hyperopt.json   # Parametri ottimizzati
│   │
│   ├── hyperopts/                     # Loss functions custom per hyperopt
│   │   ├── conservative_calmar_loss.py
│   │   └── __init__.py
│   │
│   ├── hyperopt_results/              # Risultati grezzi delle ottimizzazioni hyperopt
│   │   ├── .last_result.json          # Ultimo risultato hyperopt
│   │   ├── hyperopt_tickerdata.pkl    # Dati ticker per hyperopt (escluso)
│   │   └── strategy_*.fthypt          # File di risultato hyperopt (esclusi)
│   │
│   ├── hyperopt_results_raw/          # JSON derivati da analizza_hyperopt.py
│   │   ├── strategy_EmaRsiTrendStrategyHyperopt_2026-09-15_20-54-58.json
│   │   ├── strategy_EmaRsiTrendStrategyHyperopt_2026-09-15_21-03-22.json
│   │   ├── strategy_EmaRsiTrendStrategyHyperopt_2026-09-15_21-05-25.json
│   │   ├── strategy_EmaRsiTrendStrategyHyperopt_2026-09-15_21-07-27.json
│   │   └── strategy_EmaRsiTrendStrategyHyperopt_2026-09-15_21-09-25.json
│   │
│   ├── data/
│   │   ├── binance/                   # Dati storici spot Binance (feather)
│   │   │   ├── BTC_EUR-1h.feather
│   │   │   ├── ETH_EUR-1h.feather
│   │   │   └── SOL_EUR-1h.feather
│   │   └── binance_futures/           # Dati storici futures Binance
│   │
│   ├── backtest_results/              # Risultati dei backtest
│   │   ├── .last_result.json          # Ultimo risultato backtest
│   │   ├── aug2026_backtest.txt       # Log backtest agosto 2026
│   │   ├── v3_*.txt                   # Log di backtest della versione 3 (diverse configurazioni)
│   │   ├── backtest-result-*.meta.json # Metadati dei risultati backtest
│   │   └── backtest-result-*.zip      # Archivi compressi dei risultati (esclusi)
│   │
│   ├── notebooks/                     # Jupyter notebook (se presenti)
│   ├── plot/                          # Grafici generati
│   ├── logs/                          # Log del bot
│   ├── freqaimodels/                  # Modelli AI/ML eventuali (se presenti)
│   │
│   └── backtest_results/
│       └── nfix6-profit_max-bot_*.json  # Confronti con NostalgiaForInfinity
│
└── tradesv3.dryrun.sqlite             # Database delle operazioni di dry-run (escluso)
```

---

## 🎯 Strategie Implementate

### 1. `EmaRsiTrendStrategy` (V1 — Base)

**File**: `user_data/strategies/ema_rsi_trend_strategy.py`

Strategia **trend-following con pullback RSI** di base, completamente hardcoded senza parametri ottimizzabili.

**Logica di ingresso (entry)**:
1. **Trend di fondo rialzista**: `EMA50 > EMA200` (medio termine)
2. **Prezzo sopra il trend**: `close > EMA200`
3. **Pullback (non FOMO)**: `RSI < 30` — ingresso durante un ritracciamento nel trend, non inseguendo i massimi
4. **Volume reale**: `volume > 0`

**Logica di uscita (exit)**:
- `RSI > 75` — uscita per ipercomprato estremo
- `trailing_stop` attivo una volta in guadagno
- `minimal_roi` a scaglioni decrescenti: 15% → 8% (60min) → 4% (3h) → 2% (12h)
- `stoploss` fisso al -3%

**Parametri chiave**:
- `timeframe`: "1h"
- `can_short`: false (solo long)
- `startup_candle_count`: 210 (candele minime per EMA200 affidabile)
- `stoploss`: -0.03 (-3%)
- `minimal_roi`: `{"0": 0.15, "60": 0.08, "180": 0.04, "720": 0.02}`
- `trailing_stop_positive`: 0.02
- `trailing_stop_positive_offset`: 0.04

---

### 2. `EmaRsiTrendStrategyHyperopt` (V2 — Parametrizzata)

**File**: `user_data/strategies/ema_rsi_trend_strategy_hyperopt.py`

Versione **ottimizzabile** della strategia base. Utilizza `IntParameter` per rendere ricercabili le soglie RSI tramite hyperopt.

**Differenza chiave rispetto a V1**:
- `buy_rsi`: `IntParameter(20, 45, default=24, space="buy", optimize=True)` — hyperopt cerca il miglior valore di RSI per l'ingresso
- `sell_rsi`: `IntParameter(60, 85, default=75, space="sell", optimize=True)` — hyperopt cerca il miglior valore di RSI per l'uscita
- `minimal_roi` pre-ottimizzato: `{"0": 0.564, "438": 0.148, "1055": 0.072, "2004": 0}`
- `stoploss`: -0.041
- `trailing_stop_positive`: 0.158
- `trailing_stop_positive_offset`: 0.204

**Uso con hyperopt**:
```bash
freqtrade hyperopt --strategy EmaRsiTrendStrategyHyperopt \
    --hyperopt-loss CalmarHyperOptLoss \
    --spaces buy sell roi stoploss trailing \
    --epochs 300 \
    --timerange 20220101-20240101 \
    -c user_data/config.json
```

**Nota**: stoploss, minimal_roi e trailing_stop sono ottimizzabili automaticamente da Freqtrade senza necessità di IntParameter dedicati.

---

### 3. `EmaRsiTrendStrategyHyperoptV2` (V2.1 — Spazio di Ricerca Ristretto)

**File**: `user_data/strategies/conservative_calmar_loss.py`

Versione con **spazio di ricerca ristretto** per prevenire overfitting su capitali piccoli (1.000€).

**Differenza chiave**:
- Classe `HyperOpt` interna che restringe lo spazio di ricerca:
  - `stoploss`: da -0.10 a -0.02 (mai oltre -10%)
  - `trailing_stop_positive`: da 0.005 a 0.03 (0.5%-3%)
  - `trailing_stop_positive_offset_p1`: da 0.01 a 0.05
- Utilizza `ConservativeCalmarLoss` come loss function personalizzata
- `buy_rsi`: IntParameter(20, 45, default=35)
- `sell_rsi`: IntParameter(60, 85, default=70)
- `stoploss`: -0.05

**Perché restringere lo spazio**: senza questa restrizione, Freqtrade cerca stoploss fino a -35% e trailing fino a 35%, producendo configurazioni con drawdown del 78% inaccettabili per un capitale di 1000€.

---

### 4. `EmaRsiTrendStrategyHyperoptV3` (V3 — Split ADX)

**File**: `user_data/strategies/ema_rsi_trend_strategy_hyperopt_v3.py`

Versione più avanzata con **ingresso differenziato basato su ADX** (Average Directional Index).

**Logica di ingresso a due livelli**:
1. **`trend_pullback`**: RSI < 31 + ADX ≤ breakout_adx → uscita rapida su RSI ipercomprato
2. **`trend_breakout`**: RSI < 31 + ADX > breakout_adx → uscita lunga su inversione trend (EMA50 < EMA200)

**Filosofia**: quando RSI segnala un pullback e ADX è alto, il mercato è in un trend molto forte — il trade resta aperto più a lungo per catturare il rally. Se ADX è basso, è un semplice pullback con uscita rapida.

**Parametri aggiuntivi**:
- `breakout_adx`: `IntParameter(10, 40, default=15, space="buy", optimize=True)`
- `max_open_trades`: 4
- `leverage`: 3.0 (futures)
- `minimal_roi`: `{"0": 0.08, "60": 0.04, "180": 0.02, "720": 0.01}`
- `stoploss`: -0.034
- `trailing_stop_positive`: 0.017

---

### Confronto tra le Versioni

| Caratteristica | V1 Base | V2 Hyperopt | V2.1 Conservativa | V3 Split ADX |
|---|---|---|---|---|
| **RSI Ingresso** | Fisso (<30) | Ottimizzabile (20-45) | Ottimizzabile (20-45) | Ottimizzabile (20-45) |
| **RSI Uscita** | Fisso (>75) | Ottimizzabile (60-85) | Ottimizzabile (60-85) | Ottimizzabile (60-85) |
| **ADX** | No | No | No | Sì (10-40) |
| **Exit Tag** | `overbought` | `trend_exhausted` | `trend_exhausted` | `trend_pullback` / `trend_breakout` |
| **Leverage** | 1x | 1x | 1x | 3x (futures) |
| **Stoploss** | -3% | -4.1% | -5% (ricercabile -10%/-2%) | -3.4% |
| **Max Drawdown** | 3.52% | ~78% (senza restrizioni) | Conservativo | TBD |
| **Uso** | Studio base | Ottimizzazione | Ottimizzazione sicura | Futures avanzato |

---

## 🔧 Strumenti e Script Utilità

### `analizza_hyperopt.py`

**Scopo**: Legge automaticamente **tutti** i file `.fthypt` nella cartella `user_data/hyperopt_results/` e ne estrae parametri e metriche in forma tabellare.

**Metodo**: Utilizza il comando CLI `freqtrade hyperopt-show --best --print-json` anziché leggere direttamente il formato binario `.fthypt`, che non è JSON puro e usa encoding speciale per NaN.

**Output**:
- Tabella riassuntiva stampata a schermo
- `hyperopt_summary.csv` — CSV importabile in Excel
- `hyperopt_results_raw/*.json` — JSON grezzi per controllo manuale

**Uso**:
```bash
python analizza_hyperopt.py --config user_data/config.json --results-dir user_data/hyperopt_results
```

**Robustezza**: gestisce errori con gracefully — se un file è corrotto o un campo manca, scrive "n/d" invece di bloccarsi.

### `verifica_drawdown_fix.py`

**Scopo**: Verifica la correttezza del calcolo del max drawdown confrontando i risultati del backtest con il calcolo manuale tramite `freqtrade.data.metrics.calculate_max_drawdown`.

**Metodo**: Estrae i dati dal file zip del backtest, converte i trade in un DataFrame pandas, e confronta il drawdown calcolato da Freqtrade con quello riferito nel report.

### `create_futures_config.py` / `create_futures_config2.py`

**Scopo**: Generano automaticamente configurazioni per futures a partire da `config.json`, modificando:
- `trading_mode`: "spot" → "futures"
- `defaultType`: "spot" → "future"
- Coppie: EUR → USDT (config2)
- Leverage: 3x per BTC/EUR, ETH/EUR, SOL/EUR (config) o BTC/USDT, ETH/USDT, SOL/USDT (config2)

### `fix_config.py` / `revert_config.py`

**Scopo**: Utility per modificare rapidamente il `config.json`:
- `fix_config.py`: rimuove `margin_mode: "cross"`
- `revert_config.py`: riporta `trading_mode` a "spot"

---

## ⚙️ Configurazioni

### `config.json` (Spot — Produzione / Dry-run)

**File**: `user_data/config.json`

Configurazione principale con le seguenti impostazioni:

```json
{
  "max_open_trades": 4,          // 4 posizioni simultanee (~250€ a trade su 1000€)
  "stake_currency": "EUR",       // Valuta di riferimento
  "stake_amount": "unlimited",   // Divide equamente il capitale tra le operazioni
  "tradable_balance_ratio": 0.95, // 95% del capitale, 5% riserva per commissioni
  "dry_run": true,               // SIMULAZIONE ATTIVA (nessun soldo reale)
  "dry_run_wallet": 1000,        // Wallet virtuale da 1000€
  "fiat_display_currency": "EUR",
  "exchange": {
    "name": "binance",
    "key": "",                   // VA COMPILATO SOLO IN PRODUZIONE
    "secret": "",                // VA COMPILATO SOLO IN PRODUZIONE
    "ccxt_config": {"options": {"defaultType": "spot"}},
    "pair_whitelist": ["BTC/EUR", "ETH/EUR", "SOL/EUR"]
  },
  "telegram": {
    "enabled": false,            // Notifiche Telegram disattivate
    "token": "",
    "chat_id": ""
  },
  "api_server": {
    "enabled": true,
    "listen_ip_address": "127.0.0.1",
    "listen_port": 8080,
    "username": "freqtrade",
    "password": "freqtrade"      // Cambiare in produzione!
  },
  "bot_name": "bot_1000eur_test",
  "initial_state": "running",
  "force_entry_enable": false    // Impedisce ingressi manuali accidentali
}
```

### `config_futures.json` / `config_futures_test.json` (Futures)

Configurazioni derivate per trading su futures con:
- `trading_mode`: "futures"
- `defaultType`: "future"
- Leverage 3x
- Coppie USDT o EUR a seconda della versione

---

## 📊 Risultati Backtest e Hyperopt

### Risultati Backtest (Strategia Base V1)

**Periodo**: 2023-01-09 → 2024-01-10

| Metrica | Valore |
|---------|--------|
| Trade totali | 74 |
| Win Rate | 73% (54W / 20L) |
| Profitto totale | +8.079 EUR (+0.81%) |
| Max Drawdown | 3.52% |
| Sharpe Ratio | 0.07 |
| Sortino Ratio | 0.10 |
| Profit Factor | 1.05 |
| Best Pair | SOL/EUR (+5.06%) |
| Worst Pair | BTC/EUR (-2.53%) |

**Analisi**: La strategia ha un **win rate elevato (73%)** ma un **profitto totale molto modesto (+0.81%)** su un anno. Questo indica che le vincite sono piccole e frequenti, mentre le perdite sono rare ma più pesanti. Il Profit Factor di 1.05 è appena sopra la parità — la strategia è fragile e richiede ottimizzazione prima di qualsiasi utilizzo con soldi reali.

### Risultati Hyperopt

**File di risultati**: 11 file `.fthypt` in `user_data/hyperopt_results/`

I file `.fthypt` sono stati generati con diverse configurazioni di hyperopt e coprono sia la strategia base che la V2. I risultati grezzi sono disponibili in `user_data/hyperopt_results_raw/` in formato JSON per analisi approfondita.

### Confronti con NostalgiaForInfinity

Il progetto include file di confronto con la strategia community [NostalgiaForInfinity](https://github.com/iterativv/NostalgiaForInfinity):
- `nfix6-profit_max-bot_1000eur_test-binance-EUR-(backtest).json`
- `nfix6-profit_max-bot_1000eur_test-binance-USDT-(backtest).json`

Questi file permettono di confrontare le performance della strategia EmaRsiTrendStrategy con la popolare strategia community sullo stesso capitale (1000€) e le stesse coppie.

### Log di Backtest Dettagliati

La cartella `user_data/backtest_results/` contiene decine di log in formato `.txt` e `.meta.json` per ogni esecuzione di backtest, permettendo di tracciare l'evoluzione dei parametri e dei risultati nel tempo.

---

## 📡 Comandi Utili

### Backtest
```bash
cd C:\Users\PC\Desktop\Freqtrade_Project
freqtrade backtesting --strategy EmaRsiTrendStrategy --timerange 20230101-20240110 --breakdown month -c user_data\config.json
```

### Hyperopt (Ottimizzazione)
```bash
# Strategia base
freqtrade hyperopt --strategy EmaRsiTrendStrategy --hyperopt-loss CalmarHyperOptLoss --spaces buy sell roi stoploss trailing --epochs 300 --timerange 20220101-20240101 -c user_data\config.json

# Strategia V2 con loss conservativa
freqtrade hyperopt --strategy EmaRsiTrendStrategyHyperoptV2 --hyperopt-loss ConservativeCalmarLoss --spaces buy sell roi stoploss trailing --epochs 300 --timerange 20220101-20240101 -c user_data\config.json

# Strategia V3 con ADX
freqtrade hyperopt --strategy EmaRsiTrendStrategyHyperoptV3 --hyperopt-loss CalmarHyperOptLoss --spaces buy sell roi stoploss trailing --epochs 300 --timerange 20220101-20240101 -c user_data\config.json
```

### Dry-run (Simulazione)
```bash
freqtrade trade -c user_data\config.json --dry-run --strategy EmaRsiTrendStrategy
```

### Scaricare Dati Storici
```bash
freqtrade download-data --exchange binance --pairs BTC/EUR ETH/EUR SOL/EUR -t 1h --timerange 20230101-20240110 -c user_data\config.json
```

### Analisi Risultati Hyperopt
```bash
python analizza_hyperopt.py
```

### Avvio Rapido (Dry-run)
```bash
cd C:\Users\PC\Desktop\Freqtrade_Project
python -m freqtrade trade -c user_data\config.json --dry-run --strategy EmaRsiTrendStrategy
```

---

## 🛡️ Protezioni e Risk Management

Tutte le strategie implementano un sistema di **protezioni integrate** di Freqtrade:

```python
@property
def protections(self):
    return [
        # 1. Cooldown: 4 candele di pausa dopo un trade
        {"method": "CooldownPeriod", "stop_duration_candles": 4},
        
        # 2. MaxDrawdown: pausa di 12 candele dopo 20 trade 
        #    se il drawdown supera il 15% in 48 candele
        {
            "method": "MaxDrawdown",
            "lookback_period_candles": 48,
            "trade_limit": 20,
            "stop_duration_candles": 12,
            "max_allowed_drawdown": 0.15,
        },
        
        # 3. StoplossGuard: pausa di 12 candele per coppia dopo 
        #    3 trade consecutivi in stop loss nelle ultime 24 candele
        {
            "method": "StoplossGuard",
            "lookback_period_candles": 24,
            "trade_limit": 3,
            "stop_duration_candles": 12,
            "only_per_pair": True,
        },
    ]
```

### Significato delle Protezioni

1. **CooldownPeriod**: evita di aprire troppi trade in rapida successione, dando respiro al mercato.
2. **MaxDrawdown**: se la strategia sta perdendo troppo (15% in 48 candele con 20+ trade), mette in pausa per 12 candele per evitare ulteriori danni.
3. **StoplossGuard**: se una coppia specifica causa 3 stop loss consecutivi in 24 candele, mette in pausa quella coppia specifica per 12 candele.

---

## 🔮 Prossimi Passi Consigliati

1. **Dry-run prolungato**: eseguire `freqtrade trade -c user_data\config.json --dry-run --strategy EmaRsiTrendStrategy` per almeno 1-2 settimane e raccogliere dati reali di mercato
2. **Creare chiavi API su Binance**: [api.binance.com](https://api.binance.com) → API Keys → solo **Read/Write** (MAI abilitare withdrawal)
3. **Aggiornare config.json**: inserire API key e secret nel file `secrets.json` separato (Mai nel config.json)
4. **Validazione out-of-sample**: testare i parametri ottimizzati su un periodo che l'hyperopt NON ha mai visto
5. **Passare a trading reale**: impostare `"dry_run": false` in config.json SOLO dopo settimane di dry-run pulito
6. **Confronto definitivo**: confrontare EmaRsiTrendStrategy con NostalgiaForInfinity sugli STESSI dati e periodo
7. **Monitoraggio continuo**: usare l'API server (porta 8080) o Telegram per monitorare il bot

---

## ⚠️ Note Importanti

- **dry_run è su `true`** nel `config.json` — nessun soldo reale è coinvolto nel funzionamento attuale
- **Le API keys sono vuote** — non inserire mai chiavi API nel config.json; usa `secrets.json` separato
- **La strategia base ha dati molto conservativi** (+0.81% su 1 anno, Profit Factor 1.05) — non è pronta per trading reale senza ottimizzazione
- **L'iperopt senza restrizioni può portare a overfitting severo** — i risultati del 78% di drawdown nella V2 dimostrano quanto sia importante restringere lo spazio di ricerca
- **⚠️ NON è consulenza finanziaria** — il trading di criptovalute, specialmente con capitale piccolo e leverage, comporta il rischio concreto e totale di perdere tutto il capitale investito
- **I file `.fthypt`, `.feather`, `.sqlite`, `.zip` e `.pkl` sono esclusi dal versionamento** tramite `.gitignore` perché troppo pesanti per il repository e/o contengono dati che possono essere rigenerati

---

## 📜 Licenza

Questo progetto è fornito **così com'è**, senza alcuna garanzia. L'autore declina ogni responsabilità per eventuali perdite finanziarie derivanti dall'uso di questo software.

**Il trading comporta rischi concreti di perdita del capitale. Usa questo software solo con capitale che puoi permetterti di perdere interamente.**

---

## 🔗 Riferimenti Esterni

- [Freqtrade Documentation](https://www.freqtrade.io/en/stable/)
- [Freqtrade Installation](https://www.freqtrade.io/en/stable/installation/)
- [NostalgiaForInfinity Strategy](https://github.com/iterativv/NostalgiaForInfinity)
- [Binance API](https://api.binance.com)
- [Git LFS (per file grandi)](https://git-lfs.github.com/)
