import zipfile, json
import pandas as pd
from freqtrade.data.metrics import calculate_max_drawdown

zip_path = 'user_data/backtest_results/backtest-result-2026-09-15_21-30-35.zip'
with zipfile.ZipFile(zip_path) as z:
    data = json.loads(z.read('backtest-result-2026-09-15_21-30-35.json'))

strategy_data = data['strategy']['EmaRsiTrendStrategyHyperoptV2']
trades_list = strategy_data['trades']

# Convert to DataFrame
df = pd.DataFrame(trades_list)
print(f"Trades: {len(df)} rows")
print(f"Columns: {list(df.columns)}")
print(f"\nHas profit_ratio: {'profit_ratio' in df.columns}")
print(f"Has profit_abs: {'profit_abs' in df.columns}")

# Backtest reported values
reported_dd = strategy_data.get('max_relative_drawdown')
print(f"\nReported max_relative_drawdown from backtest: {reported_dd}")
print(f"Reported starting_balance: {strategy_data.get('starting_balance')}")
print(f"Reported dry_run_wallet: {strategy_data.get('dry_run_wallet')}")
print(f"Reported final_balance: {strategy_data.get('final_balance')}")

# Test the drawdown calculation
print("\n--- Testing calculate_max_drawdown ---")

# Method 1: Without relative (simple)
try:
    max_dd1 = calculate_max_drawdown(df, value_col='profit_ratio')
    print(f"Method 1 (simple, profit_ratio): relative_account_drawdown = {max_dd1.relative_account_drawdown:.6f} ({max_dd1.relative_account_drawdown*100:.4f}%)")
except Exception as e:
    print(f"Method 1 failed: {e}")

# Method 2: Without relative, profit_abs
try:
    max_dd2 = calculate_max_drawdown(df, value_col='profit_abs')
    print(f"Method 2 (simple, profit_abs): relative_account_drawdown = {max_dd2.relative_account_drawdown:.6f} ({max_dd2.relative_account_drawdown*100:.4f}%)")
except Exception as e:
    print(f"Method 2 failed: {e}")

# Check if the drawdown matches
if 'max_dd1' in dir() and reported_dd:
    calc = max_dd1.relative_account_drawdown
    diff = abs(calc - reported_dd)
    print(f"\nDifference: {diff:.6f} ({diff*100:.4f}%)")
    if diff < 0.001:
        print("OK: il numero torna!")
    else:
        print("MISMATCH!")
