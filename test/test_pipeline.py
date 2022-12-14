"""
Test pipeline functions
"""

import unittest

from test.context import jqsyn
from jqsyn.pipeline import (
    construct,
    All,
    Any,
    GroupBy,
    ObjectIndex,
    Keys,
    Select,
    EqualityPred,
    Sort,
    SortBy,
    ForEach,
)


class TestPipeline(unittest.TestCase):
    def test_single_stage(self):
        self.assertEqual(construct([All()]), "all")
        self.assertEqual(construct([Any()]), "any")
        self.assertEqual(construct([GroupBy(ObjectIndex("foo"))]), "group_by(.foo)")
        self.assertEqual(construct([Keys()]), "keys")
        self.assertEqual(
            construct([Select(EqualityPred(ObjectIndex("foo"), 42))]),
            "select(.foo == 42)",
        )
        self.assertEqual(construct([Sort()]), "sort")
        self.assertEqual(construct([SortBy(ObjectIndex("foo"))]), "sort_by(.foo)")

    # Needs modification if we intend to condense the pipeline in the future
    def test_double_stage(self):
        expr_str = construct([ForEach(), Sort()])
        self.assertEqual(
            [term.strip() for term in expr_str.split("|")], [".[]", "sort"]
        )
