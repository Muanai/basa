# BASA: Modern NLP toolkit for Indonesian and regional languages.

BASA helps developers clean and normalize informal Indonesian text with a simple, developer-friendly API.

```python
from basa import quick

quick("GW GKKKK NGERTIII BNGTTTT!!!!!")
# saya tidak mengerti banget!
```

## Features

* Indonesian slang normalization
* Repeated-character reduction (`gkkkk → gk`)
* Conservative typo correction (opt-in)
* Batch processing support
* Pure Python implementation
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

### Future Releases

* Javanese ↔ Indonesian translation
* Sundanese ↔ Indonesian translation
* Indonesian factual consistency evaluation
* Dataset utilities for IndoBERT and IndoBART
* Synthetic data generation for low-resource languages

## License

Released under the MIT License.
