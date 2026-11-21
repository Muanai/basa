# BASA

[![PyPI version](https://img.shields.io/pypi/v/basa.svg)](https://pypi.org/project/basa/) 
[![Python](https://img.shields.io/pypi/pyversions/basa)](https://pypi.org/project/basa/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) 
[![CI](https://github.com/Muanai/basa/actions/workflows/ci.yml/badge.svg)](https://github.com/Muanai/basa/actions/workflows/ci.yml) 
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://muanai.github.io/basa/) 
[![Downloads](https://static.pepy.tech/badge/basa)](https://pepy.tech/projects/basa)

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
    text: str | list[str],
    apply_slang: bool = True,
    apply_typo: bool = False,
    lowercase: bool = True,
    normalize_punctuation: bool = True,
    normalize_whitespace: bool = True,
    mode: Literal["formal", "concise"] = "formal",
) -> str | list[str]
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | `str` or `list[str]` | — | Input text or list of texts. |
| `apply_slang` | `bool` | `True` | Expand slang and reduce expressive repeated characters (e.g. `"bngtttt"` → `"banget"`). |
| `apply_typo` | `bool` | `False` | Correct misspelled words using Levenshtein distance. **Opt-in** — requires a vocabulary to be loaded first. |
| `lowercase` | `bool` | `True` | Lowercase the text before processing. Set `False` for NER and case-sensitive pipelines. |
| `normalize_punctuation` | `bool` | `True` | Collapse repeated punctuation marks (`"!!!!!"` → `"!"`). |
| `normalize_whitespace` | `bool` | `True` | Strip leading/trailing whitespace and collapse internal multiple spaces. |
| `mode` | `"formal"` or `"concise"` | `"formal"` | Normalization style: `"formal"` uses full standard expansions; `"concise"` prefers shorter token-efficient replacements. |

#### Processing pipeline (in order)

```
1. lowercase            → "GW GK NGERTI" → "gw gk ngerti"
2. slang normalization  → shields URLs/handles, "gkkkk" → "gk" → "tidak" (formal / concise)
3. typo correction      → "mkan" → "makan"  (opt-in via SymSpell delete index)
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

# Concise mode for tighter token budgets
normalize("gw mager bgt gercep", mode="concise")
# → 'saya malas sekali cepat'

# Enable typo correction (load built-in vocab or add custom words)
from basa import typo
typo.load_default_vocab()          # or typo.add_to_vocab({"teknik", "komputer"})
normalize("tehknik komptuer", apply_typo=True)
# → 'teknik komputer'
```

---

### `quick(text, mode="formal")`

Zero-config alias for `normalize()` with default settings.

```python
from basa import quick

quick("gw gamau pergi krn mager")
# → 'saya tidak mau pergi karena malas gerak'

quick("gw mager bgt gercep", mode="concise")
# → 'saya malas sekali cepat'
```

---

### `typo` — Typo Corrector

BASA's typo corrector is **vocabulary-driven and opt-in by default**, backed by a pure-Python SymSpell-style delete index and diagonal-banded bounded Levenshtein search with deterministic tie-breaking. You can load the built-in standard Indonesian + tech vocabulary via `typo.load_default_vocab()` or supply your own domain words via `typo.add_to_vocab()`.

```python
from basa import typo

# Load built-in core Indonesian vocabulary, or add domain terms
typo.load_default_vocab()
typo.add_to_vocab({"xgboost", "lightgbm"})

typo.correct("tehknik")  # → 'teknik'
typo.correct("ok")       # → 'ok'  (too short, skipped by default)

# Correct a full sentence (skips URLs, domains, handles, digits, and punctuation)
typo.correct_text("perangkat komptuer, https://example.com")
# → 'perangkat komputer, https://example.com'

# Get multiple suggestions
typo.suggest("tehknik", top_k=2)
# → ['teknik', 'teknis']
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
# → 'saya tidak mau pergi karena lagi bawa perasaan banget'

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

The built-in dictionary covers **1,236 entries** across 28 categories (with deduplicated keys across all categories and code-switched English technical terms preserved verbatim):

| Category | Count | Examples |
|---|---|---|
| Pronouns | 34 | `gw` → saya, `lu` → kamu, `doi` → dia, `ane` → saya, `sampeyan` → kamu |
| Kinship & address | 19 | `kk` → kakak, `ortu` → orang tua, `bokap` → ayah, `nyokap` → ibu |
| Negation | 22 | `ga`, `gak`, `nggak`, `kagak` → tidak |
| Compound negation | 30 | `gamau` → tidak mau, `gabisa` → tidak bisa, `gatau` → tidak tahu |
| Conjunctions | 53 | `yg` → yang, `krn` → karena, `stlh` → setelah, `sblm` → sebelum, `kpd` → kepada |
| Verbs | 100 | `udah` → sudah, `lg` → lagi, `ngerti` → mengerti, `nyari` → mencari, `ngobrol` → mengobrol |
| Adjectives & adverbs | 149 | `bgt` → banget, `lmyn` → lumayan, `pdhl` → padahal, `kyknya` → sepertinya |
| Question words | 28 | `gmn` → bagaimana, `bgmn` → bagaimana, `knp` → kenapa, `kumaha` → bagaimana (Sunda) |
| Greetings & responses | 72 | `makasih`, `tq` → terima kasih, `sori` → maaf, `yoi` → iya |
| Temporal & location | 27 | `skrg` → sekarang, `kmrn` → kemarin, `mgg` → minggu, `wktu` → waktu, `jkt` → jakarta |
| Internet slang | 42 | `otw` → dalam perjalanan, `btw` → omong-omong, `fyi` → sebagai informasi, `imo` → menurut saya |
| E-commerce & finance | 30 | `ongkir` → ongkos kirim, `cod` → bayar di tempat, `rekber` → rekening bersama, `gan` → saudara |
| Youth / Gen-Z | 32 | `mager` → malas gerak, `baper` → bawa perasaan, `gabut` → gaji buta, `kepo` → penasaran |
| Discourse markers | 11 | `mksdnya` → maksudnya, `pokonya` → pokoknya, `menurutku` → menurut saya |
| Javanese extended | 35 | `mangan` → makan, `turu` → tidur, `apik` → bagus, `okeh` → banyak |
| Sundanese extended | 26 | `abdi` → saya, `geus` → sudah, `tiasa` → bisa, `atuh` → dong |
| Nouns | 45 | `hp` → handphone, `temen` → teman, `matkul` → mata kuliah, `tmn2` → teman-teman |
| Health | 38 | `dmm` → demam, `opname` → rawat inap, `gws` → lekas sembuh, `isoman` → isolasi mandiri |
| Emotions & expressions | 62 | `semngt` → semangat, `kzl`, `bete` → kesal, `gokil` → gila |
| Food & drink | 48 | `nasgor` → nasi goreng, `kopsu` → kopi susu, `laper` → lapar, `mkanan` → makanan |
| Clothing & fashion | 25 | `bj` → baju, `kaos` → kaus, `kmja` → kemeja |
| Transportation | 33 | `ojol` → ojek online, `krl` → kereta rel listrik, `angkot` → angkutan kota |
| Religion & culture | 55 | `insyaallah` → insya allah, `alhdlh` → alhamdulillah, `bukber` → buka bersama, `ultah` → ulang tahun |
| Education extended | 54 | `bimbel` → bimbingan belajar, `ospek` → orientasi studi, `maba` → mahasiswa baru |
| Work & office | 40 | `wfh` → kerja dari rumah, `krja` → kerja, `krjaan` → pekerjaan |
| Numbers & quantity | 34 | `sejuta` → satu juta, `1rb` → seribu, `5jt` → lima juta, `rata2` → rata-rata |
| Compound expressions | 57 | `ngapain` → sedang apa, `kapan2` → kapan-kapan, `otw ke` → dalam perjalanan ke |
| Particles | 35 | `lah`, `sih`, `deh` (particle variants) |

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
# → 'ekspresi, mantap betul tenan!'

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

text = "Jokowi blg pemerintah siap utk bantu UMKM"
normalize(text, lowercase=False)
# → 'Jokowi bilang pemerintah siap untuk bantu UMKM'
```

---

## Design Philosophy

BASA is built around three principles:

1. **Conservative by default.** Only safe, lossless transforms are enabled out of the box (`ONER = 0%` across standard KBBI text, URLs, and code-switched technical terms). Destructive features like typo correction remain opt-in.

2. **Opt-in vocabularies for typo correction.** General workflows can load the curated standard Indonesian core word list via `typo.load_default_vocab()`, while specialized domains (fintech, e-commerce, healthcare) can supply custom word lists via `typo.add_to_vocab()`.

3. **Zero required dependencies for core preprocessing.** The `normalize()`, `quick()`, `slang`, and `typo` modules use only the Python standard library (`dependencies = []`). Optional extras (`[serving]`, `[evaluation]`, `[docs]`, `[dev]`) are isolated in `pyproject.toml`.

---

## Development

### Setup

```bash
git clone https://github.com/Muanai/basa.git
cd basa
uv sync --extra dev
```

### Running checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src/basa
uv run pytest -m "not slow"
uv run pytest -m slow
```

### Evaluation suite (`basa-evals`)

```bash
uv run --with "basa-evals>=0.1.1" basa-eval run --suite pilot_210 --system basa-full
```

### Optional extras

```bash
pip install -e ".[docs]"        # MkDocs Material, mkdocs-ask-ai, mike
pip install -e ".[serving]"     # FastAPI serving
pip install -e ".[evaluation]"  # ROUGE, BERTScore, seqeval
pip install -e ".[dev]"         # pytest, ruff, black, mypy
```

---

## Roadmap

| Version | Status | Features |
|---|---|---|
| **v0.1** | ✅ Released | `normalize()`, `quick()`, PyPI & MkDocs site, `ONER = 0` entity guardrails |
| **v0.2** | ✅ Current | SymSpell delete index, `load_default_vocab()`, `mode="concise"`, expanded lexicon, CI release gate |
| **v0.3** | 🔜 Planned | Emoji handling, `remove_emoji` flag |
| **v0.4** | 🔜 Planned | Tokenizer module (`basa.tokenize`) |
| **v1.0** | 🔜 Planned | Stable API freeze and LLM/RAG framework integrations |

---

## Contributing & Community

Contributions are welcome! See our [Contributing Guide](CONTRIBUTING.md), [Code of Conduct](CODE_OF_CONDUCT.md), and [Security Policy](SECURITY.md):

- **Slang & abbreviation additions** — add verified entries to the appropriate category in [`src/basa/core/slang.py`](src/basa/core/slang.py) and run `pytest` + `basa-evals`.
- **Bug reports** — open an issue with the exact input string, expected output, and actual output.
- **Performance & indexing** — improvements to core normalization and SymSpell lookup latency.

---

## License

MIT © 2026 [Muanai Khalifah Revindo](mailto:muanaikhalifahr@gmail.com)
