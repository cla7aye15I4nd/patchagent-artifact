import os
import re
import sys
import json
import time
import subprocess
from typing import Union

from nvwa.logger import log
from nvwa.sky.task import PatchTask, skyset_tools
from nvwa.lsp.language import LanguageType, LanguageServer
from nvwa.parser.sanitizer import Sanitizer


class ClangdServer(LanguageServer):
    def __init__(self, task: PatchTask):
        super().__init__(task)

        self.build_dir = self._compile()
        self._start()

    @classmethod
    def supported_languages(cls) -> list[LanguageType]:
        return [LanguageType.C]

    def _compile(self):
        build_dir = skyset_tools.get_sanitizer_build_path(self.project, self.tag, Sanitizer.BearSanitizer)
        compile_commands_log = os.path.join(build_dir, "compile_commands.log")
        compile_commands_json = os.path.join(build_dir, "compile_commands.json")

        if not os.path.exists(compile_commands_json):
            log.info(f"Compiling {self.project} {self.tag} with BearSanitizer")
            skyset_tools.build(
                self.project,
                self.tag,
                sanitizer="BearSanitizer",
            )

            compile_commands_list = []
            if os.path.exists(compile_commands_json):
                return build_dir
            else:
                with open(compile_commands_log, "r") as f:
                    compile_commands_list = [json.loads(line.strip()) for line in f.readlines() if line.startswith("{")]
                with open(compile_commands_json, "w") as f:
                    json.dump(compile_commands_list, f, indent=4)

        return build_dir

    def _start(self):
        self.proc = subprocess.Popen(
            ["clangd", "--clang-tidy", f"--compile-commands-dir={self.build_dir}", "--log=error"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=1,
            universal_newlines=True,
        )

        self.send_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "processId": None,
                    "rootPath": None,
                    "rootUri": f"file://{self.build_dir}",
                    "capabilities": {},
                    "trace": "off",
                    "workspaceFolders": None,
                },
            }
        )
        self.send_request({"jsonrpc": "2.0", "method": "initialized", "params": {}})

    def stop(self):
        time.sleep(1)
        assert self.proc is not None
        self.send_request({"jsonrpc": "2.0", "method": "shutdown", "params": {}})
        self.send_request({"jsonrpc": "2.0", "method": "exit", "params": {}})
        self.proc.terminate()
        try:
            self.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.proc.kill()

        if hasattr(self.proc.stdin, 'close'):
            self.proc.stdin.close() # type: ignore
        if hasattr(self.proc.stdout, 'close'):
            self.proc.stdout.close() # type: ignore
        if hasattr(self.proc.stderr, 'close'):
            self.proc.stderr.close() # type: ignore

        self.proc = None
    
    def send_request(self, message):
        message_json = json.dumps(message)
        message_bytes = message_json.encode()
        content_length = len(message_bytes)
        full_message = f"Content-Length: {content_length}\r\n\r\n{message_json}"

        self.proc.stdin.write(full_message)  # type: ignore
        self.proc.stdin.flush()  # type: ignore

    def _find_definition(self, path: str, line: int, chr: int) -> Union[list[str], None]:
        with open(path, "r") as f:
            content = f.read()

        self.send_request(
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": f"file://{path}",
                        "languageId": "c",
                        "version": 1,
                        "text": content,
                    }
                },
            }
        )
        self.send_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "textDocument/definition",
                "params": {
                    "textDocument": {
                        "uri": f"file://{path}",
                    },
                    "position": {
                        "line": line,
                        "character": chr,
                    },
                },
            }
        )

        results = self.read_response()

        if results is None:
            return None

        locations = []
        for result in results:
            prefix = f"file://{self.build_dir}/"
            path_ = result["uri"]
            if path_.startswith(prefix):
                path_ = path_[len(prefix) :]
            else:
                path_ = path_.replace("file://", "")
                log.warning(f"Trying to locate symbol in {path_}")
            line_ = result["range"]["start"]["line"] + 1
            chr_ = result["range"]["start"]["character"] + 1
            locations.append(f"{path_}:{line_}:{chr_}")

        return locations

    def _hover(self, path: str, line: int, chr: int) -> Union[str, None]:
        with open(path, "r") as f:
            content = f.read()

        self.send_request(
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": f"file://{path}",
                        "languageId": "c",
                        "version": 1,
                        "text": content,
                    }
                },
            }
        )
        self.send_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "textDocument/hover",
                "params": {
                    "textDocument": {
                        "uri": f"file://{path}",
                    },
                    "position": {
                        "line": line,
                        "character": chr,
                    },
                },
            }
        )

        results = self.read_response()
        if results is None or results['contents']['value'] is None:
            return ""

        return results["contents"]["value"]

    def find_definition(self, path: str, line: int, chr: int) -> list[str]:
        filepath = os.path.join(self.build_dir, path)
        log.info(f"Finding definition for {filepath}:{line}:{chr}")
        line, chr = line - 1, chr - 1

        while True:
            locations = self._find_definition(filepath, line, chr)
            if locations is not None:
                return locations
            self.stop()
            self._start()

    def hover(self, path: str, line: int, chr: int) -> str:
        filepath = os.path.join(self.build_dir, path)
        log.info(f"Get hint for {filepath}:{line}:{chr}")  # hover
        line, chr = line - 1, chr - 1

        while True:
            hint = self._hover(filepath, line, chr)
            if hint is not None:
                return hint
            self.stop()
            self._start()

    def read_response(self):
        output_buffer = ""
        while True:
            data = self.proc.stdout.read(1)  # type: ignore
            if not data:
                log.error("No data from clangd")
                break
            output_buffer += data

            while True:
                try:
                    response = json.loads(output_buffer)
                    if response.get("method") != None or response.get("id") != 2:
                        output_buffer = ""
                        break
                    else:
                        return response["result"]
                except json.JSONDecodeError as e:
                    try:
                        start = output_buffer.index("{")
                        end = output_buffer.rindex("}") + 1
                        response = json.loads(output_buffer[start:end])
                        if response.get("method") != None or response.get("id") != 2:
                            output_buffer = ""
                            break
                        else:
                            return response["result"]
                    except (ValueError, json.JSONDecodeError):
                        break
