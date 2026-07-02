# Cleaning Indonesian Social Media Text

Indonesian social media text often contains:

* Slang words
* Character elongation (`gkkkk`, `bangetttt`)
* Informal abbreviations
* Repeated punctuation

BASA is designed specifically to handle these patterns.

---

## Basic Example

```python
from basa import quick

quick(
    "GW GKKKK NGERTIII BNGTTTT!!!!!"
)
```

Output:

```python
"saya tidak mengerti banget!"
```

---

## Common Transformations

| Original | Normalized       |
| -------- | ---------------- |
| gw       | saya             |
| gk       | tidak            |
| udh      | sudah            |
| bgt      | banget           |
| otw      | dalam perjalanan |
| makasih  | terima kasih     |

---

## Character Reduction

Repeated characters are automatically normalized.

```python
quick(
    "sihhhhhhh"
)
```

Output:

```python
"sih"
```

Another example:

```python
quick(
    "gkkkk"
)
```

Output:

```python
"tidak"
```

---

## Punctuation Normalization

Repeated punctuation is also simplified.

```python
quick(
    "serius??????"
)
```

Output:

```python
"serius?"
```

---

## Cleaning Twitter or Instagram Data

```python
tweets = [
    "gw gk ngerti bngtttt",
    "udh makan blm????",
    "otw kampus nihhhh"
]

cleaned = quick(tweets)
```

Output:

```python
[
    "saya tidak mengerti banget",
    "sudah makan belum?",
    "dalam perjalanan kampus nih"
]
```

---

## Why Social Media Normalization Matters

Many Indonesian NLP models are trained on formal text.

Social media data introduces challenges such as:

* Informal abbreviations
* Non-standard spelling
* Character elongation
* Regional expressions

Normalization can improve:

* Text classification
* Sentiment analysis
* Topic modeling
* Named entity recognition
* Summarization pipelines

BASA provides lightweight preprocessing utilities specifically for these Indonesian-language scenarios.
