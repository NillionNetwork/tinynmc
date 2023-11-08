"""
Minimal pure-Python implementation of a secure multi-party computation
(MPC) protocol for evaluating arithmetic sum-of-products expressions via
a non-interactive computation phase.
"""
from __future__ import annotations
import doctest
import operator
import functools
import random
from modulo import mod

class node:
    def __init__(self, n: int):
        """
        Instantiate an object that maintains the state of a node
        (out of ``n`` nodes in a protocol instance).
        """
        (self.p, self.q, self.g) = (4215209819, 2107604909, 3844384293)
        self._masks = None
        self._shares = None

    def correlate(self, signature, exponents, shares_):
        """
        Generate masks for the given signature from the existing lambda.
        """
        self._shares = shares_
        self._masks = {}
        for (term_index, factor_count) in enumerate(signature):
            factors = [
                self.g ** int(l)
                for l in shares(
                    -int(exponents[term_index]),
                    self.q * 2,
                    factor_count
                )
            ]
            self._masks[(term_index, -1)] = self.g ** int(exponents[term_index])
            for factor_index in range(factor_count):
                self._masks[(term_index, factor_index)] = factors[factor_index]

    def masks(self, signature, coords_from_dealer) -> dict[tuple[int, int], mod]:
        """
        Return a dictionary mapping a set of ``(term_index, factor_index)``
        coordinates to their corresponding masks.
        """
        return {coords: self._masks[coords] for coords in coords_from_dealer}

    def compute(self, signature, mfss):
        """
        Compute a secret share of the result (of evaluating the expression).
        """
        # Combine all submitted coordinate-particle pair dictionaries
        # into a single dictionary.
        mfs = functools.reduce((lambda mfs, mfs_: mfs | mfs_), mfss)

        # Compute this node's share of the overall sum of products.
        return sum([
            self._shares[term_index]
            *
            (lambda iterable: functools.reduce(operator.mul, iterable))(
                mfs[(term_index, factor_index)]
                for factor_index in range(factor_quantity)
            )
            for (term_index, factor_quantity) in enumerate(signature)
        ])

def particles(coords_to_values, masks_from_nodes):
    """
    Build up dictionary mapping each coordinate to a value that is
    masked using the product of the masks (from all nodes) at that
    coordinate.
    """
    return {
        coords: value * prd([
            coords_to_masks[coords]
            for coords_to_masks in masks_from_nodes
        ])
        for (coords, value) in coords_to_values.items()
    }

if __name__ == '__main__':
    doctest.testmod()
