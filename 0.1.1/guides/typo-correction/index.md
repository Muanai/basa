# Typo Correction

BASA provides conservative typo correction based on Levenshtein distance.

Unlike many normalization systems, typo correction is disabled by default.

```python
from basa import normalize

normalize(
    "gw mkan",
    apply_typo=False
)
```

Output:

```python
"saya mkan"
```

---

## Why Is Typo Correction Opt-In?

Automatic typo correction can damage:

* Proper nouns
* Technical terms
* Acronyms
* Domain-specific vocabulary

For example:

```text
xgboost
lightgbm
tensorflow
jokowi
telkomsel
```

To avoid destructive behavior, BASA requires explicit user consent before applying typo correction.

---

## Loading a Vocabulary

Before enabling typo correction, add words to the vocabulary.

```python
from basa import typo

typo.add_to_vocab({
    "makan",
    "minum",
    "berangkat"
})
```

---

## Correcting Individual Words

```python
typo.correct("mkan")
```

Output:

```python
"makan"
```

---

## Correcting Full Sentences

```python
from basa import normalize

normalize(
    "gw mkan dulu",
    apply_typo=True
)
```

Output:

```python
"saya makan dulu"
```

---

## Custom Maximum Distance

The typo engine uses Levenshtein distance.

By default, the maximum correction distance is conservative.

You can also use the lower-level API directly:

```python
typo.correct(
    "mkan",
    max_dist=2
)
```

---

## Protected Vocabulary

BASA automatically protects normalized slang outputs from being modified by the typo corrector.

For example:

```python
"gk"
→ "tidak"
```

The word `"tidak"` will never be reinterpreted as a typo candidate.

This prevents interactions between the slang and typo pipelines from producing incorrect results.

---

## Recommended Workflow

For most use cases, `quick()` is the recommended entry point:

```python
from basa import quick

quick("gw gk ngerti bngtttt")
```

This approach provides safe, zero-configuration normalization for informal Indonesian text.

---

For domain-specific datasets, load your own vocabulary before enabling typo correction:

```python
from basa import normalize, typo

typo.add_to_vocab({
    "xgboost",
    "lightgbm",
    "tensorflow",
    "fintech",
    "telkomsel",
})

normalize(
    "gw belajar xgboosst",
    apply_typo=True,
)
```

Adding domain-specific terms helps reduce unintended corrections and gives you more control over the normalization pipeline.

---

## Best Practices

When using typo correction, we recommend:

* Load a vocabulary that matches your domain.
* Keep `apply_typo=False` unless spelling correction is required.
* Add technical terms, company names, and acronyms to the vocabulary.
* Review normalization outputs before using them in production workflows.

BASA intentionally favors conservative behavior over aggressive correction.

---

## Future Directions

Potential areas for future development include:

* Frequency-based candidate ranking
* Optional domain-specific dictionaries
* Faster search structures for large vocabularies
* Context-aware correction mechanisms
* Support for regional languages

These ideas are exploratory and may evolve as BASA grows and receives community feedback.

The current implementation prioritizes simplicity, transparency, and predictable behavior.
