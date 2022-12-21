from __future__ import annotations

import io
import sys
from typing import Collection, TextIO

from .tokenizer import Tokenizer
from .errors import SpspEvaluationError, SpspSyntaxError
from .evaluation import evaluate
from .parser import parse
from .scope import Scope
from .special_symbols import SpecialSymbols


def read_line() -> str:
    prompt = '>>> '
    result = ''

    while True:
        line = input(prompt)

        if (pos := line.find(SpecialSymbols.Semicolon)) >= 0:
            line = line[:pos]

        result += line + '\n'

        if result.count(SpecialSymbols.LeftParenthesis) <= result.count(SpecialSymbols.RightParenthesis) \
                and result.count(SpecialSymbols.LeftSquareBracket) <= result.count(SpecialSymbols.RightSquareBracket):
            return result

        prompt = '... '


def find_line(input_stream: TextIO, position: int) -> (str, int, int):
    initial_pos = input_stream.tell()

    read = 0
    line_no = 1

    line = ''
    line_start = None
    for line in input_stream:
        read += len(line)

        if read > position:
            line_start = read - len(line)
            break

        line_no += 1

    if line_start is None:
        line_no -= 1
        line_start = read - len(line)

    position_in_line = position - line_start
    line = line.rstrip()

    line = line.replace('\t', ' ')

    input_stream.seek(initial_pos)

    return line, line_no, position_in_line


def print_error_message(
        input_stream: TextIO,
        file_name: str,
        error: SpspEvaluationError | SpspSyntaxError,
        stream: TextIO = sys.stderr
) -> None:
    sys.stdout.flush()
    initial_pos = input_stream.tell()
    input_stream.seek(0)

    line, line_number, position_in_line = find_line(input_stream, error.position)

    if isinstance(error, SpspEvaluationError):
        error = error.cause

    print(f'File "{file_name}", line {line_number}', file=stream)
    print(line, file=stream)
    print(' ' * position_in_line + '^', file=stream)
    print(f'{type(error).__name__}: {error}', file=stream)

    input_stream.seek(initial_pos)


def run_repl(scope: Scope) -> None:
    while True:
        with io.StringIO(read_line()) as input_stream:
            try:
                for expression in parse(Tokenizer(input_stream)):
                    print(evaluate(expression, scope))
            except (SpspEvaluationError, SpspSyntaxError) as e:
                print_error_message(input_stream, '<stdin>', e, stream=sys.stdout)


def run_files(file_names: Collection[str], scope: Scope) -> bool:
    for file_name in file_names:
        with open(file_name, mode='rt', encoding='utf-8') as file:
            try:
                for expression in parse(Tokenizer(file)):
                    evaluate(expression, scope)
            except (SpspEvaluationError, SpspSyntaxError) as e:
                print_error_message(file, file_name, e)
                return False
    return True


def _main(args: list[str]) -> None:
    scope = Scope.empty()
    if len(args) <= 1:
        return run_repl(scope)

    if args[-1] != '--repl':
        run_files(args[1:], scope)
        return

    if not run_files(args[1:-1], scope):
        return
    return run_repl(scope)


_main(sys.argv)
