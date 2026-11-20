# Batch Processing

BASA supports batch processing out of the box.

Simply pass a list of strings to `normalize()` or `quick()`.

---

## Basic Example

```python
from basa import normalize

texts = [
    "gw gk ngerti",
    "udh makan blm?",
    "otw ke kampus"
]

normalize(texts)
```

Output:

```python
[
    "saya tidak mengerti",
    "sudah makan belum?",
    "dalam perjalanan ke kampus"
]
```

---

## Using `quick()`

The `quick()` API also supports batch inputs.

```python
from basa import quick

quick([
    "gw bngtt capek",
    "dia lg dimana?"
])
```

Output:

```python
[
    "saya banget capek",
    "dia lagi dimana?"
]
```

---

## Processing Pandas DataFrames

BASA works naturally with pandas.

```python
import pandas as pd

from basa import normalize

df = pd.DataFrame({
    "tweet": [
        "gw gk ngerti",
        "udh makan blm?"
    ]
})

df["clean_text"] = normalize(
    df["tweet"].tolist()
)
```

---

## Processing Large Datasets

For larger datasets, process data in batches instead of loading everything into memory at once.

```python
BATCH_SIZE = 1000

for i in range(0, len(texts), BATCH_SIZE):
    batch = texts[i:i + BATCH_SIZE]

    cleaned = normalize(batch)

    # save or process results
```

---

## Design Notes

Batch processing in BASA guarantees:

* Input order is preserved.
* Output length matches input length.
* Empty strings remain unchanged.
* Invalid values are safely ignored by the normalization pipeline.

These guarantees help make BASA predictable in production preprocessing workflows.
