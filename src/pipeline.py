"""
Operations and Pipeline
"""

import json

class Operator:
    def __str__(self):
        return self.jq_repr()

Expr = list[Operator]

def construct(expr: Expr) -> str:
    if len(expr) == 0:
        return '.'

    return ' | '.join([term.jq_repr() for term in expr])

def identity() -> Expr:
    return []

############
## Operators
############

class All(Operator):
    def jq_repr(self):
        return 'all'

class Any(Operator):
    def jq_repr(self):
        return 'any'

class ForEach(Operator):
    def jq_repr(self):
        return '.[]'

class GroupBy(Operator):
    def __init__(self, object_index):
        self.object_index = object_index

    def jq_repr(self):
        return f'group_by({self.object_index.jq_repr()})'

class Keys(Operator):
    def jq_repr(self):
        return 'keys'

class ObjectIndex(Operator):
    def __init__(self, index):
        self.index = index

    def jq_repr(self):
        return f'.{self.index}'

class Select(Operator):
    def __init__(self, pred):
        self.pred = pred

    def jq_repr(self):
        return f'select({self.pred.jq_repr()})'

class Sort(Operator):
    def jq_repr(self):
        return 'sort'

class SortBy(Operator):
    def __init__(self, object_index):
        self.object_index = object_index

    def jq_repr(self):
        return f'sort_by({self.object_index.jq_repr()})'

#############
## Predicates
#############

class Predicate:
    def __str__(self):
        return self.jq_repr()

class EqualityPred(Predicate):
    def __init__(self, object_index, value):
        self.object_index = object_index
        self.value = value

    def jq_repr(self):
        return f'{self.object_index.jq_repr()} == {json.dumps(self.value)}'
