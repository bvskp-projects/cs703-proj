"""
Schema

Operator types
- all:          list bool -> bool
- any:          list bool -> bool
- foreach:      list 'a -> stream 'a
- foreach:      dict v -> stream v
- group by:     list dict -> list (list dict)
- keys:         dict -> list str
- obj index:    dict v -> v
- select:       'a -> 'a?
- sort:         list 'a -> list 'a
- sort by:      list dict -> list dict
"""

from jqsyn.pipeline import Operator
from jqsyn.pipeline import All, Any, ForEach, Keys, Sort
from jqsyn.pipeline import GroupBy, ObjectIndex, SortBy
from jqsyn.pipeline import Select, EqualityPred


class Schema:
    pass


def get_schema(inputs: list) -> Schema:
    """
    Return a common schema for all the input json objects
    """
    return intersect([extract_schema(obj) for obj in inputs])


def extract_schema(obj) -> Schema:
    """
    Extract schema from an individual json object
    """
    if isinstance(obj, dict):
        kvs = {}
        for key, value in obj.items():
            kvs[key] = extract_schema(value)
        return DictSchema(
            kvs, intersect([extract_schema(value) for value in obj.values()])
        )
    elif isinstance(obj, list):
        return ListSchema(intersect([extract_schema(elem) for elem in obj]))
    elif isinstance(obj, bool):
        return BoolSchema()
    elif isinstance(obj, int):
        return IntSchema()
    elif isinstance(obj, str):
        return StrSchema()
    else:
        return NoneSchema()


def intersect(schemas: list[Schema]) -> Schema:
    """
    Helper function to get the common schema for all the objects
    """
    if len(schemas) == 0:
        return AnySchema()

    schema = schemas[0]
    for i in range(1, len(schemas)):
        schema = schema.intersect(schemas[i])

    return schema


##########
## Schemas
##########


class NoneSchema(Schema):
    """
    Represents the empty set
    """

    def rules(self, spec) -> list[tuple[Operator, Schema]]:
        return []

    def intersect(self, other: Schema):
        return NoneSchema()

    def __str__(self):
        return self.__class__.__name__


class AnySchema(Schema):
    """
    Represents the universal set
    """

    def rules(self, spec) -> list[tuple[Operator, Schema]]:
        raise NotImplementedError

    def intersect(self, other: Schema):
        return other

    def __str__(self):
        return self.__class__.__name__


class DictSchema(Schema):
    """
    Represents JSON dictionaries
    """

    def __init__(self, kvs: dict[str, Schema], value_schema: Schema):
        self.kvs = kvs
        self.value_schema = value_schema

    def rules(self, spec) -> list[tuple[Operator, Schema]]:
        # Possible operators:
        # - .[]
        # - .index
        # - select(.index==value)
        # - keys

        ops = []

        # .index, select
        for index, schema in self.kvs.items():
            ops.append((ObjectIndex(index), schema))

            if isinstance(schema, BoolSchema) or isinstance(schema, AnySchema):
                for bool_const in spec.get_bool_constants():
                    ops.append(
                        (Select(EqualityPred(ObjectIndex(index), bool_const)), self)
                    )

            if isinstance(schema, IntSchema) or isinstance(schema, AnySchema):
                for int_const in spec.get_int_constants():
                    ops.append(
                        (Select(EqualityPred(ObjectIndex(index), int_const)), self)
                    )

            if isinstance(schema, StrSchema) or isinstance(schema, AnySchema):
                for str_const in spec.get_str_constants():
                    ops.append(
                        (Select(EqualityPred(ObjectIndex(index), str_const), self))
                    )

        # .[]
        ops.append((ForEach(), self.value_schema))

        # keys
        ops.append((Keys(), ListSchema(StrSchema())))

        return ops

    def intersect(self, other: Schema) -> Schema:
        if isinstance(other, AnySchema):
            return self

        if isinstance(other, DictSchema):
            kvs = {}
            for key, schema in self.kvs.items():
                if key in other.kvs:
                    kvs[key] = schema.intersect(other.kvs[key])

            return DictSchema(kvs, self.value_schema.intersect(other.value_schema))

        return NoneSchema()

    def __str__(self):
        kvs = ", ".join([f"{key}: {value}" for key, value in self.kvs.items()])
        return f"{self.__class__.__name__}{{{kvs}}}{{{self.value_schema}}}"


class ListSchema(Schema):
    """
    Represents JSON lists
    """

    def __init__(self, elem_schema: Schema):
        self.elem_schema = elem_schema

    def rules(self, spec) -> list[tuple[Operator, Schema]]:
        # Possible operators
        # - list bool
        #   - all
        #   - any
        # - list dict
        #   - group_by
        #   - sort_by
        # - list 'a
        #   - foreach
        #   - sort

        ops = []

        # any, all
        if isinstance(self.elem_schema, BoolSchema) or isinstance(
            self.elem_schema, AnySchema
        ):
            ops.append((All(), BoolSchema()))
            ops.append((Any(), BoolSchema()))

        # group_by, sort_by
        if isinstance(self.elem_schema, DictSchema):
            for index in self.elem_schema.kvs:
                ops.append((GroupBy(ObjectIndex(index)), ListSchema(self)))
                ops.append((SortBy(ObjectIndex(index)), self))

        # .[], sort
        ops.append((ForEach(), self.elem_schema))
        ops.append((Sort(), self))

        return ops

    def intersect(self, other: Schema) -> Schema:
        if isinstance(other, AnySchema):
            return self

        if isinstance(other, ListSchema):
            return ListSchema(self.elem_schema.intersect(other.elem_schema))

        return NoneSchema()

    def __str__(self):
        return f"{self.__class__.__name__}[{self.elem_schema}]"


class BoolSchema(Schema):
    """
    Represents JSON booleans
    """

    def rules(self, spec) -> list[tuple[Operator, Schema]]:
        return []

    def intersect(self, other: Schema) -> Schema:
        if isinstance(other, AnySchema):
            return self

        if isinstance(other, BoolSchema):
            return BoolSchema()

        return NoneSchema()

    def __str__(self):
        return self.__class__.__name__


class IntSchema(Schema):
    """
    Represents JSON integers
    """

    def rules(self, spec) -> list[tuple[Operator, Schema]]:
        return []

    def intersect(self, other: Schema) -> Schema:
        if isinstance(other, AnySchema):
            return self

        if isinstance(other, IntSchema):
            return IntSchema()

        return NoneSchema()

    def __str__(self):
        return self.__class__.__name__


class StrSchema(Schema):
    """
    Represents JSON strings
    """

    def rules(self, spec) -> list[tuple[Operator, Schema]]:
        return []

    def intersect(self, other: Schema) -> Schema:
        if isinstance(other, AnySchema):
            return self

        if isinstance(other, StrSchema):
            return StrSchema()

        return NoneSchema()

    def __str__(self):
        return self.__class__.__name__
