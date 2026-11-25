# SOIL Core in Python

This repository contains the core implementation of SOIL in Python.
It provides the definitions, protocols and commonly used functions to build SOIL components.

For more information about the concepts, see the [SOIL documentation repository](https://github.com/DLR-RB/soil-documentation).

## Purpose

SOIL is a component model for building modular, network-transparent data systems.
This core library defines the abstractions that make it possible to compose components
that exchange *timestamped values* over *hierarchical paths*, whether in-process or across
a network.

In particular, this core library provides:

- **Primitives**: values, paths, samples, timestamps and sample trees
- **Storage** interface definitions and an in-memory database
- **Components** to track subscriptions (both from external components and code)
- **Request tracking** and timeout handling for network calls
- **Access control** interfaces
- **Transport layer** definitions and encoding interfaces
- **Connection adapters** to expose local components over connections, and to use remote
  components as if they were local

## Installation

The recommended way to install is using `pip` or `uv`:

```bash
pip install git+https://github.com/DLR-RB/soil-core-python.git@main
```

Or add it as a dependency in a `pyproject.toml`

```toml
dependencies = [
  "soil-core @ git+https://github.com/DLR-RB/soil-core-python.git@main",
]
```

## Usage

An extensive documentation with examples and best practices is available in the [documentation](documentation/best_practice.md).

## Tests

To run the tests:

```bash
python -m unittest
```

Or run single tests:

```bash
python -m unittest tests.encoding.test_binary.BinaryTests.testTree
```

## Copyright and license

### Copyright

SOIL Core Implementation in Python (soil-core-python)

Copyright 2026 DLR - Deutsches Zentrum für Luft- und Raumfahrt e.V.

This product was developed at DLR - GSOC (German Space Operations Center at the German Aerospace Center DLR, https://www.dlr.de/).

### License

This repository is provided under the [MIT license](LICENSE.txt).

## Contributing

Contributions to this project are welcome.
You may open issues, fix or expand documentation, provide new functionality or create more and better tests.
If you have a minor contribution you can open a pull request right away.
For any major contribution please open an issue first or discuss with the repository maintainer.
Please also note that you need to fill out and sign a [contributor license agreement](SOIL%20Individual%20Contributor%20Agreement.pdf).
