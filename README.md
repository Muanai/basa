# BASA

**Modern NLP preprocessing for Indonesian and regional languages.**

BASA is a lightweight, zero-dependency preprocessing library designed for real-world Indonesian text — the kind found on Twitter/X, TikTok, WhatsApp, Shopee reviews, and Discord. It normalizes informal slang, collapses expressive character repetition, reduces punctuation noise, and optionally corrects typos, all through a single clean API.

```python
from basa import normalize

normalize("GW GKKKK NGERTIII BNGTTTT!!!!!")
# → 'saya tidak mengerti banget!'
```

---

## Why BASA?

Indonesian social media text is notoriously difficult to process with standard NLP tools:

| Raw input | After `normalize()` |
|---|---|
| `gw gk ngerti bngt sihhhh!!!` | `saya tidak mengerti banget sih!` |
| `kmrn gamau makan krn baper bgt` | `kemarin tidak mau makan karena bawa perasaan banget` |
| `otw gan, rekber dlu ya!!!!!` | `dalam perjalanan saudara, rekening bersama dulu ya!` |
| `GW GKKKK NGERTIII BNGTTTT!!!!!` | `saya tidak mengerti banget!` |

Standard tokenizers and language models often fail on this kind of input because they see `"gkkkk"`, `"bngtttt"`, and `"ngertiii"` as unknown tokens. BASA normalizes them first.

---

## Installation

```bash
pip install basa
```

> **Requires Python 3.10+**

---

## Quick Start

### One-liner (recommended for most use cases)

```python
from basa import normalize

normalize("gw gk ngerti bngt sihhhh!!!")
# → 'saya tidak mengerti banget sih!'
```

### Zero-config alias

```python
from basa import quick

quick("GW GKKKK NGERTIII BNGTTTT!!!!!")
# → 'saya tidak mengerti banget!'
```

`quick()` is a thin alias for `normalize()` with all defaults applied. Use it when you want the shortest possible call.

### Batch processing

```python
from basa import normalize

texts = [
    "gw gk ngerti",
    "lu udh makan??",
    "kmrn gamau pergi krn baper bgt",
]

normalize(texts)
# → ['saya tidak mengerti', 'kamu sudah makan?', 'kemarin tidak mau pergi karena bawa perasaan banget']
```

---

## API Reference

### `normalize(text, **options)`

Normalize informal Indonesian text. Accepts a single string or a list of strings.

```python
normalize(
    text: Union[str, List[str]],
    apply_slang: bool = True,
    apply_typo: bool = False,
    lowercase: bool = True,
    normalize_punctuation: bool = True,
    normalize_whitespace: bool = True,
) -> Union[str, List[str]]
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | `str` or `List[str]` | — | Input text or list of texts. |
| `apply_slang` | `bool` | `True` | Expand slang and reduce expressive repeated characters (e.g. `"bngtttt"` → `"banget"`). |
| `apply_typo` | `bool` | `False` | Correct misspelled words using Levenshtein distance. **Opt-in** — requires a vocabulary to be loaded first. |
| `lowercase` | `bool` | `True` | Lowercase the text before processing. Set `False` for NER and case-sensitive pipelines. |
| `normalize_punctuation` | `bool` | `True` | Collapse repeated punctuation marks (`"!!!!!"` → `"!"`). |
| `normalize_whitespace` | `bool` | `True` | Strip leading/trailing whitespace and collapse internal multiple spaces. |

#### Processing pipeline (in order)

```
1. lowercase            → "GW GK NGERTI" → "gw gk ngerti"
2. slang normalization  → "gkkkk" → "gk" → "tidak"
3. typo correction      → "mkan" → "makan"  (opt-in)
4. punctuation          → "!!!!!" → "!"
5. whitespace cleanup   → "  a   b  " → "a b"
```

#### Examples

```python
# Preserve case for NER tasks
normalize("Jokowi pergi ke Jakarta", lowercase=False)
# → 'Jokowi pergi ke Jakarta'

# Disable slang (pass through raw tokens)
normalize("gw gk ngerti", apply_slang=False)
# → 'gw gk ngerti'

# Enable typo correction (requires vocab)
from basa import typo
typo.add_to_vocab({"makan", "minum", "pergi"})
normalize("saya mkan dan mnum", apply_typo=True)
# → 'saya makan dan minum'
```

---

### `quick(text)`

Zero-config alias for `normalize()` with all default settings.

```python
from basa import quick

quick("gw gamau pergi krn mager")
# → 'saya tidak mau pergi karena malas bergerak'
```

---

### `typo` — Typo Corrector

BASA's typo corrector is **vocabulary-driven and opt-in by default**. You supply the vocabulary; BASA finds the closest match using Levenshtein distance.

```python
from basa import typo

# Load your domain vocabulary
typo.add_to_vocab({"makan", "minum", "masak", "pergi", "datang"})

typo.correct("mkan")     # → 'makan'
typo.correct("mnm")      # → 'minum'
typo.correct("ok")       # → 'ok'  (too short, skipped by default)

# Correct a full sentence
typo.correct_text("saya mkan dan mnm")
# → 'saya makan dan minum'

# Get multiple suggestions
typo.suggest("mkan", top_k=3)
# → ['makan', 'masak', 'minum']
```

#### Why is `apply_typo=False` by default?

Typo correction is **destructive** when applied blindly. Without the right vocabulary, domain-specific terms like `xgboost`, `lightgbm`, or `rekber` would be mangled. BASA follows the principle of *conservative by default, destructive features opt-in*.

#### Vocabulary management

```python
from basa import typo

typo.add_to_vocab({"kata", "lain"})      # add words
typo.remove_from_vocab({"kata"})         # remove words
typo.clear_vocab()                       # reset entirely
len(typo)                                # vocab size
"makan" in typo                          # membership check

# Check cache statistics (useful for profiling)
typo.cache_info()
# → {'hits': 120, 'misses': 35, 'size': 35}
```

#### Typo corrector options

```python
from basa.core.typo import TypoCorrector

corrector = TypoCorrector(
    vocab={"makan", "minum"},
    min_word_length=4,    # tokens shorter than this are skipped (default: 4)
    min_confidence=0.5,   # minimum correction confidence in [0, 1] (default: 0.5)
)
```

---

### `slang` — Slang Normalizer

Access the underlying slang engine directly for fine-grained control.

```python
from basa.core.slang import slang, SlangNormalizer

# Use the singleton
slang.normalize("gw gamau pergi krn lg baper bgt")
# → 'saya tidak mau pergi karena sedang bawa perasaan banget'

# Custom dictionary (extend or override defaults)
custom = SlangNormalizer(custom_mapping={
    "gaskeun": "ayo lakukan",
    "jancok":  "ekspresi",
})
custom.normalize("gaskeun bro!")
# → 'ayo lakukan bro!'

# Batch normalize
slang.normalize_batch(["gw makan", "lu minum"])
# → ['saya makan', 'kamu minum']
```

#### Slang dictionary categories

The built-in dictionary covers **1,200+ entries** across 27 categories:

| Category | Count | Examples |
|---|---|---|
| Pronouns | ~40 | `gw` → saya, `lu` → kamu, `doi` → dia, `ane` → saya, `sampeyan` → kamu |
| Kinship & address | ~23 | `kk` → kakak, `ortu` → orang tua, `bokap` → ayah, `nyokap` → ibu |
| Negation | ~25 | `ga`, `gak`, `nggak`, `kagak`, `jangan`, `belom` → tidak/belum/jangan |
| Compound negation | ~30 | `gamau` → tidak mau, `gabisa` → tidak bisa, `gatau` → tidak tahu |
| Conjunctions | ~51 | `yg` → yang, `krn` → karena, `stlh` → setelah, `sblm` → sebelum |
| Verbs | ~100 | `udah` → sudah, `ngerti` → mengerti, `nyari` → mencari, `ngobrol` → mengobrol |
| Adjectives & adverbs | ~109 | `bgt` → banget, `lmyn` → lumayan, `pdhl` → padahal, `kyknya` → sepertinya |
| Question words | ~16 | `gmn` → bagaimana, `knp` → kenapa, `kumaha` → bagaimana (Sunda) |
| Greetings & responses | ~80 | `makasih`, `tq`, `sori`, `yoi`, `bye`, `tengkyu` → terima kasih/maaf/dll |
| Temporal & location | ~24 | `skrg` → sekarang, `kmrn` → kemarin, `mgg` → minggu, `wktu` → waktu |
| Internet slang | ~50 | `otw` → dalam perjalanan, `btw` → omong-omong, `lowkey` → diam-diam |
| E-commerce & finance | ~30 | `ongkir` → ongkos kirim, `cod` → bayar di tempat, `duit` → uang |
| Youth / Gen-Z | ~26 | `mager` → malas bergerak, `baper` → bawa perasaan, `gabut` → tidak ada kegiatan |
| Discourse markers | ~13 | `mksdnya` → maksudnya, `pokoknya`, `intinya`, `menurutku` → menurut saya |
| Javanese extended | ~35 | `mangan` → makan, `turu` → tidur, `apik` → bagus, `okeh` → banyak |
| Sundanese extended | ~27 | `abdi` → saya, `geus` → sudah, `tiasa` → bisa, `atuh` → dong |
| Nouns | ~48 | `hp` → handphone, `temen` → teman, `matkul` → mata kuliah, `kantor` → kantor |
| Health | ~80 | `dmm` → demam, `opname` → rawat inap, `gws` → lekas sembuh, `isoman` → isolasi mandiri |
| Emotions & expressions | ~108 | `galau`, `bete`, `ghosting`, `crush`, `pdkt` → pendekatan, `mupeng` |
| Food & drink | ~110 | `nasgor` → nasi goreng, `kopsu` → kopi susu, `laper` → lapar, `kenyang` |
| Clothing & fashion | ~85 | `ootd` → pakaian hari ini, `thrifting` → belanja baju bekas, `hoodie` |
| Transportation | ~75 | `ojol` → ojek online, `krl` → kereta rel listrik, `macet`, `nebeng` → menumpang |
| Religion & culture | ~95 | `alhamdulillah`, `bismillah`, `bukber` → buka bersama, `ultah` → ulang tahun |
| Education extended | ~91 | `bimbel` → bimbingan belajar, `ospek` → orientasi studi, `maba` → mahasiswa baru |
| Work & office | ~124 | `wfh` → kerja dari rumah, `deadline` → batas waktu, `lembur`, `resign` |
| Numbers & quantity | ~73 | `1rb` → seribu, `5jt` → lima juta, `rata2` → rata-rata, `tiba2` → tiba-tiba |
| Compound expressions | ~86 | `ngapain` → sedang apa, `kapan2` → kapan-kapan, `otw ke` → dalam perjalanan ke |

#### Extending the dictionary

You can add domain-specific entries at any time without subclassing:

```python
from basa.core.slang import slang, SlangNormalizer

# Add a single entry to the shared singleton
slang.add("npwp", "nomor pokok wajib pajak")
slang.lookup("npwp")   # → 'nomor pokok wajib pajak'
slang.remove("npwp")   # → True
len(slang)             # total entries

# Add multiple entries at once (single regex recompile)
slang.bulk_add({
    "ktp":  "kartu tanda penduduk",
    "sim":  "surat izin mengemudi",
    "stnk": "surat tanda nomor kendaraan",
})

# Or create a fully isolated custom normalizer
custom = SlangNormalizer(custom_mapping={
    "jancok": "ekspresi",
    "cuk":    "ekspresi",
})
custom.normalize("jancok, mantul tenan!")
# → 'ekspresi, mantap betul sungguh!'

# Export the full mapping for inspection or persistence
mapping = slang.export()   # → Dict[str, str]
slang.reset()              # restore built-in defaults
```

---

## Real-World Use Cases

### Preprocessing for sentiment analysis

```python
from basa import normalize

reviews = [
    "produknya bagus bgt tp ongkirnya mahal bgt!!!",
    "gw kecewa bngt, barang ga sesuai deskripsi smskali",
    "rekber dlu gan, takut kena tipu",
]

clean = normalize(reviews)
# Pass clean into your sentiment model
```

### Preprocessing for a custom NLP pipeline

```python
from basa import normalize, typo

# Load your domain vocabulary (e.g., from a word list file)
with open("vocab.txt") as f:
    domain_vocab = set(f.read().splitlines())

typo.add_to_vocab(domain_vocab)

def preprocess(text: str) -> str:
    return normalize(text, apply_typo=True)

preprocess("gw mkan siang tdi di wrng padang")
# → 'saya makan siang tadi di warung padang'
```

### NER pipeline (preserve casing)

```python
from basa import normalize

text = "Jokowi blg bhw pemerintah akan bantu UMKM"
normalize(text, lowercase=False)
# → 'Jokowi bilang bahwa pemerintah akan bantu UMKM'
```

---

## Design Philosophy

BASA is built around three principles:

1. **Conservative by default.** Only safe, lossless transforms are enabled out of the box. Destructive features (like typo correction) require explicit opt-in.

2. **No bundled vocabularies for correction.** Every domain has different vocabulary needs — fintech, e-commerce, ML, healthcare. Callers supply their own word list via `typo.add_to_vocab()`.

3. **Zero required dependencies for core preprocessing.** The `normalize()` and `slang` modules use only the Python standard library. The optional `transformers`, `torch`, and `pydantic` dependencies are only required for advanced modules (`basa.translate`, `basa.evaluate`).

---

## Development

### Setup

```bash
git clone https://github.com/Muanai/basa.git
cd basa
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS / Linux
pip install -e ".[dev]"
```

### Running tests

```bash
pytest tests/ -v
```

### Optional extras

```bash
pip install -e ".[serving]"     # FastAPI serving
pip install -e ".[evaluation]"  # ROUGE, BERTScore, seqeval
pip install -e ".[dev]"         # pytest, ruff, black, mypy
```

---

## Roadmap

| Version | Status | Features |
|---|---|---|
| **v0.1** | ✅ Current | `normalize()`, `quick()`, slang (1,600+ entries, 27 categories), typo corrector |
| **v0.2** | 🔜 Planned | BK-Tree / SymSpell for faster typo correction at large vocab sizes |
| **v0.3** | 🔜 Planned | Emoji handling, `remove_emoji` flag |
| **v0.4** | 🔜 Planned | Tokenizer module (`basa.tokenize`) |
| **v1.0** | 🔜 Planned | Stable API, full docs site, PyPI release |

---

## Contributing

Contributions are welcome! In particular:

- **Slang dictionary additions** — if you spot a common slang word that's missing, open a PR adding it to the appropriate category in [`src/basa/core/slang.py`](src/basa/core/slang.py).
- **Bug reports** — please include the exact input string and the unexpected output.
- **Performance improvements** — especially for the typo correction module.

Please open an issue before submitting large changes.

---

## License

MIT © 2026 [Muanai Khalifah Revindo](mailto:muanaikhalifahr@gmail.com)