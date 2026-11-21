<div align="center">
  <img src="docs/assets/basa.png" alt="Logo BASA" width="96" />

  <h1>BASA</h1>

  <p><em>Pra-pemrosesan NLP modern untuk bahasa Indonesia dan bahasa daerah.</em></p>

  <p>
    <a href="https://pypi.org/project/basa/"><img src="https://img.shields.io/pypi/v/basa.svg?color=160CA5" alt="Versi PyPI" /></a>
    <a href="https://pypi.org/project/basa/"><img src="https://img.shields.io/pypi/pyversions/basa?color=160CA5" alt="Python" /></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-160CA5.svg" alt="Lisensi: MIT" /></a>
    <a href="https://muanai.github.io/basa/"><img src="https://img.shields.io/badge/docs-mkdocs-160CA5.svg" alt="Dokumentasi" /></a>
    <a href="https://pepy.tech/projects/basa"><img src="https://img.shields.io/pepy/dt/basa?label=downloads&color=160CA5" alt="Unduhan" /></a>
  </p>

  <p>
    <a href="README.md">English</a> &nbsp;|&nbsp; <strong>Bahasa Indonesia</strong>
  </p>
</div>

---

BASA adalah pustaka pra-pemrosesan teks yang ringan dan bebas dependensi eksternal (*zero-dependency*) untuk teks bahasa Indonesia di dunia nyata — seperti yang ditemukan di Twitter/X, TikTok, WhatsApp, ulasan Shopee, dan Discord. BASA menormalisasi bahasa gaul, meringkas pengulangan huruf ekspresif, merapikan tanda baca berlebih, serta menyediakan koreksi typo opsional dalam satu API yang ringkas.

```python
from basa import normalize

normalize("GW GKKKK NGERTIII BNGTTTT!!!!!")
# → 'saya tidak mengerti banget!'
```

---

## Mengapa BASA?

Teks media sosial berbahasa Indonesia sering kali sulit diproses langsung oleh perangkat NLP standar:

| Input mentah | Setelah `normalize()` |
|---|---|
| `gw gk ngerti bngt sihhhh!!!` | `saya tidak mengerti banget sih!` |
| `kmrn gamau makan krn baper bgt` | `kemarin tidak mau makan karena bawa perasaan banget` |
| `otw gan, rekber dlu ya!!!!!` | `dalam perjalanan saudara, rekening bersama dulu ya!` |
| `GW GKKKK NGERTIII BNGTTTT!!!!!` | `saya tidak mengerti banget!` |

Tokenizer dan model bahasa sering kali memecah kata seperti `"gkkkk"`, `"bngtttt"`, dan `"ngertiii"` menjadi fragmen token yang tidak bermakna. BASA merapikannya terlebih dahulu sebelum masuk ke model.

---

## Instalasi

```bash
pip install basa
```

> **Membutuhkan Python 3.10+**

---

## Mulai Cepat

### Satu baris kode (direkomendasikan)

```python
from basa import normalize

normalize("gw gk ngerti bngt sihhhh!!!")
# → 'saya tidak mengerti banget sih!'
```

### Alias tanpa konfigurasi

```python
from basa import quick

quick("GW GKKKK NGERTIII BNGTTTT!!!!!")
# → 'saya tidak mengerti banget!'
```

`quick()` adalah pembungkus tipis untuk `normalize()` dengan seluruh pengaturan bawaan. Gunakan saat Anda hanya membutuhkan pemanggilan terpendek.

### Pemrosesan batch

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

## Referensi API

### `normalize(text, **options)`

Menormalisasi teks bahasa Indonesia informal. Menerima satu string maupun `list[str]`.

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

#### Parameter

| Parameter | Tipe | Bawaan | Deskripsi |
|---|---|---|---|
| `text` | `str` atau `list[str]` | — | Teks tunggal atau daftar teks yang akan diproses. |
| `apply_slang` | `bool` | `True` | Mengubah slang ke bentuk baku dan meringkas pengulangan huruf (mis. `"bngtttt"` → `"banget"`). |
| `apply_typo` | `bool` | `False` | Mengoreksi salah ketik menggunakan jarak Levenshtein. **Opt-in** — membutuhkan kosakata yang sudah dimuat. |
| `lowercase` | `bool` | `True` | Mengubah teks menjadi huruf kecil sebelum diproses. Atur ke `False` untuk pipeline NER yang sensitif terhadap huruf kapital. |
| `normalize_punctuation` | `bool` | `True` | Meringkas tanda baca berulang (`"!!!!!"` → `"!"`). |
| `normalize_whitespace` | `bool` | `True` | Menghapus spasi di awal/akhir serta merapikan spasi ganda. |
| `mode` | `"formal"` atau `"concise"` | `"formal"` | Gaya normalisasi: `"formal"` memakai padanan baku lengkap; `"concise"` memilih padanan satu kata yang lebih hemat token jika tersedia. |

#### Urutan tahapan pemrosesan

```
1. lowercase            → "GW GK NGERTI" → "gw gk ngerti"
2. slang normalization  → menjaga URL/handle, "gkkkk" → "gk" → "tidak" (formal / concise)
3. typo correction      → "mkan" → "makan"  (opt-in via indeks hapus SymSpell)
4. punctuation          → "!!!!!" → "!"
5. whitespace cleanup   → "  a   b  " → "a b"
```

#### Contoh

```python
# Pertahankan huruf kapital untuk NER
normalize("Jokowi pergi ke Jakarta", lowercase=False)
# → 'Jokowi pergi ke Jakarta'

# Nonaktifkan normalisasi slang (biarkan token apa adanya)
normalize("gw gk ngerti", apply_slang=False)
# → 'gw gk ngerti'

# Mode concise untuk efisiensi token LLM
normalize("gw mager bgt gercep", mode="concise")
# → 'saya malas sekali cepat'

# Aktifkan koreksi typo (muat kosakata bawaan atau kosakata khusus)
from basa import typo
typo.load_default_vocab()          # atau typo.add_to_vocab({"teknik", "komputer"})
normalize("tehknik komptuer", apply_typo=True)
# → 'teknik komputer'
```

---

### `quick(text, mode="formal")`

Alias tanpa konfigurasi untuk `normalize()` dengan pengaturan bawaan.

```python
from basa import quick

quick("gw gamau pergi krn mager")
# → 'saya tidak mau pergi karena malas gerak'

quick("gw mager bgt gercep", mode="concise")
# → 'saya malas sekali cepat'
```

---

### `typo` — Koreksi Typo

Modul koreksi typo BASA bersifat **berbasis kosakata dan nonaktif secara bawaan**, didukung indeks hapus bergaya SymSpell berbahan murni Python serta pencarian Levenshtein terbatas pita diagonal dengan pemecahan seri deterministik. Anda dapat memuat kosakata inti bahasa Indonesia bawaan lewat `typo.load_default_vocab()` atau menambahkan kosakata domain sendiri via `typo.add_to_vocab()`.

```python
from basa import typo

# Muat kosakata inti bawaan, atau tambahkan istilah domain
typo.load_default_vocab()
typo.add_to_vocab({"xgboost", "lightgbm"})

typo.correct("tehknik")  # → 'teknik'
typo.correct("ok")       # → 'ok'  (terlalu pendek, dilewati secara bawaan)

# Koreksi satu kalimat (melewati URL, domain, handle, angka, dan menjaga tanda baca)
typo.correct_text("perangkat komptuer, https://example.com")
# → 'perangkat komputer, https://example.com'

# Ambil beberapa saran terdekat
typo.suggest("tehknik", top_k=2)
# → ['teknik', 'teknis']
```

#### Mengapa `apply_typo=False` secara bawaan?

Koreksi typo dapat bersifat **destruktif** jika dijalankan tanpa konteks kosakata. Istilah khusus seperti `xgboost`, `lightgbm`, atau `rekber` bisa keliru diubah menjadi kata umum. BASA berpegang pada prinsip *aman secara bawaan, fitur berisiko bersifat opt-in*.

#### Pengelolaan kosakata

```python
from basa import typo

typo.add_to_vocab({"kata", "lain"})      # tambah kata
typo.remove_from_vocab({"kata"})         # hapus kata
typo.clear_vocab()                       # kosongkan seluruh kosakata
len(typo)                                # jumlah kata dalam kosakata
"makan" in typo                          # cek keanggotaan

# Statistik cache (berguna untuk profiling)
typo.cache_info()
# → {'hits': 120, 'misses': 35, 'size': 35}
```

#### Opsi `TypoCorrector`

```python
from basa.core.typo import TypoCorrector

corrector = TypoCorrector(
    vocab={"makan", "minum"},
    min_word_length=4,    # token lebih pendek dari ini dilewati (bawaan: 4)
    min_confidence=0.5,   # ambang keyakinan minimum dalam [0, 1] (bawaan: 0.5)
)
```

---

### `slang` — Normalisasi Slang

Akses mesin slang secara langsung untuk pengaturan lanjutan.

```python
from basa.core.slang import slang, SlangNormalizer

# Gunakan singleton bawaan
slang.normalize("gw gamau pergi krn lg baper bgt")
# → 'saya tidak mau pergi karena lagi bawa perasaan banget'

# Kamus khusus (tambah atau timpa entri bawaan)
custom = SlangNormalizer(custom_mapping={
    "gaskeun": "ayo lakukan",
    "jancok":  "ekspresi",
})
custom.normalize("gaskeun bro!")
# → 'ayo lakukan bro!'

# Normalisasi batch
slang.normalize_batch(["gw makan", "lu minum"])
# → ['saya makan', 'kamu minum']
```

#### Kategori kamus slang

Kamus bawaan mencakup **1.236 entri** pada 28 kategori (tanpa duplikasi antarkategori dan tetap menjaga istilah teknis bahasa Inggris):

| Kategori | Jumlah | Contoh |
|---|---|---|
| Kata ganti (*Pronouns*) | 34 | `gw` → saya, `lu` → kamu, `doi` → dia, `ane` → saya, `sampeyan` → kamu |
| Kekerabatan (*Kinship & address*) | 19 | `kk` → kakak, `ortu` → orang tua, `bokap` → ayah, `nyokap` → ibu |
| Negasi (*Negation*) | 22 | `ga`, `gak`, `nggak`, `kagak` → tidak |
| Negasi majemuk (*Compound negation*) | 30 | `gamau` → tidak mau, `gabisa` → tidak bisa, `gatau` → tidak tahu |
| Konjungsi (*Conjunctions*) | 53 | `yg` → yang, `krn` → karena, `stlh` → setelah, `sblm` → sebelum, `kpd` → kepada |
| Kata kerja (*Verbs*) | 100 | `udah` → sudah, `lg` → lagi, `ngerti` → mengerti, `nyari` → mencari, `ngobrol` → mengobrol |
| Adjektiva & adverbia | 149 | `bgt` → banget, `lmyn` → lumayan, `pdhl` → padahal, `kyknya` → sepertinya |
| Kata tanya (*Question words*) | 28 | `gmn` → bagaimana, `bgmn` → bagaimana, `knp` → kenapa, `kumaha` → bagaimana (Sunda) |
| Sapaan & respons | 72 | `makasih`, `tq` → terima kasih, `sori` → maaf, `yoi` → iya |
| Waktu & lokasi | 27 | `skrg` → sekarang, `kmrn` → kemarin, `mgg` → minggu, `wktu` → waktu, `jkt` → jakarta |
| Slang internet | 42 | `otw` → dalam perjalanan, `btw` → omong-omong, `fyi` → sebagai informasi, `imo` → menurut saya |
| E-commerce & keuangan | 30 | `ongkir` → ongkos kirim, `cod` → bayar di tempat, `rekber` → rekening bersama, `gan` → saudara |
| Bahasa gaul / Gen-Z | 32 | `mager` → malas gerak, `baper` → bawa perasaan, `gabut` → gaji buta, `kepo` → penasaran |
| Penanda wacana | 11 | `mksdnya` → maksudnya, `pokonya` → pokoknya, `menurutku` → menurut saya |
| Bahasa Jawa | 35 | `mangan` → makan, `turu` → tidur, `apik` → bagus, `okeh` → banyak |
| Bahasa Sunda | 26 | `abdi` → saya, `geus` → sudah, `tiasa` → bisa, `atuh` → dong |
| Kata benda (*Nouns*) | 45 | `hp` → handphone, `temen` → teman, `matkul` → mata kuliah, `tmn2` → teman-teman |
| Kesehatan (*Health*) | 38 | `dmm` → demam, `opname` → rawat inap, `gws` → lekas sembuh, `isoman` → isolasi mandiri |
| Emosi & ekspresi | 62 | `semngt` → semangat, `kzl`, `bete` → kesal, `gokil` → gila |
| Makanan & minuman | 48 | `nasgor` → nasi goreng, `kopsu` → kopi susu, `laper` → lapar, `mkanan` → makanan |
| Pakaian & fesyen | 25 | `bj` → baju, `kaos` → kaus, `kmja` → kemeja |
| Transportasi | 33 | `ojol` → ojek online, `krl` → kereta rel listrik, `angkot` → angkutan kota |
| Agama & budaya | 55 | `insyaallah` → insya allah, `alhdlh` → alhamdulillah, `bukber` → buka bersama, `ultah` → ulang tahun |
| Pendidikan | 54 | `bimbel` → bimbingan belajar, `ospek` → orientasi studi, `maba` → mahasiswa baru |
| Kerja & kantor | 40 | `wfh` → kerja dari rumah, `krja` → kerja, `krjaan` → pekerjaan |
| Angka & kuantitas | 34 | `sejuta` → satu juta, `1rb` → seribu, `5jt` → lima juta, `rata2` → rata-rata |
| Ungkapan majemuk | 57 | `ngapain` → sedang apa, `kapan2` → kapan-kapan, `otw ke` → dalam perjalanan ke |
| Partikel | 35 | `lah`, `sih`, `deh` (berbagai varian partikel) |

#### Menambah entri kamus

Anda dapat menambahkan kosakata domain kapan saja secara dinamis:

```python
from basa.core.slang import slang, SlangNormalizer

# Tambah satu entri ke singleton bawaan
slang.add("npwp", "nomor pokok wajib pajak")
slang.lookup("npwp")   # → 'nomor pokok wajib pajak'
slang.remove("npwp")   # → True
len(slang)             # jumlah total entri

# Tambah banyak entri sekaligus (kompilasi ulang regex cukup satu kali)
slang.bulk_add({
    "ktp":  "kartu tanda penduduk",
    "sim":  "surat izin mengemudi",
    "stnk": "surat tanda nomor kendaraan",
})

# Atau buat instance terpisah
custom = SlangNormalizer(custom_mapping={
    "jancok": "ekspresi",
    "cuk":    "ekspresi",
})
custom.normalize("jancok, mantul tenan!")
# → 'ekspresi, mantap betul tenan!'

# Ekspor seluruh mapping atau kembalikan ke bawaan
mapping = slang.export()   # → Dict[str, str]
slang.reset()              # kembalikan kamus bawaan
```

---

## Contoh Penggunaan Nyata

### Pra-pemrosesan analisis sentimen

```python
from basa import normalize

reviews = [
    "produknya bagus bgt tp ongkirnya mahal bgt!!!",
    "gw kecewa bngt, barang ga sesuai deskripsi smskali",
    "rekber dlu gan, takut kena tipu",
]

clean = normalize(reviews)
# Masukkan hasil bersih ke model analisis sentimen
```

### Pipeline NLP dengan kosakata domain khusus

```python
from basa import normalize, typo

with open("vocab.txt") as f:
    domain_vocab = set(f.read().splitlines())

typo.add_to_vocab(domain_vocab)

def preprocess(text: str) -> str:
    return normalize(text, apply_typo=True)

preprocess("gw mkan siang tdi di wrng padang")
# → 'saya makan siang tadi di warung padang'
```

### Pipeline NER (menjaga kapitalisasi)

```python
from basa import normalize

text = "Jokowi blg pemerintah siap utk bantu UMKM"
normalize(text, lowercase=False)
# → 'Jokowi bilang pemerintah siap untuk bantu UMKM'
```

---

## Filosofi Desain

BASA dibangun di atas tiga prinsip utama:

1. **Konservatif secara bawaan.** Hanya transformasi aman tanpa hilangnya makna yang aktif secara default (`ONER = 0%` pada teks KBBI baku, URL, dan istilah teknis). Fitur yang berpotensi mengubah makna seperti koreksi typo tetap bersifat opt-in.

2. **Kosakata opt-in untuk koreksi typo.** Penggunaan umum dapat memuat daftar kata inti bahasa Indonesia via `typo.load_default_vocab()`, sedangkan domain spesifik (fintech, e-commerce, kesehatan) dapat menyuplai kosakatanya sendiri melalui `typo.add_to_vocab()`.

3. **Tanpa dependensi eksternal pada modul inti.** Modul `normalize()`, `quick()`, `slang`, dan `typo` hanya memakai pustaka standar Python (`dependencies = []`). Fitur tambahan bersifat opsional (`[serving]`, `[evaluation]`, `[docs]`, `[dev]`) di `pyproject.toml`.

---

## Pengembangan

### Persiapan

```bash
git clone https://github.com/Muanai/basa.git
cd basa
uv sync --extra dev
```

### Menjalankan pengujian & pemeriksaan

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src/basa
uv run pytest -m "not slow"
uv run pytest -m slow
```

### Suite evaluasi (`basa-evals`)

```bash
uv run --with "basa-evals>=0.1.1" basa-eval run --suite pilot_210 --system basa-full
```

### Dependensi opsional

```bash
pip install -e ".[docs]"        # MkDocs Material, mkdocs-ask-ai, mike
pip install -e ".[serving]"     # FastAPI serving
pip install -e ".[evaluation]"  # ROUGE, BERTScore, seqeval
pip install -e ".[dev]"         # pytest, ruff, black, mypy
```

---

## Peta Jalan (*Roadmap*)

| Versi | Status | Fitur |
|---|---|---|
| **v0.1** | ✅ Rilis | `normalize()`, `quick()`, situs PyPI & MkDocs, proteksi entitas `ONER = 0` |
| **v0.2** | ✅ Terbaru | Indeks hapus SymSpell, `load_default_vocab()`, `mode="concise"`, perluasan kamus, gerbang rilis CI |
| **v0.3** | 🔜 Rencana | Penanganan emoji, opsi `remove_emoji` |
| **v0.4** | 🔜 Rencana | Modul tokenisasi (`basa.tokenize`) |
| **v1.0** | 🔜 Rencana | Stabilitas API penuh dan integrasi kerangka LLM/RAG |

---

## Kontribusi & Komunitas

Kontribusi sangat terbuka! Lihat [Panduan Kontribusi](CONTRIBUTING.md), [Kode Etik](CODE_OF_CONDUCT.md), dan [Kebijakan Keamanan](SECURITY.md):

- **Penambahan slang & singkatan** — tambahkan entri terverifikasi ke kategori yang tepat pada [`src/basa/core/slang.py`](src/basa/core/slang.py) lalu jalankan `pytest` dan `basa-evals`.
- **Laporan bug** — sertakan input persis, hasil yang diharapkan, dan hasil aktual pada issue.
- **Performa & pengindeksan** — peningkatan pada normalisasi inti dan latensi SymSpell.

---

## Lisensi

MIT © 2026 [Muanai Khalifah Revindo](mailto:muanaikhalifahr@gmail.com)
