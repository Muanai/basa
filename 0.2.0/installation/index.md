# Installation

## Requirements

BASA supports:

* Python 3.10 or newer

## Install from PyPI

```bash
pip install basa
```

## Verify Installation

Open a Python shell and run:

```python
from basa import quick

quick("gw gk ngerti")
```

Expected output:

```python
'saya tidak mengerti'
```

## Development Installation

Clone the repository:

```bash
git clone https://github.com/muanai/basa.git
cd basa
```

Install development dependencies using uv:

```bash
uv sync --extra dev
```

Run tests:

```bash
uv run pytest
```

Run Ruff:

```bash
uv run ruff check .
uv run ruff format .
```

Build the package:

```bash
uv build
```
