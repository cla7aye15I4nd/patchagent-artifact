import os
import sys
import unittest
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from nvwa.sky.utils import get_all_task
from nvwa.parser.utils import parse
from nvwa.logger import log

## Unittests
class TestBuildAndTest(unittest.TestCase):
    def test_build_test_without_debug(self):
        """Test the build and test process over all tasks without debug information."""
        for task in get_all_task(skip_setup=True):
            ret, _ = task.build()
            self.assertTrue(ret, "Build should return True.")

            ret, report = task.test()
            self.assertTrue(ret, "Test should return True.")

            parsed_report = parse(report, task.sanitizer)
            self.assertIsNotNone(parsed_report, "Parsed report should not be None.")

            summary = parsed_report.summary  # type: ignore
            self.assertIsNotNone(summary, "Parsed report summary should not be None.")

if __name__ == "__main__":
    def do_test(task):
        try:
            ret, report = task.test()
            assert ret, "Test should return True."

            with open(os.path.join(task.path, "report.txt"), "w") as f:
                f.write(report)

            parsed_report = parse(report, task.sanitizer)
            assert parsed_report is not None, "Parsed report should not be None."
            summary = parsed_report.summary  # type: ignore
            assert summary is not None, "Parsed report summary should not be None."
            with open(os.path.join(task.path, "summary.txt"), "w") as f:
                f.write(summary)
        except Exception:
            return False
        return True
    
    parser = argparse.ArgumentParser(description="Test Build")
    parser.add_argument("--project", type=str, help="project name")
    parser.add_argument("--tag", type=str, help="tag name")
    
    args = parser.parse_args()
    
    fail_cases = []
    for task in get_all_task(skip_setup=True, project=args.project, tag=args.tag):
        if not do_test(task):
            ret, _ = task.build()
            # ret = True
            if not ret or not do_test(task):
                fail_cases.append(task)
                log.error(f"Failed task: {task}")
    

# python3 -m unittest -v test.test_build.TestBuildAndTest.test_build_test_without_debug
# python3 test/test_build.py --project extractfix-libjpeg-turbo
