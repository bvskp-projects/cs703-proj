# Enumeration function

from collections import deque

class Work:
    pass

def enumerate(rtg, spec):
    """
    Returns
      the enumerated jq expression if found
      None otherwise
    """

    worklist = deque()
    while count(worklist) > 0 and worklist.depth < 5:

