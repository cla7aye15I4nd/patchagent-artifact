import os
import sys
import unittest
import warnings

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from nvwa.sky.utils import get_all_task
from nvwa.parser.utils import parse
from nvwa.lsp.clangd import ClangdServer
from nvwa.lsp.utils import get_language
from nvwa.logger import log


class TestClangd(unittest.TestCase):
    def test_clangd(self):
        for task in get_all_task(skip_setup=True):
            if get_language(task) not in ClangdServer.supported_languages():
                continue

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ResourceWarning)
                log.info(f"Locating symbols in {task.project} {task.tag}\r")
                clangd_server = ClangdServer(task)

            sanitizer_report = parse(task.report, task.sanitizer)
            assert sanitizer_report is not None

            for _, source in sanitizer_report.stacktrace:
                path, line, column = source.split(":")
                locations = clangd_server.find_definition(path.lstrip("/"), int(line), int(column))
                if len(locations) == 0:
                    log.error(f"Failed to locate symbol in {task.project} {task.tag}: {clangd_server.build_dir}{source}")
                elif len(locations) > 1:
                    log.info(f"Located multiple symbols in {task.project} {task.tag}: {clangd_server.build_dir}{source}")
                
                declaration = clangd_server.find_definition(path.lstrip("/"), int(line), int(column)) 
                if len(declaration) == 0:
                    log.error(f"Failed to get symbol declaration in {task.project} {task.tag}: {clangd_server.build_dir}{source}")
                elif len(declaration) > 1:
                    log.info(f"Located symbol declaration in {task.project} {task.tag}: {clangd_server.build_dir}{source}")
                            
            clangd_server.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)

# python3 -m unittest -v test.test_clangd.TestClangd
