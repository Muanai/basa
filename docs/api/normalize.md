# normalize()

The primary normalization API in BASA.

`normalize()` provides fine-grained control over the entire normalization pipeline, including slang conversion, typo correction, punctuation reduction, and case handling.

---

## Import

```python
from basa import normalize
```

---

## Basic Usage

```python
normalize(
    "GW GKKKK NGERTIII BNGTTTT!!!!!"
)
```

Output:

```python
'saya tidak mengerti banget!'
```

---

## Function Signature

```python
normalize(
    text,
    apply_slang=True,
    apply_typo=False,
    lowercase=True,
    normalize_punctuation=True,
    normalize_whitespace=True,
    mode="formal",
)
```

---

## Parameters

### `text`

Type:

```python
str | list[str]
```

The input text or batch of texts to normalize.

---

### `apply_slang`

Default:

```python
True
```

Applies:

* slang dictionary replacement
* repeated-character reduction

Example:

```python
normalize(
    "gw gk ngerti",
    apply_slang=False
)
```

Output:

```python
'gw gk ngerti'
```

---

### `apply_typo`

Default:

```python
False
```

Enables Levenshtein-based typo correction.

A vocabulary must be loaded beforehand via `typo.load_default_vocab()` or `typo.add_to_vocab()`:

```python
from basa import typo

typo.load_default_vocab()

# Or supply domain-specific words:
typo.add_to_vocab({
    "makan",
    "minum"
})
```

---

### `lowercase`

Default:

```python
True
```

Convert text to lowercase before normalization.

Example:

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

### `normalize_punctuation`

Default:

```python
True
```

Collapses repeated punctuation:

```text
!!!!! → !
????? → ?
..... → .
```

---

### `normalize_whitespace`

Default:

```python
True
```

Collapses multiple spaces and trims leading/trailing whitespace.

---

### `mode`

Type:

```python
Literal["formal", "concise"]
```

Default:

```python
"formal"
```

Controls slang replacement style:

* `"formal"` — uses standard, readable Indonesian expansions (e.g. `mager` → `malas gerak`, `gercep` → `gerak cepat`).
* `"concise"` — prefers shorter single-word equivalents where available (e.g. `mager` → `malas`, `bgt` → `sekali`, `gercep` → `cepat`).

Raises `ValueError` if given any other value.

Example:

```python
normalize("gw mager bgt gercep", mode="concise")
# 'saya malas sekali cepat'
```

---

## Batch Processing

```python
normalize([
    "gw gk ngerti",
    "udh makan blm?"
])
```

Output:

```python
[
    'saya tidak mengerti',
    'sudah makan belum?'
]
```

---

## Design Philosophy

`normalize()` follows several principles:

* Conservative defaults
* Explicit configuration
* Predictable behavior
* Stable public APIs
* Production-friendly preprocessing

For most users, `quick()` is recommended as the simpler entry point.
