import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from nvwa.sky.utils import get_all_task
from nvwa.parser.utils import parse
from nvwa.proxy.utils import extract_cpp_function_name
from nvwa.lsp.ctags import CtagsServer
from nvwa.lsp.utils import get_language
from nvwa.logger import log


class TestCtag(unittest.TestCase):
    def test_ctag(self):
        for task in get_all_task(skip_setup=True):
            if get_language(task) not in CtagsServer.supported_languages():
                continue

            log.info(f"Locating symbols in {task.project} {task.tag}\r")
            ctags_server = CtagsServer(task)
            sanitizer_report = parse(task.report, task.sanitizer)
            assert sanitizer_report is not None

            for function, _ in sanitizer_report.stacktrace:
                exteacted = extract_cpp_function_name(function)
                if exteacted is not None:
                    lines = ctags_server.locate_symbol(exteacted)
                    if len(lines) == 0:
                        log.warning(f"Function {exteacted} not found.")
                    log.debug(f"Location of {exteacted}: ")
                    for line in lines:
                        log.debug(task.immutable_project_path + '/' + line)
            
            ctags_server.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)

# python3 -m unittest -v test.test_ctag.TestCtag
