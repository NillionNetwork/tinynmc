=======
tinynmc
=======

Minimal pure-Python implementation of a secure multi-party computation (MPC) protocol for evaluating arithmetic sum-of-products expressions via a non-interactive computation phase.

|pypi|

.. |pypi| image:: https://badge.fury.io/py/tinynmc.svg
   :target: https://badge.fury.io/py/tinynmc
   :alt: PyPI version and link.

Installation and Usage
----------------------

This library is available as a `package on PyPI <https://pypi.org/project/tinynmc>`__:

.. code-block:: bash

    python -m pip install tinynmc

The library can be imported in the usual way:

.. code-block:: python

    import tinynmc

Basic Example
^^^^^^^^^^^^^

This example involves three dealers (parties contributing data) and three nodes (computation parties):

.. code-block:: python

    >>> nodes = [node(3), node(3), node(3)]

The overall expression being computed is ``(1 * 2 * 3) + (4 * 5)``. First, the dealers agree on a workflow signature. The signature lists the number of factors in each term:

.. code-block:: python

    >>> signature = [3, 2]

The signature is shared with every node so that it can perform its preprocessing steps. Next, each factor in the workflow is contributed by one of three dealers **A**, **B**, or **C**, with the ownership pattern (**A** * **B** * **C**) + (**A** * **B**). Each factor is tracked according to its ``(term_index, factor_index)`` coordinate: ``((0, 0) * (0, 1)) + ((1, 0) * (1, 1) * (1, 2))``.

Each dealer converts its coordinate-value pairs into particles by (1) requesting the multiplicative masks for each coordinate, and (2) masking its factors at each coordinate using those masks:

.. code-block:: python

    >>> coords_to_values_a = {(0, 0): 1, (1, 0): 4}
    >>> masks_from_nodes_to_a = [node.masks(signature, coords_to_values_a.keys()) for node in nodes]
    >>> masked_factors_a = particles(coords_to_values_a, masks_from_nodes_to_a)

    >>> coords_to_values_b = {(0, 1): 2, (1, 1): 5}
    >>> masks_from_nodes_to_b = [node.masks(signature, coords_to_values_b.keys()) for node in nodes]
    >>> masked_factors_b = particles(coords_to_values_b, masks_from_nodes_to_b)

    >>> coords_to_values_c = {(0, 2): 3}
    >>> masks_from_nodes_to_c = [node.masks(signature, coords_to_values_c.keys()) for node in nodes]
    >>> masked_factors_c = particles(coords_to_values_c, masks_from_nodes_to_c)


Each dealer sends all of its particles to every node, so every node receives all the masks from all the dealers:

.. code-block:: python

    >>> masked_factors_received = [masked_factors_a, masked_factors_b, masked_factors_c]

Every node computes its result share:

.. code-block:: python

    >>> result_share_at_node_0 = nodes[0].compute(signature, masked_factors_received)
    >>> result_share_at_node_1 = nodes[1].compute(signature, masked_factors_received)
    >>> result_share_at_node_2 = nodes[2].compute(signature, masked_factors_received)

The result can be reconstructed via summation from the result shares received from the nodes:

.. code-block:: python

    >>> sum([result_share_at_node_0, result_share_at_node_1, result_share_at_node_2])

Development
-----------

Documentation
^^^^^^^^^^^^^
The documentation can be generated automatically from the source files using `Sphinx <https://www.sphinx-doc.org>`__:

.. code-block:: bash

    python -m pip install .[docs]
    cd docs
    sphinx-apidoc -f -E --templatedir=_templates -o _source .. && make html

Testing
^^^^^^^

Contributions
^^^^^^^^^^^^^
In order to contribute to the source code, open an issue or submit a pull request on the `GitHub page <https://github.com/nillion-oss/tinynmc>`__ for this library.

Versioning
^^^^^^^^^^
The version number format for this library and the changes to the library associated with version number increments conform with `Semantic Versioning 2.0.0 <https://semver.org/#semantic-versioning-200>`__.

Publishing
^^^^^^^^^^
This library can be published as a `package on PyPI <https://pypi.org/project/tinynmc>`__ by a package maintainer. First, install the dependencies required for packaging and publishing:

.. code-block:: bash

    python -m pip install .[publish]

Ensure that the correct version number appears in ``pyproject.toml``. Create and push a tag for this version (replacing ``?.?.?`` with the version number):

.. code-block:: bash

    git tag ?.?.?
    git push origin ?.?.?

Remove any old build/distribution files. Then, package the source into a distribution archive:

.. code-block:: bash

    rm -rf build dist src/*.egg-info
    python -m build --sdist --wheel .

Finally, upload the package distribution archive to `PyPI <https://pypi.org>`__:

.. code-block:: bash

    python -m twine upload dist/*
