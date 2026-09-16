with open('user_data/config.json', 'r') as f:
    content = f.read()

# Remove margin_mode line if present
content = content.replace('   "margin_mode": "cross",\n', '')

with open('user_data/config.json', 'w') as f:
    f.write(content)
print('Config cleaned up')
