import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from nvwa.sky.utils import get_all_task
from nvwa.parser.utils import parse
from nvwa.logger import log
from nvwa.proxy.utils import extract_cpp_function_name


class TestParser(unittest.TestCase):
    def perform_test(self, debug):
        """Test the parser functionality over all tasks."""
        for task in get_all_task(skip_setup=True):
            parsed_report = parse(task.report, task.sanitizer)
            self.assertIsNotNone(parsed_report, "Parsed report should not be None.")

            summary = parsed_report.summary  # type: ignore
            self.assertIsNotNone(summary, "Parsed report summary should not be None.")
            if debug:
                with open(os.path.join(task.path, "summary.txt"), "w") as f:
                    f.write(summary)

    def test_parser_without_debug(self):
        """Test the parser functionality over all tasks without debug information."""
        self.perform_test(debug=False)

    def test_parser_with_debug(self):
        """Test the parser functionality over all tasks with debug information."""
        self.perform_test(debug=True)
        
    def test_statistics(self):
        overlap, total = 0, 0
        for task in get_all_task(skip_setup=True):
            sanitizer_report = parse(task.report, task.sanitizer)
            assert sanitizer_report is not None
            patch_path = os.path.join(task.path, "patch.diff")
            if not os.path.exists(patch_path):
                continue
            with open(patch_path, 'rb') as f:
                patch = f.read()
            report_functions = [f for f, _ in sanitizer_report.stacktrace]
            for key, value in sanitizer_report.additional_info.items():
                if 'stack' in key:
                    report_functions.extend(f for f, _ in value)
            for f in report_functions:
                f = extract_cpp_function_name(f)
                if f is not None and f.encode() in patch:
                    overlap += 1
                    break
            else:
                log.warning(f"Task {task.project} {task.tag} does not have overlap.")
            total += 1
                
        log.info(f"Overlap: {overlap} / {total} ({overlap / total * 100:.2f}%)")


if __name__ == "__main__":
    unittest.main(verbosity=2)

# python3 -m unittest -v test.test_parser.TestParser.test_parser_without_debug
# python3 -m unittest -v test.test_parser.TestParser.test_parser_with_debug
# python3 -m unittest -v test.test_parser.TestParser.test_statistics
