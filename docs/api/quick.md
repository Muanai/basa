# quick()

Zero-configuration text normalization.

`quick()` is the simplest way to use BASA and is recommended for most users.

Internally, it is a thin wrapper around `normalize()` with all default settings enabled.

---

## Import

```python
from basa import quick
```

---

## Basic Usage

```python
quick(
    "gw gk ngerti bngtttt sihhhh!!!"
)
```

Output:

```python
'saya tidak mengerti banget sih!'
```

---

## Function Signature

```python
quick(text)
```

---

## Supported Inputs

### Single String

```python
quick(
    "udh makan blm?"
)
```

Output:

```python
'sudah makan belum?'
```

---

### Batch Processing

```python
quick([
    "gw gk ngerti",
    "otw kampus"
])
```

Output:

```python
[
    'saya tidak mengerti',
    'dalam perjalanan kampus'
]
```

---

## Default Behavior

`quick()` always uses:

```python
normalize(
    text,
    apply_slang=True,
    apply_typo=False,
    lowercase=True,
    normalize_punctuation=True,
    normalize_whitespace=True,
)
```

---

## When Should I Use `quick()`?

Use `quick()` when:

* Cleaning social media text
* Building quick NLP prototypes
* Working with Indonesian informal language
* You do not need custom normalization settings

For advanced use cases, use `normalize()` directly.

---

## Design Philosophy

The goal of `quick()` is simple:

> Most users should only need one line of code.

```python
from basa import quick

quick(text)
```
