"""
Run synthesizer on example dataset
"""

import json, os
import unittest

from .synthesize import synthesize

def run_example(filename):
    with open(os.path.join('examples', filename), 'r') as f:
        data = json.load(f)
        spec = data['examples']
        expr = data['expression']
        constants = []
        if 'constants' in data:
            constants = data['constants']
        print(f'Synthesizing expression: {expr}')
        expr_str = synthesize(spec, constants)
        print(f'Synthesized expression: {expr_str}')

# NOTE: Exception is thrown when we fail to syntehsize
class TestExamples(unittest.TestCase):
    def test_all(self):
        run_example('all.json')

    def test_any(self):
        run_example('any.json')

    def test_group_by(self):
        run_example('group_by.json')

    def test_index(self):
        run_example('identifier.json')

    def test_identity(self):
        run_example('identity.json')

    def test_keys(self):
        run_example('keys.json')

    def test_foreach(self):
        run_example('pipe.json')

    def test_foreach_dict(self):
        run_example('projection.json')

    def test_select(self):
        run_example('select.json')

    def test_sort(self):
        run_example('sort.json')

    def test_sort_by(self):
        run_example('sort_by.json')


if __name__ == '__main__':
    unittest.main()
