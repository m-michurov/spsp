from enum import Enum


class Keyword(str, Enum):
    NoneLiteral = 'None'

    TrueLiteral = 'True'
    FalseLiteral = 'False'

    Const = 'const'
    Let = 'let'

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

    VariadicMarker = '&'

    Raise = 'raise'

    RunCatching = 'run-catching'

    MakeLazy = 'make-lazy'
