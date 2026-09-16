import json

with open('user_data/config.json', 'r') as f:
    content = f.read()

# Remove any futures-related changes
content = content.replace('"trading_mode": "futures"', '"trading_mode": "spot"')

with open('user_data/config.json', 'w') as f:
    f.write(content)
print('Reverted to spot mode')
