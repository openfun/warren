"""Warren utils."""
from functools import reduce
from typing import Callable


def pipe(*functions: Callable) -> Callable:
    """Create a functions pipeline.

    Note that functions are applied in the order they are passed to the
    function (first one first).

    Example usage:

    # Given `a()`, `b()` and `c()` defined functions
    output = pipe(a, b, c)(input)

    """
    return reduce(lambda f, g: lambda x: g(f(x)), functions, lambda x: x)
