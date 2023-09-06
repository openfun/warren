"""Test Warren utility functions."""
import pytest

from warren.utils import pipe


def test_pipe():
    """Test the pipe function."""

    def add(x):
        return x + 1

    def minus(x):
        return x - 2

    def mult(x):
        return x * 3

    assert pipe(add, minus, mult)(3) == 6
    assert pipe(add, mult)(2) == 9
    assert pipe(add)(1) == 2
    with pytest.raises(TypeError):
        pipe()()
