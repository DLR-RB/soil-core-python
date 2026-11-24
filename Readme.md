# SOIL Core in Python

This repository contains the core implementation of SOIL in Python.

## Installation

The recommended way to install is using `pip`:

```bash
pip install git+https://gitlab.gsoc.dlr.de/gitlab/rb/mit/mcs/luna/soil/soil-core-python.git@main
```

Or add it as a dependency in a `pyproject.toml`

```toml
dependencies = [
  "soil-core @ git+https://gitlab.gsoc.dlr.de/gitlab/rb/mit/mcs/luna/soil/soil-core-python.git@main",
]
```

## Tests

To run the tests:

```bash
python -m unittest -v
```

Or run single tests:

```bash
python -m unittest tests.encoding.test_binary.BinaryTests.testTree
```
