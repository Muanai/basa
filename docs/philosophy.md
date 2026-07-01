# Design Philosophy

BASA is built around a simple principle:

> Conservative defaults, developer-friendly APIs, and practical tools for Indonesian NLP.

The project prioritizes reliability and maintainability over rapid feature expansion.

---

## Conservative by Default

Text normalization can be destructive.

Proper nouns, technical terms, abbreviations, and domain-specific vocabulary should not be modified without explicit user intent.

For this reason:

```python
normalize(
    text,
    apply_typo=False
)
```

Typo correction is always opt-in.

---

## One-Line APIs

Most users should not need to read extensive documentation before becoming productive.

The simplest workflow should look like this:

```python
from basa import quick

quick("gw gk ngerti bngtttt")
```

BASA aims to provide sensible defaults while still allowing advanced configuration when necessary.

---

## Indonesian First

BASA focuses primarily on Indonesian language processing.

Many global NLP tools are designed for English-first workflows, leaving Indonesian-specific problems underrepresented.

Examples include:

* Social media slang normalization
* Repeated-character reduction
* Regional language support
* Indonesian evaluation pipelines

The project addresses these problems directly.

---

## Regional Language Support

Indonesia has hundreds of local languages, many of which remain underrepresented in modern NLP ecosystems.

Future BASA releases aim to support:

* Javanese
* Sundanese
* Additional regional languages

The long-term goal is practical tooling rather than academic benchmarks alone.

---

## Explicit Over Implicit

BASA prefers explicit configuration over hidden behavior.

For example:

```python
normalize(
    text,
    apply_typo=True,
    lowercase=False
)
```

Users should always understand which transformations are being applied to their data.

---

## Stable Public APIs

Breaking changes are introduced cautiously.

The public API is intentionally small:

```python
from basa import (
    normalize,
    quick,
    slang,
    typo,
)
```

A small API surface is easier to maintain, document, and support over time.

---

## Incremental Growth

BASA follows an incremental development model.

Instead of shipping many unfinished features, the project focuses on:

* Strong testing
* Good documentation
* Stable releases
* Conservative defaults
* Real-world usability

The objective is not to become the largest NLP framework, but to become a dependable toolkit for Indonesian and regional language processing.
