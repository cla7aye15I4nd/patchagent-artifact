import os
import sys
import json

base_dir = os.path.dirname(os.path.realpath(__file__))

for model in ['gpt-4o', 'gpt-4-turbo', 'claude-3-haiku', 'claude-3-sonnet', 'claude-3-opus', 'gpt-4o-mini']:
    base_path = os.path.join(base_dir, model)
    for file in os.listdir(base_path):
        with open(os.path.join(base_path, file)) as f:
            result = json.load(f)
            patched = any(item['patch'] is not None for item in result)
            if not patched:
                if len(result) != 15:
                    print(f'[*] {model}/{file} is not patched but have {len(result)} items')
                    
                if len(result) > 15 and '--repair' in sys.argv:
                    with open(os.path.join(base_path, file), 'w') as f:
                        json.dump(result[:15], f, indent=2)
            else:
                if len(result) > 15:
                    print(f'[*] {model}/{file} is patched but have {len(result)} items')

print('[*] Done checking')