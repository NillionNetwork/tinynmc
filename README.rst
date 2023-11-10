=======
tinynmc
=======

Minimal pure-Python implementation of a secure multi-party computation (MPC) `protocol for evaluating arithmetic sum-of-products expressions <https://nillion.pub/sum-of-products-lsss-non-interactive.pdf>`__ via a non-interactive computation phase.

|pypi| |readthedocs| |actions| |coveralls|

.. |pypi| image:: https://badge.fury.io/py/tinynmc.svg
   :target: https://badge.fury.io/py/tinynmc
   :alt: PyPI version and link.

.. |readthedocs| image:: https://readthedocs.org/projects/tinynmc/badge/?version=latest
   :target: https://tinynmc.readthedocs.io/en/latest/?badge=latest
   :alt: Read the Docs documentation status.

.. |actions| image:: https://github.com/nillion-oss/tinynmc/workflows/lint-test-cover-docs/badge.svg
   :target: https://github.com/nillion-oss/tinynmc/actions/workflows/lint-test-cover-docs.yml
   :alt: GitHub Actions status.

.. |coveralls| image:: https://coveralls.io/repos/github/nillion-oss/tinynmc/badge.svg?branch=main
   :target: https://coveralls.io/github/nillion-oss/tinynmc?branch=main
   :alt: Coveralls test coverage summary.

Installation and Usage
----------------------

This library is available as a `package on PyPI <https://pypi.org/project/tinynmc>`__:

.. code-block:: bash

    python -m pip install tinynmc

The library can be imported in the usual way:

.. code-block:: python

    import tinynmc
    from tinynmc import *

Basic Example
^^^^^^^^^^^^^

This example involves three contributors ``a``, ``b``, and ``c`` (parties submitting private input values) and three nodes ``0``, ``1``, and ``2`` (parties performing a computation):

.. code-block:: python

    >>> nodes = [node(), node(), node()]

The overall sum-of-products expression being computed is ``(1 * 2 * 3) + (4 * 5)``. First, the contributors agree on a workflow signature. The signature lists the number of factors in each term:

.. code-block:: python

    >>> signature = [3, 2]

The signature must be shared with every node so that the nodes can collectively perform the preprocessing phase (this can be accomplished using any MPC protocol that supports multiplication of secret-shared values, such as the `SPDZ <https://eprint.iacr.org/2011/535>`__ protocol that is implemented as part of `TinySMPC <https://github.com/kennysong/tinysmpc>`__ library):

.. code-block:: python

    >>> preprocess(signature, nodes)

Next, each factor in the workflow is contributed by one of three contributors **a**, **b**, or **c**, with the ownership pattern ``(a * b * c) + (a * b)``. Each factor is referenced by the contributors according to its ``(term_index, factor_index)`` coordinate within the overall expression: ``((0, 0) * (0, 1)) + ((1, 0) * (1, 1) * (1, 2))``.

Each contributor can convert its coordinate-value pairs into masked factors by (1) requesting the multiplicative shares of the masks for each coordinate, and (2) masking its factors at each coordinate using those masks:

.. code-block:: python

    >>> coords_to_values_a = {(0, 0): 1, (1, 0): 4}
    >>> masks_from_nodes_a = [node.masks(coords_to_values_a.keys()) for node in nodes]
    >>> masked_factors_a = masked_factors(coords_to_values_a, masks_from_nodes_a)

    >>> coords_to_values_b = {(0, 1): 2, (1, 1): 5}
    >>> masks_from_nodes_b = [node.masks(coords_to_values_b.keys()) for node in nodes]
    >>> masked_factors_b = masked_factors(coords_to_values_b, masks_from_nodes_b)

    >>> coords_to_values_c = {(0, 2): 3}
    >>> masks_from_nodes_c = [node.masks(coords_to_values_c.keys()) for node in nodes]
    >>> masked_factors_c = masked_factors(coords_to_values_c, masks_from_nodes_c)

Each contributor then broadcasts all of its masked factors to every node, so every node receives all of the masked factors from all of the contributors:

.. code-block:: python

    >>> broadcast = [masked_factors_a, masked_factors_b, masked_factors_c]

Then, every node can locally compute its share of the overall result:

.. code-block:: python

    >>> result_share_at_node_0 = nodes[0].compute(signature, broadcast)
    >>> result_share_at_node_1 = nodes[1].compute(signature, broadcast)
    >>> result_share_at_node_2 = nodes[2].compute(signature, broadcast)

Finally, the result can be reconstructed via summation from the result shares received from the nodes:

.. code-block:: python

    >>> int(sum([result_share_at_node_0, result_share_at_node_1, result_share_at_node_2]))
    26

Development
-----------
All installation and development dependencies are fully specified in ``pyproject.toml``. The ``project.optional-dependencies`` object is used to `specify optional requirements <https://peps.python.org/pep-0621>`__ for various development tasks. This makes it possible to specify additional options (such as ``docs``, ``lint``, and so on) when performing installation using `pip <https://pypi.org/project/pip>`__:

.. code-block:: bash

    python -m pip install .[docs,lint]

Documentation
^^^^^^^^^^^^^
The documentation can be generated automatically from the source files using `Sphinx <https://www.sphinx-doc.org>`__:

.. code-block:: bash

    python -m pip install .[docs]
    cd docs
    sphinx-apidoc -f -E --templatedir=_templates -o _source .. && make html

Testing and Conventions
^^^^^^^^^^^^^^^^^^^^^^^
All unit tests are executed and their coverage is measured when using `pytest <https://docs.pytest.org>`__ (see the ``pyproject.toml`` file for configuration details):

.. code-block:: bash

    python -m pip install .[test]
    python -m pytest

Alternatively, all unit tests are included in the module itself and can be executed using `doctest <https://docs.python.org/3/library/doctest.html>`__:

.. code-block:: bash

    python src/tinynmc/tinynmc.py -v

Style conventions are enforced using `Pylint <https://pylint.readthedocs.io>`__:

.. code-block:: bash

    python -m pip install .[lint]
    python -m pylint src/tinynmc

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

Ensure that the correct version number appears in ``pyproject.toml``, and that any links in this README document to the Read the Docs documentation of this package (or its dependencies) have appropriate version numbers. Also ensure that the Read the Docs project for this library has an `automation rule <https://docs.readthedocs.io/en/stable/automation-rules.html>`__ that activates and sets as the default all tagged versions. Create and push a tag for this version (replacing ``?.?.?`` with the version number):

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
