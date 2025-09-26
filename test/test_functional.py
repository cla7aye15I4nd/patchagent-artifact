import os
import sys
import argparse
import tempfile

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from nvwa.sky.task import skyset_tools
from nvwa.sky.utils import get_all_task
from nvwa.logger import log
from nvwa.context import ContextManager

def test_patch(args):
    for task in get_all_task(skip_setup=True):
        if (args.project is not None and task.project != args.project) or (args.tag is not None and task.tag != args.tag):
            continue
        
        if args.test_origin or args.test_all:
            res = task.test_functional()
            if res['result'] != 'passed':
                log.error(f"{task.project} {task.tag} functional test failed")

        if args.test_patch or args.test_all:  
            patch_path = os.path.join(skyset_tools.get_sky_path(task.project, task.tag), "patch.diff")
            if not os.path.exists(patch_path):
                continue
            res = task.test_functional(patch_path=patch_path)
            if res['result'] != 'passed':
                log.error(f"{task.project} {task.tag} with ground truth patch functional test failed")

        if args.test_result or args.test_all:
            cm = ContextManager(task, load_context=True, path=args.path)
            if cm.patch is None:
                continue
            
            with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
                f.write(cm.patch)
            res = task.test_functional(patch_path=f.name)
            if res['result'] != 'passed':
                log.error(f"{task.project} {task.tag} with result patch functional test failed")
                log.purple(cm.patch)
            os.unlink(f.name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Functional Test")
    parser.add_argument("--project", type=str, help="project name")
    parser.add_argument("--tag", type=str, help="tag name")
    parser.add_argument("--path", type=str, help="result path", default=os.path.join(os.path.dirname(__file__), "..", "archives", "openai"))
    parser.add_argument("--test-origin", action="store_true")
    parser.add_argument("--test-patch", action="store_true")
    parser.add_argument("--test-result", action="store_true")
    parser.add_argument("--test-all", action="store_true")

    args = parser.parse_args()
    test_patch(args)

# python3 test/test_functional.py
