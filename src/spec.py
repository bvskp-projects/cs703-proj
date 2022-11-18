"""
Specification
"""

from typing import Dict, Optional
from .pipeline import construct, Expr

import pyjq

def flatten(data) -> list:
    values = []
    if isinstance(data, dict):
        for value in data.values():
            values.extend(flatten(value))

    if isinstance(data, list):
        for value in data:
            values.extend(flatten(value))

    if isinstance(data, bool) or isinstance(data, int) or isinstance(data, str):
        values.append(data)

    return values

class Spec:
    def __init__(self, examples: list[dict], constants: list):
        self.examples = examples
        self.bool_constants = []
        self.int_constants = []
        self.str_constants = []

        for example in self.examples:
            example['flatten'] = frozenset(flatten(example['output']))

        for constant in constants:
            if isinstance(constant, bool):
                self.bool_constants.append(constant)

            if isinstance(constant, int):
                self.int_constants.append(constant)

            if isinstance(constant, str):
                self.str_constants.append(constant)

    def verify(self, expr: Expr) -> tuple[Optional[str], int]:
        """
        Verify whether the expression satisfies the specification
        If yes, returns the string representation of the expression
        Otherwise, returns None
        """
        expr_str = construct(expr)
        for example in self.examples:
            output = pyjq.all(expr_str, example['input'])
            if output != example['output']:
                return None, self.get_score(frozenset(flatten(output)), example['flatten'])
        return expr_str, 0

    def get_score(self, actual, expected):
        """
        Returns number of elements absent from the extracted output
        """
        return len(expected-actual)

    def get_bool_constants(self) -> list[bool]:
        return self.bool_constants

    def get_int_constants(self) -> list[int]:
        return self.int_constants

    def get_str_constants(self) -> list[str]:
        return self.str_constants
