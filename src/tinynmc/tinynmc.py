"""
Minimal pure-Python implementation of a secure multi-party computation
(MPC) protocol for evaluating arithmetic sum-of-products expressions via
a non-interactive computation phase.
"""
from __future__ import annotations
from typing import Sequence, Iterable
import doctest
import operator
import functools
import secrets
from modulo import modulo

_DEFAULT_P = 340282366920938463463374607431768196007
_DEFAULT_Q = 170141183460469231731687303715884098003
_DEFAULT_G = 205482397601703717038466705921080247554

def _prod(iterable: Iterable):
    """
    Multiplication aggregation operation (counterpart to ``sum``).
    """
    return functools.reduce(operator.mul, iterable)

def _merge(d: dict, d_: dict) -> dict:
    """
    Binary operation to merge two dictionaries that is backwards-compatible
    with Python 3.7.
    """
    d__ = {}
    d__.update(d)
    d__.update(d_)
    return d__

def _shares(value: modulo, modulus: int, quantity: int) -> Sequence[modulo]:
    """
    Return ``quantity`` additive secret shares (modulo ``modulus``)
    of ``value``.
    """
    shares = []
    for _ in range(quantity - 1):
        # Use rejection sampling to obtain a share value.
        shares.append(modulo(secrets.randbelow(modulus), modulus))

    return [modulo(value, modulus) - sum(shares)] + shares

class node:
    """
    Data structure for maintaining the information associated with a node in
    a protocol instantiation.

    Suppose that a protocol instance involves three contributors (parties
    submitting private input values) and three nodes (parties performing the
    computation). The node objects would be instantiated locally by each
    of the parties performing the computation.

    >>> nodes = [node(), node(), node()]

    Any sum-of-products expression that can be computed can be described by
    a *signature*: a list of integers in which each entry specifies the number
    of factors (*i.e.*, multiplicands) in each term (*i.e.*, addend of the
    overall summation). For example, suppose the expression to be computed is
    ``(1 * 2 * 3) + (4 * 5)``. This would correspond to the signature below
    because the term ``(1 * 2 * 3)`` has three factors and the term ``(4 * 5)``
    has two factors.

    >>> signature = [3, 2]

    All contributors must agree on the signature, and the signature must be
    shared with the nodes. The preprocessing phase that the nodes must execute
    (using some existing MPC protocol such as
    `SPDZ <https://eprint.iacr.org/2011/535>`__) can be simulated using the
    :obj:`preprocess` function.
    
    >>> preprocess(signature, nodes)

    The contributors must also agree on which factors in the sum-of-products
    each of them is submitting to the overall computation. In this example,
    we assume that each factor in the workflow is contributed by one of three
    contributors **a**, **b**, or **c**, with the ownership pattern
    ``(a * b * c) + (a * b)``. Each factor is referenced by the contributors
    according to its ``(term_index, factor_index)`` coordinate within the
    overall expression: ``((0, 0) * (0, 1)) + ((1, 0) * (1, 1) * (1, 2))``.

    Agreeing on the above, each contributor can then request from the nodes
    the multiplicative shares of the masks it must use to protect its values
    (organized by the coordinates of the inputs to which they correspond).

    >>> coords_to_values_a = {(0, 0): 1, (1, 0): 4}
    >>> masks_from_nodes_a = [node.masks(coords_to_values_a.keys()) for node in nodes]

    >>> coords_to_values_b = {(0, 1): 2, (1, 1): 5}
    >>> masks_from_nodes_b = [node.masks(coords_to_values_b.keys()) for node in nodes]

    >>> coords_to_values_c = {(0, 2): 3}
    >>> masks_from_nodes_c = [node.masks(coords_to_values_c.keys()) for node in nodes]

    Each node can then mask its input values using the masks via the
    :obj:`masked_factors` function. This function organizes the process of
    masking the input values at each coordinate using the mask for that
    coordinate. The output of this function consists of the *masked factors*
    that are safe to broadcast to the nodes.

    >>> masked_factors_a = masked_factors(coords_to_values_a, masks_from_nodes_a)
    >>> masked_factors_b = masked_factors(coords_to_values_b, masks_from_nodes_b)
    >>> masked_factors_c = masked_factors(coords_to_values_c, masks_from_nodes_c)

    Then, each contributor broadcasts *all* of its masked factors to *every* node.
    Every node receives *all* the masked factors from *all* the contributors.
    Then, each node can locally perform its computation to obtain its share of
    the overall result.

    >>> broadcast = [masked_factors_a, masked_factors_b, masked_factors_c]
    >>> result_share_at_node_0 = nodes[0].compute(signature, broadcast)
    >>> result_share_at_node_1 = nodes[1].compute(signature, broadcast)
    >>> result_share_at_node_2 = nodes[2].compute(signature, broadcast)

    Finally, the result can be reconstructed via simple summation from the
    result shares received from the nodes.

    >>> int(sum([result_share_at_node_0, result_share_at_node_1, result_share_at_node_2]))
    26
    """
    def __init__(self: node):
        """
        Instantiate an object that maintains the state of a node.
        """
        self.q = _DEFAULT_Q
        self.p = _DEFAULT_P
        self.g = modulo(_DEFAULT_G, self.p)
        self._masks = None
        self._shares = None

    def correlate(
            self: node,
            signature: Sequence[int],
            exponents: Sequence[modulo],
            shares_: Sequence[modulo]
        ):
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

    def masks(
            self: node,
            coordinates_from_contributor: Sequence[tuple[int, int]]
        ) -> dict[tuple[int, int], modulo]:
        """
        Return a dictionary mapping a set of ``(term_index, factor_index)``
        coordinates to their corresponding masks.
        """
        return {
            coordinates: self._masks[coordinates]
            for coordinates in coordinates_from_contributor
        }

    def compute(
            self: node,
            signature: Sequence[int],
            masked_factors_from_contributors: Sequence[dict[tuple[int, int], modulo]]
        ):
        """
        Compute a secret share of the result (of evaluating the expression).
        """
        # Combine all submitted (coordinate, masked factor) pair dictionaries
        # into a single dictionary.
        # pylint: disable=redefined-outer-name
        masked_factors: dict[tuple[int, int], modulo] = \
            functools.reduce(_merge, masked_factors_from_contributors)

        # Compute this node's share of the overall sum of products.
        # pylint: disable=consider-using-generator
        return sum([
            self._shares[term_index]
            *
            _prod(
                masked_factors[(term_index, factor_index)]
                for factor_index in range(factor_quantity)
            )
            for (term_index, factor_quantity) in enumerate(signature)
        ])

def preprocess(signature: Sequence[int], nodes: Sequence[node]):
    """
    Simulate a preprocessing phase for the supplied signature and collection
    of nodes.
    """
    q = _DEFAULT_Q
    p = _DEFAULT_P
    g = modulo(_DEFAULT_G, p)

    mask_exponent = [
        secrets.randbelow(q * 2) # Use rejection sampling.
        for term_index in range(len(signature))
    ]
    node_to_exponent_shares = list(zip(*[
        _shares(mask_exponent[term_index], q * 2, len(nodes))
        for term_index in range(len(signature))
    ]))
    node_to_mask_shares = list(zip(*[
        _shares(int(g ** exponent), p, len(nodes))
        for exponent in mask_exponent
    ]))

    for (i, n) in enumerate(nodes):
        n.correlate(
            signature,
            node_to_exponent_shares[i],
            node_to_mask_shares[i]
        )

def masked_factors(
        coordinates_to_values: dict[tuple[int, int], int],
        masks_from_nodes: Iterable[dict[tuple[int, int], modulo]]
    ) -> dict[tuple[int, int], modulo]:
    """
    Build up dictionary mapping each coordinate to a value that is
    masked using the product of the masks (from all nodes) at that
    coordinate.
    """
    return {
        coordinates: value * _prod([
            coordinates_to_masks[coordinates]
            for coordinates_to_masks in masks_from_nodes
        ])
        for (coordinates, value) in coordinates_to_values.items()
    }

if __name__ == '__main__':
    doctest.testmod() # pragma: no cover
