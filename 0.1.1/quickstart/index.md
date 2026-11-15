# Quick Start

BASA provides two main entry points:

* `quick()` for zero-configuration usage
* `normalize()` for fine-grained control

---

## Quick Normalization

The simplest way to clean Indonesian informal text:

```python
from basa import quick

quick("gw gk ngerti bngtttt sihhhh!!!")
```

Output:

```python
'saya tidak mengerti banget sih!'
```

---

## Fine-Grained Control

Use `normalize()` when you need more control over the pipeline:

```python
from basa import normalize

normalize(
    "GW GKKKK NGERTIII BNGTTTT!!!!!",
    apply_slang=True,
    apply_typo=False,
    lowercase=True,
    normalize_punctuation=True,
)
```

Output:

```python
'saya tidak mengerti banget!'
```

---

## Batch Processing

BASA supports lists of strings out of the box:

```python
texts = [
    "gw gk ngerti",
    "udh makan blm?"
]

normalize(texts)
```

Output:

```python
[
    'saya tidak mengerti',
    'sudah makan belum?'
]
```

---

## Preserving Original Casing

Disable automatic lowercasing when case information matters:

```python
normalize(
    "Jokowi pergi ke Jakarta",
    lowercase=False
)
```

Output:

```python
'Jokowi pergi ke Jakarta'
```

---

## Typo Correction

Typo correction is disabled by default.

Load your vocabulary first:

```python
from basa import normalize, typo

typo.add_to_vocab({
    "makan",
    "minum"
})
```

Then enable typo correction:

```python
normalize(
    "gw mkan",
    apply_typo=True
)
```

Output:

```python
'saya makan'
```

---

## Why Is Typo Correction Opt-In?

Typo correction can accidentally modify:

* technical terms
* proper nouns
* abbreviations
* domain-specific vocabulary

To prevent destructive transformations, BASA keeps typo correction disabled by default.

---

## Next Steps

* Read the API Reference for detailed documentation.
* Explore the Guides section for practical NLP workflows.
* Check the Roadmap to see upcoming features.
