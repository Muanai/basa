# slang

Indonesian slang normalization engine.

The `slang` object powers BASA's informal text preprocessing, including slang replacement and repeated-character reduction.

---

## Import

```python
from basa import slang
```

---

## Basic Usage

```python
slang.normalize(
    "gw gkkkk ngerti bngtttt"
)
```

Output:

```python
'saya tidak mengerti banget'
```

---

## Character Reduction

Repeated characters are automatically simplified.

```python
slang.normalize(
    "sihhhhhhh"
)
```

Output:

```python
'sih'
```

---

## Dictionary-Based Replacement

```python
slang.normalize(
    "udh makan blm?"
)
```

Output:

```python
'sudah makan belum?'
```

---

## Inspecting the Dictionary

You can inspect the supported slang words and their standard replacements, or count the total number of entries:

```python
# Get all supported words (alphabetically sorted)
words = slang.supported_words()

print(words["gw"])
# 'saya'
print(words["gk"])
# 'tidak'

# Count total entries
print(len(slang))
# 1308
```

---

## Adding Custom Entries

Users can extend the dictionary dynamically.

```python
slang.add({
    "wfo": "work from office",
    "wfh": "work from home"
})
```

Example:

```python
slang.normalize(
    "hari ini wfh"
)
```

Output:

```python
'hari ini work from home'
```

---

## Dictionary Coverage

BASA currently provides:

* General conversation slang
* Social media abbreviations
* Internet expressions
* Common Indonesian informal forms

Future releases may include:

* Javanese slang
* Sundanese slang
* Regional dictionaries
* Domain-specific vocabularies

---

## Design Philosophy

The slang engine prioritizes:

* Conservative replacements
* Explicit mappings
* Fast regex-based processing
* Developer extensibility
* Indonesian-first normalization
