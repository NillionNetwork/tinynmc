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

def _prod(iterable):
    return functools.reduce(operator.mul, iterable)

def _merge(d, d_):
    d__ = {}
    d__.update(d)
    d__.update(d_)
    return d__

def _shares(s, modulus, quantity) -> list[mod]:
    ss = []
    for _ in range(quantity - 1):
        ss.append(mod(random.randint(0, modulus - 1), modulus))

    return [mod(s, modulus) - sum(ss)] + ss

class node:
    """
    Data structure for maintaining the information associated with a node in
    a protocol instantiation.

    Suppose that a protocol instance involves three contributors (parties
    submitting private input values) and three nodes (parties performing the
    computation).

    >>> nodes = [node(), node(), node()]

    Given a signature for the expression to be computed, it is possible to
    simulate the preprocessing phase.

    >>> signature = [3, 2]
    >>> preprocessing(signature, nodes)
    
    Each contributor can then generate request its masked factors from the
    nodes.

    >>> coords_to_values_a = {(0, 0): 1, (1, 0): 4}
    >>> masks_from_nodes_to_a = [node.masks(coords_to_values_a.keys()) for node in nodes]
    >>> masked_factors_a = masked_factors(coords_to_values_a, masks_from_nodes_to_a)

    >>> coords_to_values_b = {(0, 1): 2, (1, 1): 5}
    >>> masks_from_nodes_to_b = [node.masks(coords_to_values_b.keys()) for node in nodes]
    >>> masked_factors_b = masked_factors(coords_to_values_b, masks_from_nodes_to_b)

    >>> coords_to_values_c = {(0, 2): 3}
    >>> masks_from_nodes_to_c = [node.masks(coords_to_values_c.keys()) for node in nodes]
    >>> masked_factors_c = masked_factors(coords_to_values_c, masks_from_nodes_to_c)
    
    Each contributor broadcasts all of its masked factors to every node, so every
    node receives all the masked factors from all the contributors and performs
    its computation.

    >>> broadcast = [masked_factors_a, masked_factors_b, masked_factors_c]
    >>> result_share_at_node_0 = nodes[0].compute(signature, broadcast)
    >>> result_share_at_node_1 = nodes[1].compute(signature, broadcast)
    >>> result_share_at_node_2 = nodes[2].compute(signature, broadcast)

    The result can be reconstructed via summation from the result shares
    received from the nodes.

    >>> int(sum([result_share_at_node_0, result_share_at_node_1, result_share_at_node_2]))
    26
    """
    def __init__(self):
        """
        Instantiate an object that maintains the state of a node.
        """
        (self.p, self.q) = (4215209819, 2107604909)
        self.g = mod(3844384293, self.p)
        self._masks = None
        self._shares = None

    def correlate(self, signature, exponents, shares_):
        """
        Generate masks for the given signature from the existing mask exponents.
        """
        self._shares = shares_
        self._masks = {}
        for (term_index, factor_count) in enumerate(signature):
            factors = [
                self.g ** int(l)
                for l in _shares(
                    -int(exponents[term_index]),
                    self.q * 2,
                    factor_count
                )
            ]
            self._masks[(term_index, -1)] = self.g ** int(exponents[term_index])
            for factor_index in range(factor_count):
                self._masks[(term_index, factor_index)] = factors[factor_index]

    def masks(self, coords_from_dealer) -> dict[tuple[int, int], mod]:
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
        mfs = functools.reduce(_merge, mfss)

        # Compute this node's share of the overall sum of products.
        # pylint: disable=consider-using-generator
        return sum([
            self._shares[term_index]
            *
            _prod(
                mfs[(term_index, factor_index)]
                for factor_index in range(factor_quantity)
            )
            for (term_index, factor_quantity) in enumerate(signature)
        ])

def preprocessing(signature, nodes):
    """
    Simulate a preprocessing phase for the supplied signature and collection
    of nodes.
    """
    (p, q) = (4215209819, 2107604909)
    g = mod(3844384293, p)

    randoms = [
        random.randint(0, (q * 2) - 1)
        for term_index in range(len(signature))
    ]
    node_to_exponent_shares = list(zip(*[
        _shares(randoms[term_index], q * 2, len(nodes))
        for term_index in range(len(signature))
    ]))
    node_to_factor_shares = list(zip(*[
        _shares(int(g ** exponent), p, len(nodes))
        for exponent in randoms
    ]))

    for (i, n) in enumerate(nodes):
        n.correlate(signature, node_to_exponent_shares[i], node_to_factor_shares[i])

def masked_factors(coords_to_values, masks_from_nodes):
    """
    Build up dictionary mapping each coordinate to a value that is
    masked using the product of the masks (from all nodes) at that
    coordinate.
    """
    return {
        coords: value * _prod([
            coords_to_masks[coords]
            for coords_to_masks in masks_from_nodes
        ])
        for (coords, value) in coords_to_values.items()
    }

if __name__ == '__main__':
    doctest.testmod() # pragma: no cover
