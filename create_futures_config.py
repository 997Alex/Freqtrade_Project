import json

with open('user_data/config.json', 'r') as f:
    content = f.read()

# Replace to futures mode
content = content.replace('"trading_mode": "spot"', '"trading_mode": "futures"')
content = content.replace('"defaultType": "spot"', '"defaultType": "future"')

# Add leverage config
content = content.replace(
    '"force_entry_enable": false',
    '"force_entry_enable": false,\n   "leverage": {"BTC/EUR": 3, "ETH/EUR": 3, "SOL/EUR": 3}'
)

with open('user_data/config_futures_test.json', 'w') as f:
    f.write(content)
print('created config_futures_test.json')
