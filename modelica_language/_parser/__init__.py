__all__ = ("ParserPEG",)

import builtins
import functools
import types
import typing
import warnings
from typing import Any, Optional, Tuple

import arpeggio

from ..exceptions import ParserWarning
from . import peg_syntax, peg_visitor

_builtins__isinstance = builtins.isinstance


@functools.wraps(_builtins__isinstance)
def _callable_is_instance_of_function(obj: Any, class_or_tuple: Any) -> bool:
    if class_or_tuple is types.FunctionType:  # noqa: E721
        class_or_tuple = typing.Callable
    return _builtins__isinstance(obj, class_or_tuple)


class ParserPython(arpeggio.ParserPython):
    @functools.wraps(arpeggio.ParserPython._from_python)
    def _from_python(self, *args: Any, **kwargs: Any) -> Any:
        try:
            builtins.isinstance = _callable_is_instance_of_function
            return super()._from_python(*args, **kwargs)
        finally:
            builtins.isinstance = _builtins__isinstance


class ParserPEG(arpeggio.Parser):
    def __init__(
        self,
        language_def: str,
        root_rule_name: str,
        comment_rule_name: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ):
        """
        Constructs parser from textual PEG definition.

        Args:
            language_def (str): A string describing language grammar using
                PEG notation.
            root_rule_name(str): The name of the root rule.
            comment_rule_name(str): The name of the rule for comments.
        """

        ignore_case: bool = kwargs.pop("ignore_case", False)
        if ignore_case:
            warnings.warn(
                (
                    f"ignore_case is {ignore_case!r}\n"
                    "Modelica grammar should be case-sensitive."
                ),
                ParserWarning,
            )

        super(ParserPEG, self).__init__(*args, **kwargs)
        self.root_rule_name = root_rule_name
        self.comment_rule_name = comment_rule_name

        # PEG Abstract Syntax Graph
        self.parser_model, self.comments_model = self._from_peg(language_def)

        # In debug mode export parser model to dot for
        # visualization
        if self.debug:
            from arpeggio.export import PMDOTExporter

            root_rule = self.parser_model.rule_name
            PMDOTExporter().exportFile(
                self.parser_model, "{}_peg_parser_model.dot".format(root_rule)
            )

    def _parse(self) -> arpeggio.ParseTreeNode:
        return self.parser_model.parse(self)

    def _from_peg(
        self, language_def: str
    ) -> Tuple[
        arpeggio.ParsingExpression, Optional[arpeggio.ParsingExpression]
    ]:
        parser = arpeggio.ParserPython(
            peg_syntax.grammar,
            peg_syntax.comment,
            reduce_tree=False,
            debug=self.debug,
        )
        parse_tree = parser.parse(language_def)

        return peg_visitor.visit_parse_tree(
            parse_tree,
            self.root_rule_name,
            self.comment_rule_name,
            self.debug,
        )
