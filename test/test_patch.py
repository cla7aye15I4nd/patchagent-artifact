import os
import sys
import unittest
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from nvwa.sky.utils import get_all_task
from nvwa.logger import log


class TestPatch(unittest.TestCase):
    def test_patch(self):
        fail_cases = []
        for task in get_all_task(skip_setup=True):
            try:
                patch_path = os.path.join(task.path, "patch.diff")
                ret, _ = task.build(patch_path=patch_path)
                assert ret is True, "Build should return True."

                _, report = task.test(patch=True)
                assert report == "", "Report should be empty."
            except AssertionError as e:
                fail_cases.append((task, e))
                log.error(f"Failed task: {task}")

        for task, e in fail_cases:
            log.error(f"Failed task: {task} {e}")

        self.assertEqual(len(fail_cases), 0, f"{len(fail_cases)} failed cases.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Patch")
    parser.add_argument("--project", type=str, help="project name")
    parser.add_argument("--tag", type=str, help="tag name")
    
    args = parser.parse_args()
    for task in get_all_task(skip_setup=True, project=args.project, tag=args.tag):
        try:
            patch_path = os.path.join(task.path, "patch.diff")
            ret, _ = task.build(patch_path=patch_path)
            assert ret is True, "Build should return True."

            _, report = task.test(patch=True)
            assert report == "", "Report should be empty."
        except AssertionError as e:
            log.error(f"Failed task: {task}")


# python3 -m unittest -v test.test_patch.TestPatch
# python3 test/test_patch.py --project extractfix-libjpeg-turbo