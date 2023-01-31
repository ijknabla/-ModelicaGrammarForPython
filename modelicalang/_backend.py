__all__ = (
    "ParsingExpression",
    "ParsingExpressionLike",
    "enable_method_in_parser_python",
    "not_start_with_keyword",
    "returns_parsing_expression",
)

import builtins
import enum
import types
from functools import wraps
from types import TracebackType
from typing import (
    Any,
    Callable,
    ClassVar,
    Optional,
    Tuple,
    Type,
    TypeVar,
    cast,
)

import arpeggio
from arpeggio import ParserPython
from typing_extensions import ParamSpec, Protocol, TypeAlias

P = ParamSpec("P")
T = TypeVar("T")
T_keywords = TypeVar("T_keywords", bound="SupportsKeywords")

ParsingExpression = arpeggio.ParsingExpression
ParsingExpressionLike: TypeAlias = "arpeggio._ParsingExpressionLike"


_isinstance__builtins = builtins.isinstance


def _isinstance__callable_as_function(obj: Any, class_or_tuple: Any) -> bool:
    if class_or_tuple is types.FunctionType:  # noqa: E721
        return _isinstance__builtins(obj, Callable)  # type: ignore
    else:
        return _isinstance__builtins(obj, class_or_tuple)


class EnableMethodInParserPython(enum.Enum):
    instance = enum.auto()

    def __call__(self, f: Callable[P, T]) -> Callable[P, T]:
        @wraps(f)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            with self:
                return f(*args, **kwargs)

        return wrapped

    def __enter__(self) -> Type[ParserPython]:
        builtins.isinstance = _isinstance__callable_as_function
        return ParserPython

    def __exit__(
        self,
        typ: Optional[Type[BaseException]],
        value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        builtins.isinstance = _isinstance__builtins
        return None


enable_method_in_parser_python = EnableMethodInParserPython.instance


class SupportsKeywords(Protocol):
    _keywords_: ClassVar[Tuple[str, ...]]


def not_start_with_keyword(
    f: Callable[[Type[T_keywords]], ParsingExpression]
) -> Callable[[Type[T_keywords]], ParsingExpression]:
    @wraps(f)
    @returns_parsing_expression
    def wrapped(cls: Type[T_keywords]) -> ParsingExpressionLike:
        return (
            arpeggio.Not(
                arpeggio.RegExMatch(
                    r"(" + r"|".join(cls._keywords_) + r")(?![0-9A-Z_a-z])"
                )
            ),
            f(cls),
        )

    return wrapped


def returns_parsing_expression(
    f: Callable[P, ParsingExpressionLike]
) -> Callable[P, ParsingExpression]:
    return cast(Callable[P, ParsingExpression], f)