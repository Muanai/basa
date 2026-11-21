# BASA: Modern NLP toolkit for Indonesian and regional languages.

BASA helps developers clean and normalize informal Indonesian text with a simple, developer-friendly API.

```python
from basa import quick

quick("GW GKKKK NGERTIII BNGTTTT!!!!!")
# saya tidak mengerti banget!
```

## Features

* Indonesian slang normalization (`formal` and `concise` modes)
* Repeated-character reduction (`gkkkk → gk`)
* Entity preservation for URLs, domains, emails, handles, and hashtags
* Indexed conservative typo correction (opt-in, with built-in `typo.load_default_vocab()`)
* Batch processing support
* Pure Python implementation (zero core dependencies)
* Developer-friendly API

## Installation

```bash
pip install basa
```

## Quick Example

```python
from basa import normalize

normalize(
    "gw gk ngerti bngtttt sihhhh!!!"
)

# saya tidak mengerti banget sih!
```

## Design Philosophy

BASA follows several core principles:

* **Conservative by default** — destructive operations are opt-in.
* **One-line API** — most users should only need `quick()`.
* **Indonesian-first** — built specifically for Indonesian NLP workflows.
* **Future regional support** — designed to grow toward Javanese, Sundanese, and other local languages.

## Roadmap

### v0.1

* `normalize()`
* `quick()`
* Slang normalization
* Typo correction
* Batch processing

### v0.2

* SymSpell-style delete index (`p50 ~ 1 ms` at 50k vocabulary)
* Built-in core vocabulary via `typo.load_default_vocab()`
* `mode="formal" | "concise"` parameter on `normalize()` and `quick()`
* URL/domain/handle shielding and expanded slang/abbreviation coverage

### Future Releases

* Javanese ↔ Indonesian translation
* Sundanese ↔ Indonesian translation
* Indonesian factual consistency evaluation
* Dataset utilities for IndoBERT and IndoBART
* Synthetic data generation for low-resource languages

## License

Released under the MIT License.
