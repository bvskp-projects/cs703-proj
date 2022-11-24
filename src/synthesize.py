"""
Synthesis function
TODO: Support recursive paths (including identity)
"""

from .schema import get_schema, Schema
from .spec import Spec
from .pipeline import identity, Expr
from queue import PriorityQueue
from heapq import heappush, heappop
from dataclasses import dataclass, field

def bottom_up(spec: Spec, input_schema: Schema, depth: int) -> str:
    """
    Bottom up enumeration of jq parse expressions
    """
    @dataclass(order=True)
    class Work:
        priority: int
        length: int
        expr: Expr = field(compare=False)
        schema: Schema = field(compare=False)

    # worklist = deque()
    worklist = []
    expr_str, score = spec.verify(identity())
    if expr_str is not None:
        return expr_str
    heappush(worklist, Work(score, 0, identity(), input_schema))
    while len(worklist) > 0:
        work = heappop(worklist)
        expr, expr_schema = work.expr, work.schema
        if len(expr) >= depth:
            continue
        for op, schema in expr_schema.rules(spec):
            next_expr = expr + [op]
            expr_str, score = spec.verify(next_expr)
            if expr_str is not None:
                return expr_str
            heappush(worklist, Work(score, len(next_expr), next_expr, schema))

    raise OutOfDepth(depth)

def synthesize(examples: list[dict], constants: list = [], depth: int = 3) -> str:
    """
    Returns a jq parse expression string that satisfies the input-output examples
    """
    input_schema = get_schema([example['input'] for example in examples])
    spec = Spec(examples, constants)
    return bottom_up(spec, input_schema, depth)

class OutOfDepth(Exception):
    """
    Raised when all expressions until the specified depth are enumerated
    """
    def __init__(self, depth: int):
        self.depth = depth

    def __str__(self):
        return f'Exhausted all supported expressions till depth: {self.depth}'
