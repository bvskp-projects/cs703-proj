"""
Test Schema
"""

import unittest

from jqsyn.schema import get_schema


class TestSchema(unittest.TestCase):
    def test_list_bool(self):
        example = [True, False]
        schema = get_schema([example])
        self.assertEqual(str(schema), "ListSchema[BoolSchema]")

    def test_list_empty(self):
        example = []
        schema = get_schema([example])
        self.assertEqual(str(schema), "ListSchema[AnySchema]")

    def test_dict(self):
        example = {"foo": 42, "bar": "42"}
        schema = get_schema([example])
        self.assertEqual(
            str(schema), "DictSchema{foo: IntSchema, bar: StrSchema}{NoneSchema}"
        )

    def test_intersect(self):
        example0 = {"foo": 42, "bar": "42"}
        example1 = {"bar": "forty two"}
        schema = get_schema([example0, example1])
        self.assertEqual(str(schema), "DictSchema{bar: StrSchema}{NoneSchema}")

    def test_intersect_any(self):
        example0 = [True]
        example1 = []
        schema = get_schema([example0, example1])
        self.assertEqual(str(schema), "ListSchema[BoolSchema]")


class RuleSpec:
    def get_bool_constants(self) -> list[bool]:
        return []

    def get_int_constants(self) -> list[int]:
        return [42]

    def get_str_constants(self) -> list[str]:
        return []


class TestRules(unittest.TestCase):
    def test_list_bool(self):
        example = [True, False]
        schema = get_schema([example])
        rules = sorted(
            [(str(op), str(schema)) for op, schema in schema.rules(RuleSpec())]
        )
        expected = sorted(
            [
                ("any", "BoolSchema"),
                ("all", "BoolSchema"),
                (".[]", "BoolSchema"),
                ("sort", "ListSchema[BoolSchema]"),
            ]
        )
        self.assertEqual(rules, expected)

    def test_list_dict(self):
        example = [{"foo": 1, "bar": 2}, {"foo": 3, "bar": 4}]
        schema = get_schema([example])
        rules = sorted(
            [(str(op), str(schema)) for op, schema in schema.rules(RuleSpec())]
        )
        expected = sorted(
            [
                (
                    "group_by(.foo)",
                    (
                        "ListSchema[ListSchema[DictSchema{foo: IntSchema, bar:"
                        " IntSchema}{IntSchema}]]"
                    ),
                ),
                (
                    "group_by(.bar)",
                    (
                        "ListSchema[ListSchema[DictSchema{foo: IntSchema, bar:"
                        " IntSchema}{IntSchema}]]"
                    ),
                ),
                (
                    "sort_by(.foo)",
                    "ListSchema[DictSchema{foo: IntSchema, bar: IntSchema}{IntSchema}]",
                ),
                (
                    "sort_by(.bar)",
                    "ListSchema[DictSchema{foo: IntSchema, bar: IntSchema}{IntSchema}]",
                ),
                (".[]", "DictSchema{foo: IntSchema, bar: IntSchema}{IntSchema}"),
                (
                    "sort",
                    "ListSchema[DictSchema{foo: IntSchema, bar: IntSchema}{IntSchema}]",
                ),
            ]
        )
        self.assertEqual(rules, expected)

    def test_dict(self):
        example = {"foo": 42}
        schema = get_schema([example])
        rules = sorted(
            [(str(op), str(schema)) for op, schema in schema.rules(RuleSpec())]
        )
        expected = sorted(
            [
                (".[]", "IntSchema"),
                ("keys", "ListSchema[StrSchema]"),
                (".foo", "IntSchema"),
                ("select(.foo == 42)", "DictSchema{foo: IntSchema}{IntSchema}"),
            ]
        )
        self.assertEqual(rules, expected)
