from __future__ import annotations

import io
import sys
from typing import Collection

from . import Tokenizer
from .errors import SpspBaseError
from .evaluation import evaluate
from .parser import parse
from .scope import Scope
from .special_symbols import SpecialSymbols


def read_line() -> str:
    prompt = '>>> '
    result = ''
    while True:
        line = input(prompt).rstrip()
        result += line.strip(SpecialSymbols.Backslash)

        if not line.endswith(SpecialSymbols.Backslash):
            return result

        prompt = '... '


def run_repl() -> None:
    scope = Scope.empty()

    while True:
        with io.StringIO(read_line()) as input_stream:
            try:
                for expression in parse(Tokenizer(input_stream)):
                    print(evaluate(expression, scope))
            except SpspBaseError as e:
                print(f'{type(e).__name__}: {e}')


def run_files(file_names: Collection[str]) -> None:
    scope = Scope.empty()

    for file_name in file_names:
        with open(file_name, mode='rt', encoding='utf-8') as file:
            for expression in parse(Tokenizer(file)):
                evaluate(expression, scope)


def _main(args: Collection[str]) -> None:
    if len(args) <= 1:
        return run_repl()

    return run_files(args[1:])


_main(sys.argv)
