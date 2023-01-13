__all__ = (
    "ParsingExpression",
    "ParsingExpressionLike",
    "enable_method_in_parser_python",
    "not_start_with_keyword",
    "returns_parsing_expression",
)

import builtins
import types
from functools import wraps
from typing import Any, Callable, ClassVar, Tuple, Type, TypeVar, cast

import arpeggio
from typing_extensions import ParamSpec, Protocol, TypeAlias

P = ParamSpec("P")
T = TypeVar("T")
T_keywords = TypeVar("T_keywords", bound="SupportsKeywords")

ParsingExpression = arpeggio.ParsingExpression
ParsingExpressionLike: TypeAlias = "arpeggio._ParsingExpressionLike"


__builtins_isinstance = builtins.isinstance


@wraps(__builtins_isinstance)
def __callable_is_instance_of_function(obj: Any, class_or_tuple: Any) -> bool:
    if class_or_tuple is types.FunctionType:  # noqa: E721
        return __builtins_isinstance(obj, Callable)  # type: ignore
    else:
        return __builtins_isinstance(obj, class_or_tuple)


def enable_method_in_parser_python(f: Callable[P, T]) -> Callable[P, T]:
    @wraps(f)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            builtins.isinstance = __callable_is_instance_of_function
            return f(*args, **kwargs)
        finally:
            builtins.isinstance = __builtins_isinstance

    return wrapped


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
