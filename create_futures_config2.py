import json

with open('user_data/config.json', 'r') as f:
    content = f.read()

# Create futures config with USDT pairs
content = content.replace('"trading_mode": "spot"', '"trading_mode": "futures"')
content = content.replace('"defaultType": "spot"', '"defaultType": "future"')

# Replace pairs with USDT versions
content = content.replace('"BTC/EUR"', '"BTC/USDT"')
content = content.replace('"ETH/EUR"', '"ETH/USDT"')
content = content.replace('"SOL/EUR"', '"SOL/USDT"')

# Add leverage
content = content.replace(
    '"force_entry_enable": false',
    '"force_entry_enable": false,\n   "leverage": {"BTC/USDT": 3, "ETH/USDT": 3, "SOL/USDT": 3}'
)

with open('user_data/config_futures.json', 'w') as f:
    f.write(content)
print('Created config_futures.json with USDT pairs')
