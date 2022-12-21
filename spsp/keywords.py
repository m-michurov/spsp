from enum import Enum

__all__ = [
    'Keyword'
]


class Keyword(str, Enum):
    NoneLiteral = 'None'

    TrueLiteral = 'True'
    FalseLiteral = 'False'

    Const = 'const'
    Let = 'let'
    Rebind = 'rebind'

    If = 'if'

    ImportModule = 'import-module'

    Del = 'del'

    Lambda = 'lambda'

    Macro = 'macro'

    Do = 'do'

    Expression = 'expr!'

    EvaluateExpression = 'eval!'

    Inline = 'inline!'
    InlineLiteral = 'inline-value!'

    Symbolic = 'symbolic!'

    VariadicMarker = '&'

    Raise = 'raise'

    RunCatching = 'run-catching'

    MakeLazy = 'make-lazy'
