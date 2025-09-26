import os
import sys
import unittest
import warnings

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from nvwa.sky.utils import get_all_task
from nvwa.logger import log
from nvwa.context import Context, ContextManager
from nvwa.proxy import internal

openai_archive = os.path.join(os.path.dirname(__file__), "..", "archives", "openai")


class TestContext(unittest.TestCase):
    def test_context_locate(self):
        warnings.filterwarnings(action="ignore", category=ResourceWarning)

        for task in get_all_task():
            cm = ContextManager(task, load_context=True, path=openai_archive)
            for context in cm.contexts:
                fake_context = Context(task)
                for tool_call in context.tool_calls:
                    if tool_call["name"] == "locate":
                        internal.locate(fake_context, tool_call["args"]["symbol"], auto_hint=True)
                    fake_context.tool_calls.append(tool_call)

    def test_context_viewcode(self):
        warnings.filterwarnings(action="ignore", category=ResourceWarning)

        for task in get_all_task():
            cm = ContextManager(task, load_context=True, path=openai_archive)
            for context in cm.contexts:
                fake_context = Context(task)
                for tool_call in context.tool_calls:
                    if tool_call["name"] == "viewcode":
                        internal.viewcode(fake_context, tool_call["args"]["path"], tool_call["args"]["start_line"], tool_call["args"]["end_line"], auto_hint=True)
                    fake_context.tool_calls.append(tool_call)


if __name__ == "__main__":
    unittest.main(verbosity=2)

# python3 -m unittest -v test.test_context.TestContext.test_context_locate
# python3 -m unittest -v test.test_context.TestContext.test_context_viewcode
