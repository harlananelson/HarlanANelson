# addpage

A simple Python package to add new .qmd files to Quarto's _quarto.yml navigation.

## Installation

```bash
pip install -e .
```

## Usage

From the command line:

```bash
addpage new_page.qmd
```

In Python:

```python
from addpage import add_qmd_to_yaml

add_qmd_to_yaml("new_page.qmd")
```

For more options, use:

```bash
addpage --help
```