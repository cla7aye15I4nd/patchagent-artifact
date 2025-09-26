import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from nvwa.sky.utils import get_all_task
from nvwa.logger import log
from nvwa.context import Context
from nvwa.proxy import internal
from nvwa.proxy.utils import extract_cpp_function_name


class TestLocate(unittest.TestCase):
    def test_locate(self):
        for task in get_all_task():
            context = Context(task)
            report = task.sanitizer_report
            assert report is not None
            for stack in [report.stacktrace] + [v for k, v in report.additional_info.items() if "stack" in k]:
                for idx, frame in enumerate(stack):
                    if (sym := extract_cpp_function_name(frame[0])) is not None:
                        internal.locate(context, sym)


if __name__ == "__main__":
    unittest.main(verbosity=2)

# python3 -m unittest -v test.test_locate.TestLocate
