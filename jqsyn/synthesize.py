"""
Synthesis function
TODO: Support recursive paths (including identity)
"""

from jqsyn.schema import get_schema, Schema, DictSchema, ListSchema
from jqsyn.spec import Spec
from jqsyn.pipeline import identity, Expr
from queue import PriorityQueue
from heapq import heappush, heappop
from dataclasses import dataclass, field
from copy import deepcopy


def bottom_up(
    spec: Spec, input_schema: Schema, depth: int, max_results: int
) -> list[str]:
    """
    Bottom up enumeration of jq parse expressions
    """

    @dataclass(order=True)
    class Work:
        priority: int
        length: int
        expr: Expr = field(compare=False)
        schema: Schema = field(compare=False)

    results = []
    worklist = []
    expr_str, score = spec.verify(identity())
    if expr_str is not None:
        results.append(expr_str)
        if len(results) == max_results:
            return results
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
                results.append(expr_str)
                if len(results) == max_results:
                    return results
            heappush(worklist, Work(score, len(next_expr), next_expr, schema))

    if results:
        return results
    else:
        raise OutOfDepth(depth)


def union_synthesis(
    input_schema,
    output_schema,
    input_examples: list,
    output_examples: list,
    constants: list,
    depth: int,
) -> str:
    if isinstance(output_schema, DictSchema):
        union_dict = {}
        for key, value_schema in output_schema.kvs.items():
            key_examples = []
            for output_example in output_examples:
                key_examples.append(output_example[key])
            union_dict[key] = union_synthesis(
                input_schema,
                value_schema,
                input_examples,
                key_examples,
                constants,
                depth,
            )
        exprs = [f"{key}: {expr_str}" for key, expr_str in union_dict.items()]
        exprs = ", ".join(exprs)
        return f"{{{exprs}}}"
    elif isinstance(output_schema, ListSchema):
        examples = [
            {"input": input_example, "output": output_example}
            for input_example, output_example in zip(input_examples, output_examples)
        ]
        return bottom_up(Spec(examples, constants), input_schema, depth, 1)[0]
    else:
        examples = [
            {"input": input_example, "output": [output_example]}
            for input_example, output_example in zip(input_examples, output_examples)
        ]
        return bottom_up(Spec(examples, constants), input_schema, depth, 1)[0]


def multi_synthesis(
    examples: list[dict], constants: list = [], depth: int = 3, max_results: int = 1
) -> list[str]:
    """
    Returns a jq parse expression string that satisfies the input-output examples
    """
    input_examples = [example["input"] for example in examples]
    input_schema = get_schema(input_examples)
    try:
        spec = Spec(examples, constants)
        return bottom_up(spec, input_schema, depth, max_results)
    except OutOfDepth:
        # message_examples = deepcopy(examples)
        # name_examples = deepcopy(examples)
        # parents_examples = deepcopy(examples)
        # for example in message_examples:
        #     example["output"] = [example["output"][0]["message"]]
        # for example in name_examples:
        #     example["output"] = [example["output"][0]["name"]]
        # for example in parents_examples:
        #     example["output"] = example["output"][0]["parents"]
        # message_expr = bottom_up(Spec(message_examples, constants), input_schema, depth)
        # name_expr = bottom_up(Spec(name_examples, constants), input_schema, depth)
        # parents_expr = bottom_up(Spec(parents_examples, constants), input_schema, depth)
        # return (
        #     f"{{message: {message_expr}, name: {name_expr}, parents: [{parents_expr}]}}"
        # )
        output_examples = [example["output"][0] for example in examples]
        output_schema = get_schema(output_examples)
        return [
            union_synthesis(
                input_schema,
                output_schema,
                input_examples,
                output_examples,
                constants,
                depth,
            )
        ]


def synthesize(examples: list[dict], constants: list = [], depth: int = 3) -> str:
    return multi_synthesis(examples, constants, depth)


class OutOfDepth(Exception):
    """
    Raised when all expressions until the specified depth are enumerated
    """

    def __init__(self, depth: int):
        self.depth = depth

    def __str__(self):
        return f"Exhausted all supported expressions till depth: {self.depth}"
