# typo

Conservative typo correction engine.

The `typo` object provides Levenshtein-based spelling correction with explicit vocabulary management.

Unlike many text normalization systems, BASA requires users to opt in to typo correction.

---

## Import

```python
from basa import typo
```

---

## Loading a Vocabulary

Before using typo correction, add words to the vocabulary.

```python
typo.add_to_vocab({
    "makan",
    "minum",
    "berangkat"
})
```

---

## Correcting Individual Words

```python
typo.correct(
    "mkan"
)
```

Output:

```python
'makan'
```

---

## Correcting Sentences

```python
typo.correct_text(
    "saya mkan dulu"
)
```

Output:

```python
'saya makan dulu'
```

---

## Custom Maximum Distance

```python
typo.correct(
    "mkan",
    max_dist=2
)
```

The default behavior is intentionally conservative to avoid overcorrection.

---

## Protected Vocabulary

BASA automatically protects normalized slang outputs from typo correction.

Example:

```text
gk
↓
tidak
```

The word `"tidak"` is never treated as a typo candidate, preventing interactions between normalization stages.

---

## Vocabulary Management

Add new words:

```python
typo.add_to_vocab({
    "tensorflow",
    "lightgbm",
    "xgboost"
})
```

This is particularly useful for:

* Technical datasets
* Financial documents
* Domain-specific NLP pipelines

---

## Design Philosophy

The typo engine follows several principles:

* Explicit user control
* Conservative corrections
* Domain adaptability
* Predictable behavior
* Minimal surprises

The long-term roadmap includes:

* Frequency-based ranking
* BK-tree acceleration
* Context-aware corrections
* Regional language support
