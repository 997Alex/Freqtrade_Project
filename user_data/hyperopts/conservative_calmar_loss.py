"""
ConservativeCalmarLoss — loss function hyperopt con due guardrail espliciti

Risolve i due problemi emersi dai 5 run precedenti:

1. CalmarHyperOptLoss trovava config con 1-2 trade in 2 anni: pochi trade
   = drawdown quasi zero = rapporto Calmar artificialmente ottimo.
   QUI: sotto MIN_TRADES, la config viene scartata con una penalita' crescente.

2. SortinoHyperOptLoss ha trovato +3.36% di profitto con il 78.5% di
   drawdown: il Sortino penalizza la volatilita' dei rendimenti negativi,
   non un singolo drawdown prolungato.
   QUI: scartiamo con penalita' pesante ogni config che superi
   MAX_DRAWDOWN_ALLOWED, indipendentemente da quanto e' alto il profitto.

CAMBIO IMPORTANTE rispetto alla versione precedente:
Non ricalcoliamo piu' il drawdown a mano con calculate_max_drawdown().
Dopo aver verificato che ne' value_col="profit_ratio" ne' relative=True
riproducevano il 6.34% mostrato dal backtest (entrambi davano 535.9%,
lo stesso numero sbagliato in entrambi i casi — segno che il problema
non era quale variante della funzione usare), leggiamo il drawdown
DIRETTAMENTE da backtest_stats: lo stesso dizionario da cui Freqtrade
genera la tabella "Drawdown 6.34%" del backtest. E' garantito essere
lo stesso numero, perche' e' letteralmente lo stesso numero.

DOVE METTERLO: user_data/hyperopts/conservative_calmar_loss.py

USO:
    freqtrade hyperopt --strategy EmaRsiTrendStrategyHyperoptV2 \
        --hyperopt-loss ConservativeCalmarLoss \
        --spaces buy sell roi stoploss trailing \
        --epochs 300 \
        --timerange 20220101-20240101 \
        -c user_data\\config.json

Le soglie sotto sono un punto di partenza, non "la" risposta giusta —
cambiale in base a quanto sei disposto a rischiare tu, con 1000€.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from pandas import DataFrame

from freqtrade.optimize.hyperopt import IHyperOptLoss

# ---- Soglie di rischio: modificale liberamente ----
MIN_TRADES = 20                 # sotto questa soglia, la config e' scartata
MAX_DRAWDOWN_ALLOWED = 0.20     # 20%: oltre questa soglia, penalita' pesante
BAD_LOSS = 100.0                # "voto pessimo", abbastanza alto da escludere l'epoch

# Possibili nomi della chiave del drawdown dentro backtest_stats, in ordine
# di probabilita'. Diverse versioni di Freqtrade usano nomi leggermente
# diversi: proviamo tutti prima di arrenderci.
DRAWDOWN_KEY_CANDIDATES = (
    "max_drawdown_account",
    "max_drawdown",
    "max_drawdown_abs",
    "max_relative_drawdown",
)

DEBUG_LOG = Path("hyperopt_debug_backtest_stats_keys.txt")


class ConservativeCalmarLoss(IHyperOptLoss):
    """
    loss = -(profitto_totale / max_drawdown), con due guardrail:
    - trade_count troppo basso -> penalita' crescente
    - max_drawdown (letto da backtest_stats, non ricalcolato) oltre
      soglia -> penalita' crescente
    (hyperopt minimizza: valori piu' bassi = risultato migliore)
    """

    @staticmethod
    def hyperopt_loss_function(
        results: DataFrame,
        trade_count: int,
        min_date: datetime,
        max_date: datetime,
        config: Dict = None,
        processed: Dict[str, DataFrame] = None,
        backtest_stats: Dict[str, Any] = None,
        *args,
        **kwargs,
    ) -> float:

        total_profit = results["profit_abs"].sum()
        starting_balance = (config or {}).get("dry_run_wallet") or 1000.0
        profit_pct = total_profit / starting_balance

        # Guardrail 1: troppo pochi trade per essere un campione affidabile.
        if trade_count < MIN_TRADES:
            return BAD_LOSS + (MIN_TRADES - trade_count) - profit_pct

        # --- Leggi il drawdown gia' calcolato da Freqtrade, non ricalcolarlo ---
        max_dd_rel = None
        source = backtest_stats or {}
        for key in DRAWDOWN_KEY_CANDIDATES:
            if key in source and source[key] is not None:
                max_dd_rel = abs(float(source[key]))
                break

        if max_dd_rel is None:
            # Nessuna delle chiavi previste esiste in questa versione di
            # Freqtrade: invece di indovinare ancora, logghiamo le chiavi
            # REALMENTE presenti cosi' la prossima correzione e' certa,
            # non un altro tentativo alla cieca.
            keys_found = sorted(source.keys()) if source else ["<backtest_stats e' None o vuoto>"]
            with open(DEBUG_LOG, "a", encoding="utf-8") as f:
                f.write(str(keys_found) + "\n")
            return BAD_LOSS  # penalizza finche' non troviamo la chiave giusta

        # Se per qualche motivo e' 0 esatto (mai capitato finora, ma meglio
        # essere difensivi), evita la divisione per zero.
        max_dd_rel = max(max_dd_rel, 0.0001)

        # Guardrail 2: drawdown oltre soglia. Il termine -profit_pct evita
        # che un epoch catastrofico sembri "il migliore tra gli scartati"
        # solo perche' il suo eccesso di drawdown e' marginalmente piu'
        # piccolo di un altro epoch vicino al pareggio.
        if max_dd_rel > MAX_DRAWDOWN_ALLOWED:
            eccesso = max_dd_rel - MAX_DRAWDOWN_ALLOWED
            return BAD_LOSS + eccesso * 100 - profit_pct

        calmar_like = total_profit / max_dd_rel

        return -calmar_like