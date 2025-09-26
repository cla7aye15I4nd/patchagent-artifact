import os
import json

base_dir = os.path.dirname(os.path.realpath(__file__))

use_after_free_cases = [
    '4f6d42a-invalid_free',
    '0b29a41-use_after_free',
    '4607052-double_free',
    '4925c40-use_after_free',
    '7e2cb01-use_after_free',
    '7e2e92f-use_after_free',
    'ebedc7a-use_after_free',
    '1c1f34f-heap_buffer_overflow',
    '74b08bf-heap_double_free',
    '82b9212-heap_use_after_free',
    'afcb483-heap_use_after_free',
    '491a3ac-heap_use_after_free',
    '052d534-slab_use_after_free',
    '1ec35ea-slab_use_after_free',
    '4e99b32-use_after_free',
    '5ad3cb0-slab_use_after_free',
    '664a393-use_after_free',
    '6e764bc-use_after_free',
    '6f51352-use_after_free',
    '7d2f353-slab_use_after_free',
    '805d849-slab_use_after_free',
    'a689b93-use_after_free',
    'a6afa41-slab_out_of_bounds',
    'ac309e7-use_after_free',
    'd1dc877-use_after_free',
    'd6d09a6-use_after_free',
    '458ce51-use_after_free',
    'b95c01a-use_after_free',
    'd9b4a0c-use_after_free',
    '42616e0-use_after_free',
    'e84a4e3-use_after_free',
    'f2295fa-use_after_free',
    '9d20cd5-invalid_free',
    '8aec568-use_after_free',
    'af5acf3-use_after_free',
    'b4168c9-use_after_free',
    'bf5bbf0-use_after_free',
    '7cfd367-use_after_free',
    '9650e3c-use_after_free',
    'cf780fd-use_after_free',
    'd17a7bd-use_after_free',
    'd22d160-use_after_free',
    '139076a-use_after_free',
]

for model in ["gpt-4o", "gpt-4-turbo", "claude-3-haiku", "claude-3-sonnet", "claude-3-opus", "gpt-4o-mini"]:
    base_path = os.path.join(base_dir, model)
    for file in os.listdir(base_path):
        if not any(tag in file for tag in use_after_free_cases):
            continue
        flag = False
        with open(os.path.join(base_path, file)) as f:
            result = json.load(f)
            for item in result:
                if item["patch"] is not None:
                    print(f"==================================================================================")
                    print(f"[!] {model}/{file} has a patch")
                    for line in item['patch'].splitlines():
                        if line.startswith("+"):
                            print(f'\033[92m{line}\033[0m')
                        elif line.startswith("-"):
                            print(f'\033[91m{line}\033[0m')
                        else:
                            print(line)
                    x = input("If you want to remove the patch [y/n]: ")
                    if x == "y":
                        item["patch"] = None
                        flag = True

        with open(os.path.join(base_path, file), 'w') as f:
            json.dump(result, f, indent=4)

print("[*] Done checking")
