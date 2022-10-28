from collections import deque
import pyjq

class Operator(object):
    def __init__(self):
        self.term = False
    def __str__(self):
        return '#%s#' % self.__class__.__name__
    def __repr__(self):
        return str(self)

class OpAttrNT(Operator):
    def __init__(self, expr, spec, forpipe = False):
        super().__init__()
        self.term = False
        assert(runnable(expr))
        _, outputs = run_expr(expr, spec)
        # Now we need to select an attribute.
        first = outputs[0][0]
        if type(first) != dict:
            raise ValueError
        
        if not forpipe:
            keys = set(list(first.keys()))
        else:
            keys = set()
            for k in first.keys(): 
                keys = keys.union(list(first[k].keys()) if type(first[k]) == dict else [])

        for output in outputs[1:]:
            o = output[0]
            if type(o) != dict:
                raise ValueError

            if not forpipe:
                newkeys = set(list(o.keys()))
            else:
                newkeys = set()
                for k in o.keys(): 
                    newkeys = newkeys.add(list(o[k].keys()) if type(o[k]) == dict else [])
            keys = keys.union(newkeys)
        self.keys = keys

    def gen(self):
        return [OpAttr(x) for x in self.keys]

class OpForEachNT(Operator):
    def __init__(self, expr, spec):
        super().__init__()
        self.term = False
        self.expr = expr
        self.spec = spec
    def gen(self):
        return [(OpForEach(), OpAttrNT(self.expr, self.spec, forpipe=True))]

class OpForEach(Operator):
    def __init__(self):
        super().__init__()
        self.term = True
    def __str__(self):
        return ' | .[] | '

# class OpHasNT(Operator):
#     def __init__(self, expr, spec):
#         super().__init__()
#         self.term = False
#         assert(runnable(expr))
#         _, outputs = run_expr(expr, spec)
#         # Now we need to select an attribute.
#         first = outputs[0][0]
#         if type(first) != dict:
#             raise ValueError
        
#         keys = set(list(first.keys()))
#         for output in outputs[1:]:
#             o = output[0]
#             if type(o) != dict:
#                 raise ValueError
#             keys.union(set(list(o.keys())))
#         self.keys = keys

#     def gen(self):
#         return [OpHas(x) for x in self.keys]

class OpAttr(Operator):
    def __init__(self, atr):
        super().__init__()
        self.term = True
        self.atr = atr
    def __str__(self):
        return '.%s' % self.atr

# class OpHas(Operator):
#     def __init__(self, atr):
#         super().__init__()
#         self.term = True
#         self.atr = atr
#     def __str__(self):
#         return '| has("%s")' % self.atr

class OpIdentity(Operator):
    def __init__(self):
        super().__init__()
        self.term = True
    def __str__(self):
        return '.'


def runnable(expr):
    return all(map(lambda x: x.term, expr))

def construct(expr):
    if type(expr[0]) == OpIdentity and len(expr) > 1 and type(expr[1]) != OpForEach:
        e = expr[1:]
    else:
        e = expr
    return ''.join(map(lambda x: str(x), e))

def run_expr(expr, spec):
    expr_str = construct(expr)
    outputs = []
    match = True
    for example in spec:
        output = pyjq.all(expr_str, example['input'])
        if output != example['output']:
            match = False
        outputs.append(output)
    return (match, outputs)

def enumerate(rtg, spec):
    """
    Returns
      the enumerated jq expression if found
      None otherwise
    """

    worklist = deque()
    ops = [OpAttrNT, OpForEachNT]
    worklist.append([OpIdentity()])
    while len(worklist) > 0:
        expr = worklist.pop()
        if len(expr) > 5: continue
        if not runnable(expr):
            rhs = expr.pop()
            assert(rhs.term == False)
            for new in rhs.gen():
                if type(new) != tuple:
                    worklist.append(expr + [new])
                else:
                    worklist.append(expr + [new[0], new[1]])
            # TODO: open the left most non-terminal and add to worklist
            continue

        # Run it and compare input output

        match, _ = run_expr(expr, spec)
        if match: return expr

        for op in ops:
            type_infer_expr = expr + [op(expr, spec)]
            worklist.append(type_infer_expr)

if __name__ == '__main__':
    import json, os
    tests = ["identifier.json", "identity.json", "projection.json"]
    for t in tests:
        with open(os.path.join("examples", t), 'r') as f:
            data = f.read(4096)
            spec = json.loads(data)['examples']
            rvalue = enumerate(None, spec)
            print("%s: %s" % (t, construct(rvalue)))