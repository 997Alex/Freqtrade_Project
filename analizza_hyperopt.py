#!/usr/bin/env python3
"""
analizza_hyperopt.py
=====================
Legge automaticamente TUTTI i file di risultati hyperopt presenti in
user_data/hyperopt_results/ (uno per ogni run che hai lanciato) ed
estrae, per ciascuno, i parametri scelti dal miglior epoch e le
metriche principali (profitto, drawdown, numero di trade).

PERCHE' QUESTO SCRIPT NON LEGGE DIRETTAMENTE I FILE .fthypt
--------------------------------------------------------------
I file .fthypt non sono JSON puro: usano un formato interno (rapidjson
con encoding speciale per NaN) che puo' anche cambiare tra versioni di
Freqtrade. Il modo robusto e supportato per leggerli e' chiedere a
Freqtrade stesso di farlo, tramite il comando CLI:

    freqtrade hyperopt-show --best -n -1 --print-json --no-header

Questo script automatizza quella chiamata per ogni file trovato nella
cartella, invece di farla a mano una alla volta, e mette tutto insieme
in una tabella + un CSV apribile in Excel.

USO
---
Lancialo dalla cartella del progetto (dove sta la sotto-cartella user_data):

    python analizza_hyperopt.py

Parametri opzionali:

    python analizza_hyperopt.py --config user_data\\config.json --results-dir user_data\\hyperopt_results

OUTPUT
------
- Tabella riassuntiva stampata a schermo
- hyperopt_summary.csv nella cartella corrente
- hyperopt_results_raw/<nome_file>.json — il JSON completo restituito da
  Freqtrade per ogni run, per controllare a mano se qualche campo non
  fosse stato estratto correttamente (lo script e' scritto in modo
  difensivo: se non trova un campo atteso scrive "n/d" invece di
  bloccarsi, cosi' puoi comunque vedere tutto il resto).
"""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


def find_hyperopt_files(results_dir: Path):
    return sorted(results_dir.glob("*.fthypt"))


def run_hyperopt_show(config_path: Path, filename: str):
    """
    Chiama 'freqtrade hyperopt-show' sul file specificato e ne parsa
    l'output JSON. Ritorna None (invece di interrompere tutto lo script)
    se qualcosa va storto, cosi' un run rotto non blocca l'analisi degli
    altri.
    """
    cmd = [
        sys.executable, "-m", "freqtrade", "hyperopt-show",
        "-c", str(config_path),
        "--hyperopt-filename", filename,
        "--best", "-n", "-1",
        "--print-json",
        "--no-header",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        print(f"  [ERRORE] Timeout leggendo {filename}")
        return None
    except FileNotFoundError:
        print("  [ERRORE] Non trovo il modulo freqtrade. Lancia questo script "
              "dallo stesso ambiente Python/venv dove hai installato Freqtrade.")
        return None

    if result.returncode != 0:
        print(f"  [ERRORE] Freqtrade ha restituito un errore per {filename}:")
        snippet = result.stderr.strip()[:500]
        print("  " + snippet.replace("\n", "\n  "))
        return None

    stdout = result.stdout.strip()
    candidates = [i for i in (stdout.find("{"), stdout.find("[")) if i != -1]
    if not candidates:
        print(f"  [ERRORE] Nessun JSON trovato nell'output per {filename}")
        print("  Output grezzo:", stdout[:300])
        return None

    try:
        data = json.loads(stdout[min(candidates):])
    except json.JSONDecodeError as e:
        print(f"  [ERRORE] JSON non valido per {filename}: {e}")
        return None

    # Aggiungi le metriche dal testo dell'output (JSON non le contiene)
    metrics = parse_metrics_from_text(result.stdout)
    data["results_metrics"] = metrics

    return data


def parse_metrics_from_text(output: str) -> dict:
    """
    Parsa le metriche dal testo dell'output di hyperopt-show.
    Restituisce un dizionario con trade_count, profit_total_pct, max_drawdown_pct.
    """
    metrics = {}
    try:
        for line in output.split("\n"):
            if "Total/Daily Avg Trades" in line:
                val = line.split("|")[-2].strip().split()[0]
                metrics["trade_count"] = int(float(val))
            elif "Total profit %" in line:
                val = line.split("|")[-2].strip().replace("%", "")
                metrics["profit_total_pct"] = float(val)
            elif "Absolute drawdown" in line and "EUR" in line:
                val = line.split("|")[-2].strip().split()[0]
                metrics["max_drawdown_pct"] = float(val)
    except (ValueError, IndexError):
        pass
    return metrics


def extract_row(filename: str, data) -> dict:
    """
    Estrae in modo difensivo i campi che interessano. Non assume nomi
    di campo fissi per i parametri (dipendono da cosa hai ottimizzato,
    es. buy_rsi/sell_rsi oggi, magari altri domani) — li include TUTTI
    dinamicamente con prefisso 'param_'.
    """
    if isinstance(data, list):
        data = data[0] if data else {}

    params = data.get("params", {}) or {}
    metrics = data.get("results_metrics", {}) or {}

    row = {"file": filename, "loss": data.get("loss", "n/d")}

    metric_aliases = {
        "trade_count": ["trade_count", "total_trades"],
        "profit_total_pct": [
            "profit_total_pct", "total_profit_pct", "profit_total_pct_relative"
        ],
        "max_drawdown_pct": [
            "max_drawdown_account", "max_drawdown", "max_drawdown_abs"
        ],
    }
    for out_key, candidates in metric_aliases.items():
        row[out_key] = next((metrics[k] for k in candidates if k in metrics), "n/d")

    for k, v in params.items():
        row[f"param_{k}"] = v

    return row


def main():
    parser = argparse.ArgumentParser(
        description="Estrae parametri e metriche da tutti i run hyperopt salvati."
    )
    parser.add_argument("--config", default="user_data/config.json")
    parser.add_argument("--results-dir", default="user_data/hyperopt_results")
    args = parser.parse_args()

    config_path = Path(args.config)
    results_dir = Path(args.results_dir)

    if not results_dir.exists():
        print(f"Cartella non trovata: {results_dir}")
        sys.exit(1)

    files = find_hyperopt_files(results_dir)
    if not files:
        print(f"Nessun file .fthypt trovato in {results_dir}")
        sys.exit(0)

    print(f"Trovati {len(files)} file di risultati hyperopt. Analizzo...\n")

    debug_dir = Path("hyperopt_results_raw")
    debug_dir.mkdir(exist_ok=True)

    rows = []
    for f in files:
        print(f"-> {f.name}")
        data = run_hyperopt_show(config_path, f.name)
        if data is None:
            continue
        (debug_dir / f"{f.stem}.json").write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )
        rows.append(extract_row(f.name, data))

    if not rows:
        print("\nNessun risultato leggibile. Controlla gli errori sopra.")
        sys.exit(1)

    # Unione di tutte le colonne apparse in qualunque riga (run diversi
    # possono avere ottimizzato parametri diversi tra loro).
    fixed_cols = ["file", "loss", "trade_count", "profit_total_pct", "max_drawdown_pct"]
    param_cols = sorted({k for r in rows for k in r if k.startswith("param_")})
    headers = fixed_cols + param_cols
    for r in rows:
        for h in headers:
            r.setdefault(h, "n/d")

    widths = {h: max(len(h), max(len(str(r[h])) for r in rows)) for h in headers}
    print("\n" + " | ".join(h.ljust(widths[h]) for h in headers))
    print("-+-".join("-" * widths[h] for h in headers))
    for r in rows:
        print(" | ".join(str(r[h]).ljust(widths[h]) for h in headers))

    out_csv = Path("hyperopt_summary.csv")
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSalvato: {out_csv.resolve()}")
    print(f"JSON grezzi per controllo manuale in: {debug_dir.resolve()}")


if __name__ == "__main__":
    main()
