# Contributing to BASA

Thank you for your interest in contributing to **BASA**! Contributions of all sizes—bug reports, slang and abbreviation additions, typo vocabulary improvements, performance work, and documentation—are welcome.

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Ways to Contribute

* **Bug Reports:** Open an issue on [GitHub Issues](https://github.com/Muanai/basa/issues) with the exact input string, expected output, actual output, and BASA version.
* **Slang & Abbreviation Entries:** Propose missing colloquial Indonesian words or standard abbreviations in [`src/basa/core/slang.py`](src/basa/core/slang.py).
* **Core Engine & Typo Correction:** Improvements to normalization accuracy, SymSpell indexing, memory footprint, or documentation.

Please open an issue first to discuss large architectural changes before submitting a pull request.

## Development Setup

BASA targets Python `>=3.10` and uses [`uv`](https://docs.astral.sh/uv/) for dependency and environment management:

```bash
git clone https://github.com/Muanai/basa.git
cd basa
uv sync --extra dev
```

To build documentation locally, also include the `docs` extra:

```bash
uv sync --extra dev --extra docs
uv run mkdocs serve
```

## Project Design Guardrails

When contributing code or dictionary changes, keep these core constraints intact:

1. **Zero Core Dependencies:** `src/basa/core/` must use only the Python standard library (`dependencies = []` in `pyproject.toml`). Optional integrations belong under `[project.optional-dependencies]`.
2. **Conservative Defaults (`ONER = 0`):** Default `normalize()` / `quick()` must never corrupt clean standard Indonesian text, URLs, domains (`www.*`), emails, social handles, or English technical loanwords. Destructive operations such as typo correction remain opt-in (`apply_typo=False` by default).
3. **No Duplicate Dictionary Keys:** Place new entries in the single most appropriate category dict inside [`src/basa/core/slang.py`](src/basa/core/slang.py). `tests/test_normalize.py` enforces zero duplicate keys across category dicts via AST inspection.
4. **Strict Typing & Formatting:** Public APIs must pass `mypy --strict` and `ruff` checks (`line-length = 88`, Python `3.10` syntax).

## Running Checks Before Opening a PR

Run all quality, type, and test checks locally:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src/basa
uv run pytest -m "not slow"
uv run pytest -m slow
```

If your change affects normalization behavior or dictionaries, verify against the independent `basa-evals` release gate as well:

```bash
uv run --with "basa-evals>=0.1.1" basa-eval run --suite pilot_210 --system basa-full
```

## Pull Request Process

1. Create a focused branch from `main`.
2. Add unit or regression tests under `tests/` for any bug fix or new behavior.
3. Update relevant docs under `docs/` or `README.md` when public behavior changes.
4. Ensure all local checks and CI workflows pass before requesting review.
