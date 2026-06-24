"""
BASA - Slang Normalization Module
===================================
Converts informal/colloquial Indonesian text (including Javanese/Sundanese
particles) into standardized Indonesian.

Supported categories:
    - Pronouns (aku/kamu shortcuts)
    - Kinship & address terms (kk, bokap, nyokap, dll)
    - Negation (ga/gak/nggak → tidak)
    - Compound negation (gamau, gabisa, gatau → tidak mau, dll)
    - Conjunctions & prepositions (abbreviations like yg, dgn, krn)
    - Common verbs (udah, blm, mo, tau, liat, dll)
    - Adjectives & adverbs (bgt, bener, lumayan, dll)
    - Question words (knp, gmn, kmn, dll)
    - Greetings & responses (makasih, ok, sip, tq, dll)
    - Temporal & location (skrg, ntr, kmrn, sini, dll)
    - Internet slang → Indonesian equivalent (btw, lol, omg, dll)
    - E-commerce & finance (ongkir, rekber, tf, dll)
    - Youth & Gen-Z slang (mager, baper, gabut, dll)
    - Discourse markers (mksd, intinya, menurutku, dll)
    - Javanese extended (mangan, turu, apik, dll)
    - Sundanese extended (abdi, anjeun, geus, dll)
    - Nouns (temen, hp, laptop, dll)
    - Health terms (dmm, btk, opname, dll)
    - Emotions & expressions (galau, baper, kesal, ghosting, dll)
    - Food & drink (nasgor, kopsu, laper, kenyang, dll)
    - Clothing & fashion (ootd, thrifting, hoodie, dll)
    - Transportation (ojol, krl, macet, nebeng, dll)
    - Religion & culture (alhamdulillah, bismillah, ultah, dll)
    - Education extended (bimbel, ospek, maba, snbt, dll)
    - Work & office (wfh, deadline, lembur, resign, dll)
    - Numbers & quantity (1rb, 5jt, rata2, tiba2, dll)
    - Compound expressions (ngapain, otw ke, kapan2, dll)
    - Particles (lah, deh, nih, dong, kok, sih, lho, pun, dll)

Usage:
    from basa.core.slang import slang

    # Basic usage (convenience singleton)
    result = slang.normalize("gw gamau pergi krn lg baper bgt")
    # → "saya tidak mau pergi karena sedang bawa perasaan banget"

    # With custom entries
    from basa.core.slang import SlangNormalizer
    normalizer = SlangNormalizer(custom_mapping={"jancok": "ekspresi"})
    result = normalizer.normalize("gw jancok kaget")

    # Batch processing
    texts = ["gw udah makan", "km blm tidur?"]
    results = slang.normalize_batch(texts)

Notes:
    - All replacements are lowercased (standard for NLP preprocessing).
    - Word boundaries (\\b) prevent partial-word substitution.
    - Slang keys sorted longest-first to prevent premature partial matches.
    - Repeated character normalization distinguishes vowels vs consonants
      to avoid breaking abbreviations like "kk", "dll", "mm".
"""

import re
from typing import Dict, List, Optional

# ─────────────────────────────────────────────────────────────────────────────
# SLANG DICTIONARY (organized by category for easier maintenance)
# ─────────────────────────────────────────────────────────────────────────────

# First & second person pronouns
_PRONOUNS: Dict[str, str] = {
    # First person singular
    "aq":    "aku",
    "ak":    "aku",
    "akuh":  "aku",
    "q":     "aku",
    "sy":    "saya",
    "w":     "saya",
    "gw":    "saya",
    "gue":   "saya",
    "gua":   "saya",
    "ane":   "saya",       # Betawi/Jakartan slang
    "ana":   "saya",       # Arabic-influenced
    "wkwk":  "tertawa",    # common filler — override happens in internet
    # First person possessive
    "gw nya":"saya punya",
    "gue nya":"saya punya",
    # Second person
    "u":     "kamu",
    "lu":    "kamu",
    "lo":    "kamu",
    "loe":   "kamu",
    "elo":   "kamu",
    "elu":   "kamu",
    "km":    "kamu",
    "ente":  "kamu",       # Betawi/Jakartan slang
    "antum": "kamu",       # Arabic-influenced (plural polite)
    "sampeyan": "kamu",    # Javanese polite
    "sampean": "kamu",     # Javanese casual
    "sampyan": "kamu",     # Javanese casual variant
    # Third person
    "dy":    "dia",
    "dya":   "dia",
    "doi":   "dia",        # Jakartan slang for girlfriend/boyfriend
    # Plural
    "mrk":   "mereka",
    "qt":    "kita",
    "kln":   "kalian",
    # Reflexive
    "sndiri": "sendiri",
    "sndr":   "sendiri",
}

# Kinship & address terms
_KINSHIP: Dict[str, str] = {
    "kk":     "kakak",
    "kak":    "kakak",
    "adk":    "adik",
    "adek":   "adik",
    "bpk":    "bapak",
    "bpak":   "bapak",
    "bapk":   "bapak",
    "ayh":    "ayah",
    "klg":    "keluarga",
    "klrg":   "keluarga",
    "kel":    "keluarga",
    "ortu":   "orang tua",
    "ortuku": "orang tuaku",
    "bokap":  "ayah",
    "nyokap": "ibu",
    "pakde":  "paman",
    "bude":   "bibi",
    "om":     "paman",
    "tante":  "bibi",
}

# Standalone negation words
_NEGATION: Dict[str, str] = {
    "g":       "tidak",
    "ga":      "tidak",
    "gak":     "tidak",
    "gk":      "tidak",
    "ngga":    "tidak",
    "nggak":   "tidak",
    "engga":   "tidak",
    "enggak":  "tidak",
    "kagak":   "tidak",
    "nope":    "tidak",
    "nop":     "tidak",
    "gakk":    "tidak",
    "gaknya":  "tidaknya",
    "bkn":     "bukan",
    "bknnya":  "bukannya",
    "jgn":     "jangan",
    "jgnan":   "jangan",
    "belom":   "belum",
    "belom2":  "belum-belum",
    "blom":    "belum",
    "blm2":    "belum-belum",
    "masih blm":"masih belum",
}

# Compound negation — written as one word without spaces (very common in chat)
# e.g. "gamau" = "ga" + "mau" = "tidak mau"
# NOTE: These MUST be registered before single-char negation in the dict so
# that the longest-first sort in _compile_pattern() handles them correctly.
_COMPOUND_NEGATION: Dict[str, str] = {
    "gamau":    "tidak mau",
    "gmau":     "tidak mau",
    "gabisa":   "tidak bisa",
    "gbisa":    "tidak bisa",
    "gakbisa":  "tidak bisa",
    "gapunya":  "tidak punya",
    "gpunya":   "tidak punya",
    "gasuka":   "tidak suka",
    "gsuka":    "tidak suka",
    "gaada":    "tidak ada",
    "gada":     "tidak ada",   # gaada → gada after vowel reduction
    "gatau":    "tidak tahu",
    "gtau":     "tidak tahu",
    "gatahu":   "tidak tahu",
    "gaperlu":  "tidak perlu",
    "gperlu":   "tidak perlu",
    "gaboleh":  "tidak boleh",
    "gboleh":   "tidak boleh",
    "gamakan":  "tidak makan",
    "gaminum":  "tidak minum",
    "gadatang": "tidak datang",
    "gamasuk":  "tidak masuk",
    "gasempet": "tidak sempat",
    "gabawa":   "tidak bawa",
    "gabayar":  "tidak bayar",
    "gaberani": "tidak berani",
    "gabalik":  "tidak balik",
    "gabener":  "tidak benar",
    "gakuat":   "tidak kuat",
    "gamungkin":"tidak mungkin",
}

# Conjunctions, prepositions, and formal abbreviations
_CONJUNCTIONS: Dict[str, str] = {
    "tp":     "tapi",
    "tpi":    "tapi",
    "trs":    "terus",
    "trus":   "terus",
    "dr":     "dari",
    "sm":     "sama",
    "ama":    "sama",
    "dpt":    "dapat",
    "tdk":    "tidak",
    "krn":    "karena",
    "krna":   "karena",
    "karna":  "karena",
    "utk":    "untuk",
    "bwt":    "buat",
    "spy":    "supaya",
    "klo":    "kalau",
    "kalo":   "kalau",
    "yg":     "yang",
    "dgn":    "dengan",
    "dg":     "dengan",
    "jg":     "juga",
    "bkn":    "bukan",
    "pd":     "pada",
    "dlm":    "dalam",
    # Formal abbreviations
    "dll":    "dan lain-lain",
    "dsb":    "dan sebagainya",
    "dst":    "dan seterusnya",
    "tsb":    "tersebut",
    "yth":    "yang terhormat",
    "nb":     "catatan",
    # Time-relation conjunctions
    "stlh":   "setelah",
    "sblm":   "sebelum",
    "slma":   "selama",
    "tntg":   "tentang",
    "ttng":   "tentang",
    "thd":    "terhadap",
    "antr":   "antara",
    "srt":    "serta",
    "kmdian": "kemudian",
    "kmdn":   "kemudian",
    "lalu":   "kemudian",
    # Formal/business abbreviations
    "ttd":    "tanda tangan",
    "an":     "atas nama",
    "up":     "untuk perhatian",
    "re":     "balasan",
    "fwd":    "teruskan",
    "fw":     "teruskan",
    "lmk":    "beri tahu saya",
    "etc":    "dan lain-lain",
    "ps":     "catatan tambahan",
    "no":     "nomor",
}

# Verbs and auxiliary verbs
_VERBS: Dict[str, str] = {
    "udh":       "sudah",
    "sdh":       "sudah",
    "dah":       "sudah",
    "udah":      "sudah",
    "udeh":      "sudah",
    "blm":       "belum",
    "blum":      "belum",
    "lg":        "sedang",
    "lgi":       "sedang",
    "bs":        "bisa",
    "bsa":       "bisa",
    "jd":        "jadi",
    "mo":        "mau",
    "mw":        "mau",
    "tau":       "tahu",
    "taw":       "tahu",
    "pake":      "pakai",
    "make":      "pakai",
    "mkn":       "makan",
    "mkan":      "makan",
    "liat":      "lihat",
    "liad":      "lihat",
    "ngerti":    "mengerti",
    "ngarti":    "mengerti",
    "nanya":     "bertanya",
    "nyari":     "mencari",
    "nyoba":     "mencoba",
    "ngomong":   "berbicara",
    "nunggu":    "menunggu",
    "lakuin":    "lakukan",
    "byr":       "bayar",
    "hrs":       "harus",
    "blh":       "boleh",
    "prlu":      "perlu",
    "blg":       "bilang",
    "sk":        "suka",
    "dtg":       "datang",
    "dateng":    "datang",
    # Extended verbs
    "bikin":     "membuat",
    "bkin":      "membuat",
    "kasih":     "berikan",
    "ksih":      "berikan",
    "ambl":      "ambil",
    "simpen":    "simpan",
    "smpen":     "simpan",
    "masukin":   "masukkan",
    "keluarin":  "keluarkan",
    "tambahin":  "tambahkan",
    "kurangin":  "kurangi",
    "hapusin":   "hapuskan",
    "benerin":   "betulkan",
    "gnti":      "ganti",
    "pndh":      "pindah",
    "plng":      "pulang",
    "brngkt":    "berangkat",
    "balik":     "kembali",
    "blk":       "kembali",
    "nyampe":    "sampai",
    "nyampek":   "sampai",
    "smpe":      "sampai",
    "sampe":     "sampai",
    "ketemu":    "bertemu",
    "ktmu":      "bertemu",
    "ngikut":    "ikut",
    "ikutin":    "ikuti",
    "dengerin":  "dengarkan",
    "denger":    "dengar",
    "dnger":     "dengar",
    "lpd":       "lupa",
    "inget":     "ingat",
    "ngelupain": "melupakan",
    "ngebantu":  "membantu",
    "bntu":      "bantu",
    "cek":       "periksa",
    "ngecek":    "memeriksa",
    "cobaain":   "coba",
    "ngelakuin": "melakukan",
    "mnta":      "minta",
    "mintain":   "mintakan",
    "krm":       "kirim",
    "kirimin":   "kirimkan",
    "bli":       "beli",
    "beliin":    "belikan",
    "jln":       "jalan",
    "maen":      "main",
    "nemenin":   "menemani",
    "temenin":   "menemani",
    "temenan":   "berteman",
    "kenalan":   "berkenalan",
    "ngobrol":   "mengobrol",
    "ngopi":     "minum kopi",
    "nitip":     "titip",
    "titipin":   "titipkan",
    "bayarin":   "bayarkan",
    "bljr":      "belajar",
    "bljar":     "belajar",
    "ngajar":    "mengajar",
    "ngjar":     "mengajar",
}

# Adjectives, adverbs, and discourse particles
_ADJECTIVES_ADVERBS: Dict[str, str] = {
    "bgt":      "banget",
    "bngt":     "banget",
    "bnget":    "banget",
    "bget":     "banget",
    "bet":      "banget",
    "amet":     "amat",
    "bener":    "benar",
    "bnr":      "benar",
    "bner":     "benar",
    "cepet":    "cepat",
    "ttp":      "tetap",
    "lbh":      "lebih",
    "krg":      "kurang",
    "sdkt":     "sedikit",
    "dikit":    "sedikit",
    "dkit":     "sedikit",
    "hny":      "hanya",
    "bbrp":     "beberapa",
    "emg":      "memang",
    "emang":    "memang",
    "aja":      "saja",
    "doang":    "saja",
    "kek":      "seperti",
    "kayak":    "seperti",
    "kyk":      "seperti",
    "syg":      "sayang",
    # Common informal particles mapped to nearest standard equivalent
    "nih":      "ini",
    "tuh":      "itu",
    "yuk":      "ayo",
    "ae":       "saja",         # Sundanese/Javanese particle
    "wae":      "saja",         # Sundanese: just/only
    "tok":      "saja",         # Javanese: only
    # Extended adjectives/adverbs
    "abis":     "habis",
    "abish":    "habis",
    "hbs":      "habis",
    "pol":      "sekali",
    "beneran":  "sungguhan",
    "lm":       "lama",
    "lame":     "lama",
    "trllu":    "terlalu",
    "tll":      "terlalu",
    "ckp":      "cukup",
    "smpt":     "sempat",
    "prnh":     "pernah",
    "srg":      "sering",
    "jrng":     "jarang",
    "sllu":     "selalu",
    "slalu":    "selalu",
    "kdng":     "kadang",
    "mgkn":     "mungkin",
    "pst":      "pasti",
    "trnyta":   "ternyata",
    "trnyata":  "ternyata",
    "lgsg":     "langsung",
    "lngsng":   "langsung",
    "mlh":      "malah",
    "pdhl":     "padahal",
    "pdhal":    "padahal",
    "pdahl":    "padahal",
    "slnya":    "soalnya",
    "gitu":     "begitu",
    "gt":       "begitu",
    "gini":     "begini",
    "gn":       "begini",
    "bnyk":     "banyak",
    "byk":      "banyak",
    "bnyak":    "banyak",
    "sdkit":    "sedikit",
    "bgs":      "bagus",
    "bgus":     "bagus",
    "bagoes":   "bagus",
    "jlk":      "jelek",
    "jlek":     "jelek",
    "kcewa":    "kecewa",
    "mhl":      "mahal",
    "mhal":     "mahal",
    "mahl":     "mahal",
    "mrh":      "murah",
    "lmyn":     "lumayan",
    "lumyn":    "lumayan",
    "lmyan":    "lumayan",
    "mayan":    "lumayan",
    "enk":      "enak",
    "mntap":    "mantap",
    "asik":     "asyik",
    "cpk":      "capai",
    "cape":     "capai",
    "lela":     "lelah",
    "ngantu":   "mengantuk",
    "laper":    "lapar",
    "skt":      "sakit",
    "smbh":     "sembuh",
    "seneng":   "senang",
    "sneng":    "senang",
    "bhgia":    "bahagia",
    "tkt":      "takut",
    "bngun":    "bingung",
    "psng":     "pusing",
    "mls":      "malas",
    "rjn":      "rajin",
    "sbnrnya":  "sebenarnya",
    "sbnr":     "sebenarnya",
    "mending":  "lebih baik",
    "kyknya":   "sepertinya",
    "sptnya":   "sepertinya",
    "sprtnya":  "sepertinya",
    "gitu2":    "begitu-begitu",
    "pelan2":   "pelan-pelan",
    "lama2":    "lama-lama",
    "buru2":    "terburu-buru",
    "kwalitas": "kualitas",
}

# Question words
_QUESTION_WORDS: Dict[str, str] = {
    "knp":     "kenapa",
    "gmn":     "bagaimana",
    "gimana":  "bagaimana",
    "gmna":    "bagaimana",
    "gimna":   "bagaimana",
    "kmn":     "kemana",
    "dmn":     "di mana",
    "drmn":    "dari mana",
    "drmana":  "dari mana",
    "kpn":     "kapan",
    "manaa":   "mana",
    # Sundanese question words
    "kumaha":  "bagaimana",
    "naon":    "apa",
    "saha":    "siapa",
    "iraha":   "kapan",
    "kamana":  "kemana",
}

# Greetings, affirmations, and common social responses
_GREETINGS_RESPONSES: Dict[str, str] = {
    # Thanks
    "makasih":      "terima kasih",
    "makasi":       "terima kasih",
    "mksh":         "terima kasih",
    "mksih":        "terima kasih",
    "trims":        "terima kasih",
    "thx":          "terima kasih",
    "tq":           "terima kasih",
    "ty":           "terima kasih",
    "trimakasih":   "terima kasih",
    "terimakasih":  "terima kasih",
    "mkch":         "terima kasih",
    "tengkyu":      "terima kasih",
    "tengkyuu":     "terima kasih",
    # Requests
    "pls":          "tolong",
    "pliss":        "tolong",
    "plz":          "tolong",
    "plzz":         "tolong",
    "tlg":          "tolong",
    # Apology
    "mf":           "maaf",
    "afwan":        "maaf",         # Arabic-Indonesian
    "maap":         "maaf",
    "sori":         "maaf",
    "sory":         "maaf",
    "sorry":        "maaf",
    "sorri":        "maaf",
    "mnt maaf":     "minta maaf",
    # Agreement
    "ok":           "oke",
    "okk":          "oke",
    "okee":         "oke",
    "okelah":       "oke",
    "sip":          "baik",
    "siapp":        "siap",
    "iy":           "iya",
    "iyap":         "iya",
    "yap":          "ya",
    "yep":          "ya",
    "yup":          "ya",
    "yupp":         "ya",
    "yeah":         "ya",
    "yoi":          "iya",          # Jakartan slang
    "mantul":       "mantap betul",
    # Greetings
    "hi":           "hai",
    "hey":          "hei",
    "met pagi":     "selamat pagi",
    "met siang":    "selamat siang",
    "met sore":     "selamat sore",
    "met malam":    "selamat malam",
    "slmt dtng":    "selamat datang",
    "smpai jumpa":  "sampai jumpa",
    "dadah":        "sampai jumpa",
    "dah":          "sampai jumpa",
    "bye":          "selamat tinggal",
    "byee":         "selamat tinggal",
    "byebye":       "selamat tinggal",
    "ciao":         "selamat tinggal",
    "papay":        "selamat tinggal",
    # Javanese / Sundanese particles (polite registers)
    "nggih":        "iya",          # Javanese: yes (polite)
    "inggih":       "iya",          # Javanese: yes (formal)
    "mboten":       "tidak",        # Javanese: no/not
    "monggo":       "silakan",      # Javanese: please go ahead
    "suwun":        "terima kasih", # Javanese: thank you
    "matur suwun":  "terima kasih", # Javanese: thank you (full form)
    "nuwun":        "terima kasih", # Javanese: thank you
    # Sundanese
    "muhun":        "iya",
    "hapunten":     "maaf",
    "punten":       "permisi",
    "hatur nuhun":  "terima kasih",
    # Arabic-Indonesian
    "syukron":      "terima kasih",
    # Polite expressions
    "prmisi":       "permisi",
    "silahkan":     "silakan",
    "samasama":     "sama-sama",
    "samsama":      "sama-sama",
    "sama sama":    "sama-sama",
}

# Temporal expressions and locations
_TEMPORAL_LOCATION: Dict[str, str] = {
    "skrg":  "sekarang",
    "skrng": "sekarang",
    "ntr":   "nanti",
    "ntar":  "nanti",
    "kmrn":  "kemarin",
    "kmren": "kemarin",
    "bsk":   "besok",
    "td":    "tadi",
    "dlu":   "dulu",
    "dlo":   "dulu",
    "hr":    "hari",
    "hri":   "hari",
    "mlm":   "malam",
    "malem": "malam",
    "pg":    "pagi",
    "sni":   "sini",
    "dsini": "di sini",
    "dsni":  "di sini",
    "sono":  "sana",
    "mgg":   "minggu",
    "bln":   "bulan",
    "thn":   "tahun",
    "mnt":   "menit",
    "dtk":   "detik",
    "jdwl":  "jadwal",
    "wktu":  "waktu",
}

# Internet slang — mapped to Indonesian equivalents (not English)
_INTERNET_SLANG: Dict[str, str] = {
    "otw":       "dalam perjalanan",
    "btw":       "omong-omong",
    "fyi":       "sebagai informasi",
    "imo":       "menurut saya",
    "imho":      "menurut saya",
    "cmiiw":     "koreksi jika saya salah",
    "lol":       "tertawa",
    "wkwk":      "tertawa",
    "wkwwk":     "tertawa",
    "wkwkwk":    "tertawa",
    "awokwok":   "tertawa",
    "xixi":      "tertawa",     # Chinese laughter, common in Indonesian social media
    "lmao":      "tertawa keras",
    "omg":       "astaga",
    "idk":       "saya tidak tahu",
    "tbh":       "sejujurnya",
    "ngl":       "sejujurnya",
    "tbf":       "sejujurnya",
    "nvm":       "lupakan saja",
    "jk":        "bercanda",
    "np":        "tidak masalah",
    "afk":       "pergi sebentar",
    "brb":       "segera kembali",
    "dm":        "pesan langsung",
    "tldr":      "ringkasnya",
    "wdyt":      "menurutmu",
    "wdym":      "apa maksudmu",
    "ftr":       "akhirnya",
    # Platforms
    "wa":        "whatsapp",
    "ig":        "instagram",
    "fb":        "facebook",
    "tt":        "tiktok",
    "yt":        "youtube",
    "twit":      "twitter",
    "linkin":    "linkedin",
    "gform":     "google form",
    "gdrive":    "google drive",
    "gmeet":     "google meet",
    # Social media terms
    "wag":       "grup whatsapp",
    "gc":        "grup chat",
    "bc":        "pesan siaran",
    "nohp":      "nomor handphone",
    "ootd":      "pakaian hari ini",
    "vibe":      "suasana",
    "vibes":     "suasana",
    "mood":      "suasana hati",
    "hype":      "heboh",
    "trending":  "sedang tren",
    "lowkey":    "diam-diam",
    "highkey":   "terang-terangan",
}

# E-commerce and finance terms
_ECOMMERCE_FINANCE: Dict[str, str] = {
    "gan":    "saudara",
    "sis":    "saudari",
    "rekber": "rekening bersama",
    "cod":    "bayar di tempat",
    "ongkir": "ongkos kirim",
    "tf":     "transfer",
    "dp":     "uang muka",
    "hrg":    "harga",
    "hrga":   "harga",
    "jastip": "jasa titip",
    "pesen":  "pesan",
    "minat":  "berminat",
    "duit":   "uang",
    "duwit":  "uang",
    "fulus":  "uang",
    "rb":     "ribu",
    "jt":     "juta",
    "mlyr":   "miliar",
    "pcs":    "buah",
    "lbr":    "lembar",
    "btl":    "botol",
    "asap":   "sesegera mungkin",
    "acc":    "disetujui",
    "bkl":    "bakal",
    "bakal":  "akan",
    "mslh":   "masalah",
    "sls":    "selesai",
    "slsai":  "selesai",
    "mlai":   "mulai",
    "mulain": "mulai",
}

# Youth / Gen-Z Indonesian slang
_YOUTH_SLANG: Dict[str, str] = {
    "mager":    "malas bergerak",
    "baper":    "bawa perasaan",
    "gabut":    "tidak ada kegiatan",
    "kepo":     "ingin tahu",
    "santuy":   "santai",
    "woles":    "santai",
    "gercep":   "gerak cepat",
    "gass":     "ayo",
    "gaspol":   "ayo semangat",
    "gaskeun":  "ayo lakukan",     # Sundanese-influenced
    "bucin":    "budak cinta",
    "julid":    "iri hati",
    "halu":     "halusinasi",
    "flexing":  "pamer",
    "pansos":   "panjat sosial",
    "curhat":   "berbagi cerita",
    "kekinian": "tren terkini",
    "kekinan":  "tren terkini",
    "hits":     "populer",
    "relate":   "relatable",
    "selfie":   "foto sendiri",
    "caption":  "keterangan foto",
    "story":    "cerita",
    "feeds":    "beranda",
}

# Discourse markers and meta-commentary
_DISCOURSE_MARKERS: Dict[str, str] = {
    "mksd":       "maksud",
    "mksdnya":    "maksudnya",
    "pkoknya":    "pokoknya",
    "pokonya":    "pokoknya",
    "jdinya":     "jadinya",
    "hslnya":     "hasilnya",
    "sngktnya":   "singkatnya",
    "menurutku":  "menurut saya",
    "mnrtku":     "menurut saya",
    "menurutgw":  "menurut saya",
    "akhirny":    "akhirnya",
}

# Javanese extended vocabulary
_JAVANESE_EXTENDED: Dict[str, str] = {
    # Pronouns
    "awakmu":   "kamu",
    "njenengan":"anda",
    "kulo":     "saya",
    "kula":     "saya",
    "inyong":   "saya",
    "dewek":    "sendiri",
    # Adjectives
    "apik":     "bagus",
    "elek":     "jelek",
    "okeh":     "banyak",
    "sithik":   "sedikit",
    "gedhe":    "besar",
    "cilik":    "kecil",
    "adoh":     "jauh",
    "cedhak":   "dekat",
    "alon":     "pelan",
    "anyar":    "baru",
    "lawas":    "lama",
    "sae":      "baik",
    # Verbs
    "mangkat":  "berangkat",
    "kondur":   "pulang",
    "mangan":   "makan",
    "ngombe":   "minum",
    "turu":     "tidur",
    "tangi":    "bangun",
    "mlaku":    "berjalan",
    "mlayu":    "berlari",
    "lungguh":  "duduk",
    "ngadeg":   "berdiri",
    "weruh":    "tahu",
    "krungu":   "dengar",
    "ndelok":   "lihat",
    "takon":    "bertanya",
    "kandha":   "berkata",
    "tuku":     "beli",
    "adol":     "jual",
}

# Sundanese extended vocabulary
_SUNDANESE_EXTENDED: Dict[str, str] = {
    # Pronouns
    "abdi":       "saya",
    "anjeun":     "kamu",
    "maneh":      "kamu",
    # Particles
    "atuh":       "dong",
    "euy":        "ya",
    "mah":        "sih",
    "teh":        "itu",
    "nya":        "ya",
    # Adjectives
    "alus":       "bagus",
    "awon":       "jelek",
    "caket":      "dekat",
    "leueur":     "lambat",
    "sae pisan":  "sangat bagus",
    # Verbs/expressions
    "geus":       "sudah",
    "keur":       "sedang",
    "bade":       "akan",
    "hoyong":     "mau",
    "daek":       "mau",
    "tiasa":      "bisa",
    "aya":        "ada",
    "teu":        "tidak",
    "acan":       "belum",
    "can":        "belum",
    # Quantity
    "loba":       "banyak",
    "saeutik":    "sedikit",
    "ged\u00e9":  "besar",
    "leutik":     "kecil",
}

# Common nouns (abbreviations and informal forms)
_NOUNS: Dict[str, str] = {
    # People & relationships
    "tmn":    "teman",
    "temen":  "teman",
    "tmn2":   "teman-teman",
    "temen2": "teman-teman",
    "shbt":   "sahabat",
    "pcr":    "pacar",
    "mntm":   "mantan",
    # Work & study
    "krjn":   "pekerjaan",
    "kntr":   "kantor",
    "sklh":   "sekolah",
    "kmps":   "kampus",
    "kliah":  "kuliah",
    "tgs":    "tugas",
    "pr":     "pekerjaan rumah",
    "ujin":   "ujian",
    "ulngn":  "ulangan",
    "mhsw":   "mahasiswa",
    "mhs":    "mahasiswa",
    "mrd":    "murid",
    "kls":    "kelas",
    "mapel":  "mata pelajaran",
    "matkul": "mata kuliah",
    "mtkl":   "mata kuliah",
    "skrpsi": "skripsi",
    "wsd":    "wisuda",
    "nlai":   "nilai",
    "ipk":    "indeks prestasi kumulatif",
    "ip":     "indeks prestasi",
    "dl":     "batas waktu",
    "prsnts": "presentasi",
    "lprn":   "laporan",
    "rvisi":  "revisi",
    # Things & gadgets
    "hp":     "handphone",
    "hape":   "handphone",
    "ltop":   "laptop",
    "mtr":    "motor",
    "mbl":    "mobil",
    "rmh":    "rumah",
    "mkn":    "makan",
    "mnum":   "minum",
    # Places
    "wrg":    "warung",
    "warteg": "warung tegal",
    "psr":    "pasar",
    "gdg":    "gedung",
    "rs":     "rumah sakit",
    "pskms":  "puskesmas",
}

# Health & wellness vocabulary
_HEALTH: Dict[str, str] = {
    # Symptoms
    "dmm":     "demam",
    "btk":     "batuk",
    "plk":     "pilek",
    "ml":      "mual",
    "mntah":   "muntah",
    "alrgi":   "alergi",
    "sesak":   "sesak napas",
    "sktkpl":  "sakit kepala",
    "mencret": "diare",
    "mules":   "mulas",
    "lebam":   "memar",
    "kslng":   "keseleo",
    # Medical personnel & places
    "obt":     "obat",
    "dkter":   "dokter",
    "dr":      "dokter",
    "prwt":    "perawat",
    "rwt":     "rawat",
    "opname":  "rawat inap",
    "ugd":     "unit gawat darurat",
    "igd":     "instalasi gawat darurat",
    "poli":    "poliklinik",
    "apotk":   "apotek",
    "resep":   "resep dokter",
    "rsep":    "resep dokter",
    "rapid test":"tes cepat",
    # Wellness & fitness
    "jalan2":  "jalan-jalan",
    "olrga":   "olahraga",
    "gym":     "olahraga",
    "lari":    "berlari",
    "jogging": "joging",
    "tdr":     "tidur",
    "tdrsiang":"tidur siang",
    "bgdng":   "begadang",
    "istrhat": "istirahat",
    "istrht":  "istirahat",
    "shat":    "sehat",
    "smbh":    "sembuh",
    "lekas sembuh": "lekas sembuh",
    "cpt smbh":"lekas sembuh",
    "get well soon": "lekas sembuh",
    "gws":     "lekas sembuh",
    "isoman":  "isolasi mandiri",
}

# Emotions, feelings & expressions
_EMOTIONS_EXPRESSIONS: Dict[str, str] = {
    # Happiness / excitement
    "happy":     "bahagia",
    "excited":   "bersemangat",
    "semngt":    "semangat",
    "smngat":    "semangat",
    "smgt":      "semangat",
    "bersemgt":  "bersemangat",
    "yey":       "hore",
    "yeay":      "hore",
    "yay":       "hore",
    "asoy":      "asyik",
    "krn2":      "keren-keren",
    "mantab":    "mantap",
    "gokil":     "luar biasa",
    "gila":      "luar biasa",
    "gile":      "luar biasa",
    "gilak":     "luar biasa",
    "parah":     "luar biasa",
    "lebay":     "berlebihan",
    "lbay":      "berlebihan",
    # Sadness / disappointment
    "sdh2":      "sedih",
    "kcewa":     "kecewa",
    "kzl":       "kesal",
    "bete":      "kesal",
    "bt":        "kesal",
    "gondok":    "kesal",
    "sewot":     "kesal",
    "jutek":     "judes",
    "nangis":    "menangis",
    "nangiss":   "menangis",
    "mewek":     "menangis",
    "ngedumel":  "mengeluh",
    "ngeluh":    "mengeluh",
    "ngrundel":  "mengeluh",
    "geregetan": "kesal",
    "gereget":   "kesal",
    "dongkol":   "kesal",
    "badmood":   "suasana hati buruk",
    "bad mood":  "suasana hati buruk",
    "overthink": "terlalu banyak pikiran",
    "otk":       "terlalu banyak pikiran",
    "down":      "sedang terpuruk",
    "ngedown":   "sedang terpuruk",
    "insecure":  "tidak percaya diri",
    "minder":    "rendah diri",
    # Surprise / shock
    "shock":     "syok",
    "bnggong":   "bengong",
    "melongo":   "terpana",
    "bnggung":   "bingung",
    "mumet":     "pusing",
    "mupeng":    "sangat menginginkan",
    # Love / affection
    "syangku":   "sayangku",
    "cintrong":  "cinta",
    "gebetan2":  "gebetan-gebetan",
    "pdkt":      "pendekatan",
    "chat":      "pesan",
    "dm2":       "kirim pesan langsung",
    "ghosting":  "menghilang tiba-tiba",
    "ghosted":   "ditinggal tiba-tiba",
    "friendzone":"zona teman",
    "fz":        "zona teman",
    "crush":     "orang yang disukai",
    "clbk":      "cinta lama bersemi kembali",
    "php":       "pemberi harapan palsu",
    "playing":   "mempermainkan",
    "dimainin":  "dipermainkan",
    "selingkuh": "berselingkuh",
    "selingkuhi":"berselingkuhi",
    "selingkuhan":"perselingkuhan",
    "putusin":   "memutuskan",
    "balikan":   "bersama kembali",
    # Tired / lazy
    "capek":     "lelah",
    "capai":     "lelah",
    "kecapean":  "kelelahan",
    "nganggur":  "tidak bekerja",
    "males":     "malas",
    "mager":     "malas bergerak",
    "rebahan":   "berbaring santai",
    "santey":    "santai",
    "ndak":      "tidak",
    "enggak":    "tidak",
}

# Food & drink vocabulary
_FOOD_DRINK: Dict[str, str] = {
    # General food terms
    "mkan":      "makan",
    "mkanan":    "makanan",
    "lauk":      "lauk-pauk",
    "ns":        "nasi",
    "sayur":     "sayuran",
    "syr":       "sayuran",
    "mie":       "mi",
    "mie2":      "mie-mie",
    "indomie":   "mi instan",
    "indmie":    "mi instan",
    "indomie goreng": "mi goreng instan",
    "migo":      "mi goreng",
    "migor":     "mi goreng",
    "nasgor":    "nasi goreng",
    "nsgr":      "nasi goreng",
    "molen":     "kue molen",
    "grngn":     "gorengan",
    "batagor":   "bakso tahu goreng",
    "cireng":    "aci goreng",
    "cilok":     "aci dicolok",
    "baso":      "bakso",
    "bks":       "bakso",
    "gado2":     "gado-gado",
    "blr":       "bubur",
    "nsuduk":    "nasi uduk",
    "warteg":    "warung tegal",
    "wrtg":      "warung tegal",
    # Drinks
    "mnum":      "minum",
    "mnuman":    "minuman",
    "kpi":       "kopi",
    "tehmanis":  "teh manis",
    "juice":     "jus",
    "bubble tea":"boba teh",
    "kopsu":     "kopi susu",
    "americano": "kopi americano",
    "minol":     "minuman beralkohol",
    # Taste / quality
    "enakk":     "enak",
    "mantul":    "mantap betul",
    "kriuk":     "renyah",
    "pedes":     "pedas",
    "asem":      "asam",
    "bukan enak":"tidak enak",
    "gaenak":    "tidak enak",
    "ga enak":   "tidak enak",
    "keabisan":  "kehabisan",
    "khabisan":  "kehabisan",
    # Meal times / hunger
    "makanmalam": "makan malam",
    "srpn":      "sarapan",
    "malem":     "malam",
    "laper":     "lapar",
    "laperan":   "sedang lapar",
    "kelaperan": "sangat lapar",
    "ngidam":    "mengidam",
    "nagih":     "ketagihan",
    "kenyangn":  "kekenyangan",
}

# Clothing & fashion vocabulary
_CLOTHING_FASHION: Dict[str, str] = {
    # Garments
    "bj":        "baju",
    "kaos":      "kaus",
    "kos":       "kaus",
    "kmja":      "kemeja",
    "jket":       "jaket",
    "cln":       "celana",
    "dress":     "gaun",
    "jlbb":      "jilbab",
    "hijaber":   "pengguna hijab",
    "krdng":     "kerudung",
    "koko":      "baju koko",
    "pjm":       "piyama",
    "sweter":    "sweater",
    "hudi":      "hoodie",
    "cardigan":  "kardigan",
    "outer":     "jaket luar",
    "outher":    "jaket luar",
    "vest":      "rompi",
    # Footwear
    "spt2":      "sepatu-sepatu",
    "sdl":       "sandal",
    "sneakers":  "sepatu kets",
    "snakers":   "sepatu kets",
    "boots":     "sepatu bot",
    "heels":     "sepatu hak tinggi",
    "higheels":  "sepatu hak tinggi",
    "flatshoes": "sepatu flat",
    "slippers":  "sandal",
    # Accessories
    "tote bag":  "tas tote",
    "totebag":   "tas tote",
    "dmpt":      "dompet",
    "jamtgn":    "jam tangan",
    "kacmt":     "kacamata",
    # Fashion terms
    "outfit":    "pakaian",
    "ootd":      "pakaian hari ini",
    "mix match": "padupadan",
    "mixmatch":  "padupadan",
    "casual":    "kasual",
    "stylish":   "bergaya",
    "trendy":    "trendi",
    "vintage":   "jadul bergaya",
    "thrift":    "beli baju bekas",
    "thrifting": "belanja baju bekas",
    "preloved":  "bekas pakai",
    "ukrn":      "ukuran",
    "size":      "ukuran",
    "kebesaran": "terlalu besar",
    "kekecilan": "terlalu kecil",
}

# Transportation vocabulary
_TRANSPORTATION: Dict[str, str] = {
    # Vehicles
    "mtr":       "motor",
    "mbl":       "mobil",
    "spd":       "sepeda",
    "angkot":    "angkutan kota",
    "busway":    "bus transjakarta",
    "tj":        "transjakarta",
    "krl":       "kereta rel listrik",
    "mrt":       "mass rapid transit",
    "lrt":       "light rail transit",
    "commuter":  "kereta komuter",
    "komuter":   "kereta komuter",
    "pswt":      "pesawat",
    "bdr":       "bandara",
    "kpl":       "kapal",
    "ojol":      "ojek online",
    "taxi":      "taksi",
    "bentor":    "becak motor",
    "bnsn":      "bensin",
    "bbm":       "bahan bakar minyak",
    # Navigation / travel
    "jln":       "jalan",
    "mct":       "macet",
    "plkmpng":   "pulang kampung",
    "prjlnan":   "perjalanan",
    "jrk":       "jarak",
    "deket":     "dekat",
    "prk":       "parkir",
    "numpang":   "menumpang",
    "nunut":     "menumpang",
    "nebeng":    "menumpang",
    "nyetir":    "mengemudi",
    "nyupir":    "mengemudikan",
    "setir":     "kemudi",
    "spion":     "kaca spion",
    "gps":       "navigasi",
    "maps":      "peta navigasi",
    "gmaps":     "google maps",
}

# Religion, culture & social life
_RELIGION_CULTURE: Dict[str, str] = {
    # Islamic expressions (very common in Indonesian daily speech)
    "insyaallah": "insya allah",
    "inshallah":  "insya allah",
    "ia":         "insya allah",
    "alhdlh":     "alhamdulillah",
    "alhdlll":    "alhamdulillah",
    "amdlh":      "alhamdulillah",
    "alhamdu":    "alhamdulillah",
    "masyaallah": "masya allah",
    "subhankl":   "subhanallah",
    "astagfirullah": "astaghfirullah",
    "astghfr":    "astaghfirullah",
    "bsmllh":     "bismillah",
    "bismillahirrahmanirrahim": "bismillah",
    "allahuakbar": "allahu akbar",
    "aamiin":     "amin",
    "aminn":      "amin",
    "jazakallah": "semoga Allah membalas kebaikanmu",
    "jazakallahu khair": "semoga Allah membalas kebaikanmu",
    "barakallah": "semoga Allah memberkahimu",
    "sholat":     "salat",
    "solat":      "salat",
    "shalat":     "salat",
    "bukpus":     "buka puasa",
    "bukber":     "buka bersama",
    "ramadhan":   "ramadan",
    "idulfitri":  "idul fitri",
    "eid":        "lebaran",
    "fitrah":     "zakat fitrah",
    "msdjd":      "masjid",
    "mushola":    "musala",
    "musholla":   "musala",
    "psntrn":     "pesantren",
    "ustadz":     "ustaz",
    "ustad":      "ustaz",
    "kyai":       "kiai",
    # National / cultural
    "bhineka":    "bhinneka",
    "17an":       "tujuh belasan",
    "hut ri":     "hari ulang tahun republik indonesia",
    "hutri":      "hari ulang tahun republik indonesia",
    # Events / celebrations
    "ultah":      "ulang tahun",
    "ulangtahun": "ulang tahun",
    "ultahku":    "ulang tahunku",
    "happy birthday": "selamat ulang tahun",
    "hbd":        "selamat ulang tahun",
    "hbday":      "selamat ulang tahun",
    "met ultah":  "selamat ulang tahun",
    "met ulth":   "selamat ulang tahun",
    "wedding":    "pernikahan",
    "nikah":      "menikah",
    "nikahin":    "menikahkan",
    "tunang":     "tunangan",
    "akad":       "akad nikah",
    "undngn":     "undangan",
    "kondangan":  "menghadiri pernikahan",
    "kondngan":   "kondangan",
    "ngaji":      "mengaji",
}

# Education extended vocabulary
_EDUCATION_EXTENDED: Dict[str, str] = {
    # School levels
    "sd":        "sekolah dasar",
    "smp":       "sekolah menengah pertama",
    "sma":       "sekolah menengah atas",
    "smk":       "sekolah menengah kejuruan",
    "univ":      "universitas",
    "univrsitas":"universitas",
    "kampus":    "kampus",
    "kuliah":    "kuliah",
    "mhsw":      "mahasiswa",
    "dsn":       "dosen",
    "gr":        "guru",
    "kepsek":    "kepala sekolah",
    "kpsek":     "kepala sekolah",
    # Academic activities
    "bljar":     "belajar",
    "bljr":      "belajar",
    "ngajar":    "mengajar",
    "ngjar":     "mengajar",
    "ulngn":     "ulangan",
    "tgs":       "tugas",
    "pr":        "pekerjaan rumah",
    "homework":  "pekerjaan rumah",
    "hw":        "pekerjaan rumah",
    "presntsi":  "presentasi",
    "prsnts":    "presentasi",
    "laporan":   "laporan",
    "lprn":      "laporan",
    "mklh":      "makalah",
    "skrpsi":    "skripsi",
    "thesis":    "tesis",
    "wsuda":    "wisuda",
    "wsda":    "wisuda",
    "wsd":       "wisuda",
    "yudisium":  "yudisium",
    "ospek":     "orientasi studi",
    "maba":      "mahasiswa baru",
    "mhs baru":  "mahasiswa baru",
    # Grades & results
    "nilai":     "nilai",
    "nlai":      "nilai",
    "rapor":     "rapor",
    "raport":    "rapor",
    "ipk":       "indeks prestasi kumulatif",
    "ip":        "indeks prestasi",
    "llus":     "lulus",
    "lls":       "lulus",
    "ggal":     "gagal",
    "ggl":       "gagal",
    "remedial":  "remedial",
    "remidi":    "remedial",
    "ngulang":   "mengulang",
    "nunggak":   "tidak naik kelas",
    "naikin":    "menaikkan",
    "beasiwa":   "beasiswa",
    "bsw":       "beasiswa",
    "beasiswaku":"beasiswaku",
    "daftar":    "daftar",
    "dft":       "daftar",
    "pendaftran":"pendaftaran",
    "pendftran": "pendaftaran",
    "pndftran": "pendaftaran",
    "pndftran":  "pendaftaran",
    "sleksi":    "seleksi",
    "slksi":     "seleksi",
    "snbt":      "seleksi nasional berdasarkan tes",
    "utbk":      "ujian tulis berbasis komputer",
    "sbmptn":    "seleksi bersama masuk perguruan tinggi negeri",
    "ppdb":      "penerimaan peserta didik baru",
    "bimbel":    "bimbingan belajar",
    "bmbl":      "bimbingan belajar",
    "tryout":    "uji coba",
    "to":        "uji coba",
}

# Work & office vocabulary
_WORK_OFFICE: Dict[str, str] = {
    # Job types & positions
    "krja":      "kerja",
    "kerjaan":   "pekerjaan",
    "krjaan":    "pekerjaan",
    "kntr":      "kantor",
    "prusahaan": "perusahaan",
    "prshn":     "perusahaan",
    "bos":       "atasan",
    "boss":      "atasan",
    "rekan":     "rekan kerja",
    "krywn":     "karyawan",
    "pgwai":     "pegawai",
    "pns":       "pegawai negeri sipil",
    "asn":       "aparatur sipil negara",
    "honorer":   "tenaga honorer",
    "freelance": "pekerja lepas",
    "frilens":   "pekerja lepas",
    "wfh":       "kerja dari rumah",
    "wfo":       "kerja dari kantor",
    "wfa":       "kerja dari mana saja",
    "remote":    "kerja jarak jauh",
    "hybrid":    "kerja hibrida",
    "intern":    "magang",
    "mgang":     "magang",
    "kntrak":    "kontrak",
    "resign":    "mengundurkan diri",
    "resignasi": "pengunduran diri",
    "phk":       "pemutusan hubungan kerja",
    # Work activities
    "rpt":       "rapat",
    "meeting":   "rapat",
    "mtg":       "rapat",
    "zoom":      "rapat video",
    "gmeet":     "google meet",
    "deadline":  "batas waktu",
    "dl":        "batas waktu",
    "dl nya":    "batas waktunya",
    "submit":    "kirimkan",
    "sbmt":      "kirimkan",
    "rvisi":     "revisi",
    "approval":  "persetujuan",
    "approved":  "disetujui",
    "acc":       "disetujui",
    "reject":    "ditolak",
    "feedback":  "masukan",
    "ftdbk":     "masukan",
    "report":    "laporan",
    "update":    "perbarui",
    "followup":  "tindak lanjut",
    "fu":        "tindak lanjut",
    "asap":      "sesegera mungkin",
    "urgent":    "mendesak",
    "priority":  "prioritas",
    "prio":      "prioritas",
    "kpi":       "indikator kinerja utama",
    "okr":       "tujuan dan hasil kunci",
    "brainstorm":"curah gagasan",
    "brnstrm":   "curah gagasan",
    # Finance / salary
    "gji":       "gaji",
    "gajinya":   "gajinya",
    "thr":       "tunjangan hari raya",
    "lmbr":      "lembur",
    "overtime":  "lembur",
    "ot":        "lembur",
    "ct":        "cuti",
    "check in":  "masuk kerja",
    "checkin":   "masuk kerja",
    "check out": "keluar kerja",
    "checkout":  "keluar kerja",
    # Tools / digital work
    "email":     "surel",
    "mailing":   "mengirim surel",
    "cc":        "tembusan",
    "bcc":       "tembusan tersembunyi",
    "forward":   "teruskan",
    "teams":     "microsoft teams",
    "ms teams":  "microsoft teams",
    "excel":     "microsoft excel",
    "word":      "microsoft word",
    "ppt":       "powerpoint",
    "powerpoint":"presentasi powerpoint",
    "drive":     "google drive",
    "cloud":     "komputasi awan",
    "database":  "basis data",
    "app":       "aplikasi",
    "apk":       "aplikasi",
    "software":  "perangkat lunak",
    "hardware":  "perangkat keras",
}

# Numbers, measurements & quantity expressions
_NUMBERS_QUANTITY: Dict[str, str] = {
    # Informal prefix shortcuts  (sejuta / semiliar are genuine contractions)
    "sejuta":    "satu juta",
    "semiliar":  "satu miliar",
    # Informal number abbreviations  (rb = ribu, jt = juta)
    "1rb":       "seribu",
    "2rb":       "dua ribu",
    "5rb":       "lima ribu",
    "10rb":      "sepuluh ribu",
    "20rb":      "dua puluh ribu",
    "50rb":      "lima puluh ribu",
    "100rb":     "seratus ribu",
    "200rb":     "dua ratus ribu",
    "500rb":     "lima ratus ribu",
    "1jt":       "satu juta",
    "2jt":       "dua juta",
    "5jt":       "lima juta",
    "10jt":      "sepuluh juta",
    # Quantity abbreviations  (slang → standard)
    "slrh":      "seluruh",
    "sktr":      "sekitar",
    "hmpr":      "hampir",
    "hmpir":     "hampir",
    "plng2":     "paling-paling",
    # Reduplications  (written as X2 or concatenated)
    "rata2":     "rata-rata",
    "ratarata":  "rata-rata",
    "kira2":     "kira-kira",
    "kirakira":  "kira-kira",
    "sktr":      "sekitar",
    "hmpr":      "hampir",
    "plng2":     "paling-paling",
    # Time quantities
    "sebentar":  "sebentar",
    "sbntr":     "sebentar",
    "sbntr lg":  "sebentar lagi",
    "slmanya":   "selamanya",
    "smntara":   "sementara",
    "mndak":     "mendadak",
    "dadakan":   "mendadak",
    "ssgera":    "segera",
    "sgera":     "segera",
    "sgra":      "segera",
    "cpat":      "cepat",
}

# Common compound slang expressions & phrases
# Only include entries where the COMBINED phrase produces a different result
# than individual word lookups would give (e.g. slang fusion, negation compounds
# with particles, or abbreviations that span multiple tokens).
_COMPOUND_EXPRESSIONS: Dict[str, str] = {
    # Slang word + particle/qualifier — net transformation differs from individual lookups
    "eh iya":      "oh iya",      # discourse opener
    "gitu kan":    "begitu kan",
    "gitu dong":   "begitu dong",
    "beneran ga":  "sungguh tidak",
    "beneran nih": "sungguh ini",
    "srius":       "serius",      # typo of standard word
    "serius nih":  "serius ini",
    # Question compounds with negation particle
    "bisa ga":     "bisa tidak",
    "bisa gak":    "bisa tidak",
    "boleh ga":    "boleh tidak",
    "boleh gak":   "boleh tidak",
    "mau ga":      "mau tidak",
    "mau gak":     "mau tidak",
    "tau ga":      "tahu tidak",
    "tau gak":     "tahu tidak",
    # Multi-token slang phrases
    "gimana caranya": "bagaimana caranya",
    "gmn caranya": "bagaimana caranya",
    "gue juga":    "saya juga",
    "gw juga":     "saya juga",
    "kayaknya sih":"sepertinya",
    "kayaknya iya":"sepertinya iya",
    "buat apa":    "untuk apa",
    "bwt apa":     "untuk apa",
    "ngapain":     "sedang apa",
    "ngapain aja": "sedang apa saja",
    "lagi ngapain":"sedang apa",
    "lagi dimana": "sedang di mana",
    "lg dmn":      "sedang di mana",
    "otw ke":      "dalam perjalanan ke",
    "nyampe blm":  "sudah sampai belum",
    "sampai blm":  "sudah sampai belum",
    # Compound slang where slang token fuses with standard word
    "udah mkan":   "sudah makan",   # mkan not split correctly if fused
    "blm makan":   "belum makan",
    "udh lma":     "sudah lama",
    "br aja":      "baru saja",
    "bsk aja":     "besok saja",
    "skrg juga":   "sekarang juga",
    "dr tadi":     "dari tadi",
    "dr dulu":     "dari dulu",
    "tlg bantu":   "tolong bantu",
    # Agreement / disagreement — particle changes meaning of phrase
    "emang bener": "memang benar",
    "bener juga":  "benar juga",
    "iya bener":   "iya benar",
    "nggak dong":  "tidak dong",
    "nggak sih":   "tidak sih",
    "ya ga":       "ya tidak",
    "ga juga":     "tidak juga",
    "gak juga":    "tidak juga",
    "bukan gitu":  "bukan begitu",
    "bukan disini":"bukan di sini",
    "maksudnya gimana": "maksudnya bagaimana",
    "mksdnya gmn": "maksudnya bagaimana",
    # Temporal compound abbreviations
    "kapan2":      "kapan-kapan",
    "kapan2 ya":   "kapan-kapan ya",
    "ntar aja":    "nanti saja",
    "tar aja":     "nanti saja",
    "makasih banyak": "terima kasih banyak",
}

# ─────────────────────────────────────────────────────────────────────────────
# PARTICLES
# Indonesian sentence-final / clause-final pragmatic particles.
# The 6 canonical forms (lah, deh, nih, dong, kok, sih) are pass-through mapped
# to prevent them from being stripped. Other particles rely on auto-reduction.
#
# Design: _reduce_repeated_chars automatically collapses:
#   - vowels: 2+ consecutive → 1  (laah → lah, yaa → ya)
#   - consonants: 3+ consecutive → 1 (lahhhh → lah, yukkk → yuk)
# Note: 2-consonant repeats (lahh, dehh) are explicitly mapped here as they
# are not auto-reduced.
# ─────────────────────────────────────────────────────────────────────────────
_PARTICLES: Dict[str, str] = {
    # ── lah ──
    "lah":     "lah",
    "lh":      "lah",
    "lahh":    "lah",
    "la":      "lah",

    # ── deh ──
    "deh":     "deh",
    "dh":      "deh",
    "dehh":    "deh",
    "de":      "deh",

    # ── nih ──
    "nih":     "nih",
    "ni":      "nih",
    "nihh":    "nih",
    "neh":     "nih",    # Betawi variant
    "nehh":    "nih",

    # ── dong ──
    "dong":    "dong",
    "dng":     "dong",
    "dongg":   "dong",
    "don":     "dong",

    # ── kok ──
    "kok":     "kok",
    "kokk":    "kok",

    # ── sih ──
    "sih":     "sih",
    "si":      "sih",
    "sihh":    "sih",
    "sich":    "sih",

    # ── Other Particle Variants ──
    "loh":     "lho",
    "lo":      "lho",
    "punn":    "pun",
    "tohh":    "toh",
    "kahh":    "kah",
    "tahh":    "tah",
    "woy":     "woi",
    "woyy":    "woi",
    "hey":     "hei",
    "yukk":    "yuk",
    "yuk ah":  "yuk",
    "ahh":     "ah",
    "ihh":     "ih",
    "idihh":   "idih",
}

# ─────────────────────────────────────────────────────────────────────────────
# MERGE ALL CATEGORIES INTO ONE MAPPING
# Order matters: later dicts override earlier ones on key conflicts.
# Compound negation must appear so that it sorts BEFORE single-char negation
# (handled automatically by longest-first sort in _compile_pattern).
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_SLANG: Dict[str, str] = {}
for _cat in (
    _PRONOUNS,
    _KINSHIP,
    _NEGATION,
    _COMPOUND_NEGATION,
    _CONJUNCTIONS,
    _VERBS,
    _ADJECTIVES_ADVERBS,
    _QUESTION_WORDS,
    _GREETINGS_RESPONSES,
    _TEMPORAL_LOCATION,
    _INTERNET_SLANG,
    _ECOMMERCE_FINANCE,
    _YOUTH_SLANG,
    _DISCOURSE_MARKERS,
    _JAVANESE_EXTENDED,
    _SUNDANESE_EXTENDED,
    _NOUNS,
    _HEALTH,
    _EMOTIONS_EXPRESSIONS,
    _FOOD_DRINK,
    _CLOTHING_FASHION,
    _TRANSPORTATION,
    _RELIGION_CULTURE,
    _EDUCATION_EXTENDED,
    _WORK_OFFICE,
    _NUMBERS_QUANTITY,
    _COMPOUND_EXPRESSIONS,
    _PARTICLES,
):
    _DEFAULT_SLANG.update(_cat)


# ─────────────────────────────────────────────────────────────────────────────
# REPEATED CHARACTER NORMALIZATION PATTERNS
# ─────────────────────────────────────────────────────────────────────────────

# Vowels: reduce 2+ consecutive identical vowels → 1
# e.g. "manaa" → "mana", "bangeeeet" → "banget"
# Rationale: vowel elongation is always expressive, never meaningful.
_VOWEL_REPEAT = re.compile(r'([aeiouAEIOU])\1+')

# Consonants: reduce 3+ consecutive identical consonants → 1
# e.g. "bgttt" → "bgt", "wkwwwk" → "wkwk"
# Rationale: keep "kk" (kakak), "ll" (dalam "dll"), "mm" etc. intact;
#            only collapse truly elongated forms (3+).
_CONSONANT_REPEAT = re.compile(r'([^aeiouAEIOU\s\d])\1{2,}')

# Whitespace normalization
_WHITESPACE = re.compile(r'\s+')


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CLASS
# ─────────────────────────────────────────────────────────────────────────────

class SlangNormalizer:
    """
    Normalizes informal/colloquial Indonesian text to standard Indonesian.

    Args:
        custom_mapping: Optional additional slang entries that override or
                        extend the built-in dictionary.

    Example:
        >>> normalizer = SlangNormalizer()
        >>> normalizer.normalize("gw gamau pergi krn lg baper bgt")
        'saya tidak mau pergi karena sedang bawa perasaan banget'

        >>> normalizer.add("npwp", "nomor pokok wajib pajak")
        >>> normalizer.normalize("masukin npwp dulu")
        'masukkan nomor pokok wajib pajak dulu'

        >>> normalizer.normalize_batch(["gw mau makan", "km udah makan?"])
        ['saya mau makan', 'kamu sudah makan?']
    """

    def __init__(self, custom_mapping: Optional[Dict[str, str]] = None):
        self.mapping: Dict[str, str] = {
            k.lower(): v for k, v in _DEFAULT_SLANG.items()
        }
        if custom_mapping:
            self.mapping.update({k.lower(): v for k, v in custom_mapping.items()})
        self._regex: Optional[re.Pattern] = None
        self._compile_pattern()

    # ─── Internal ────────────────────────────────────────────────────────────

    def _compile_pattern(self) -> None:
        """
        Build a compiled regex from the current mapping.

        Keys are sorted longest-first so compound slang like "gamau"
        matches before its shorter substring "ga".
        """
        if not self.mapping:
            self._regex = None
            return
        sorted_keys = sorted(self.mapping.keys(), key=len, reverse=True)
        escaped = [re.escape(k) for k in sorted_keys]
        pattern = r'\b(' + '|'.join(escaped) + r')\b'
        self._regex = re.compile(pattern, re.IGNORECASE)

    @staticmethod
    def _reduce_repeated_chars(text: str) -> str:
        """
        Collapse elongated characters to their canonical form.

        Rules:
            - Vowels (a, e, i, o, u): 2+ consecutive → 1
              "manaaaa" → "mana",  "bangeeeet" → "banget"
            - Consonants: 3+ consecutive → 1
              "bgttttt" → "bgt",   "wkwwwwk" → "wkwk"
              "kk" → "kk"  (preserved — abbreviation for "kakak")
              "dll" → "dll" (preserved — "dan lain-lain")

        Vowels are processed first so that a string like "aaakk" is handled
        correctly in two distinct passes without cross-contamination.
        """
        text = _VOWEL_REPEAT.sub(r'\1', text)
        text = _CONSONANT_REPEAT.sub(r'\1', text)
        return text

    # ─── Public API ──────────────────────────────────────────────────────────

    def normalize(self, text: str, normalize_whitespace: bool = True) -> str:
        """
        Normalize a single text string.

        Pipeline:
            1. Reduce elongated characters (vowels then consonants)
            2. Replace slang tokens via compiled regex
            3. (Optionally) collapse multiple whitespace into one

        Args:
            text: Input text string.
            normalize_whitespace: If True, collapse multi-space into single
                                  space and strip leading/trailing whitespace.

        Returns:
            Normalized text string.

        Example:
            >>> slang.normalize("gw gamau pergi krn lg baper bgt")
            'saya tidak mau pergi karena sedang bawa perasaan banget'

            >>> slang.normalize("makasihhhh bgttttt")
            'terima kasih banget'

            >>> slang.normalize("gwwww gkkkk ngertiii")
            'saya tidak mengerti'
        """
        if not text or not text.strip():
            return text

        # Step 1: Reduce elongated characters
        text = self._reduce_repeated_chars(text)

        # Step 2: Apply slang replacements
        if self._regex:
            def _replace(match: re.Match) -> str:
                word = match.group(1).lower()
                return self.mapping.get(word, match.group(1))

            text = self._regex.sub(_replace, text)

        # Step 3: Normalize whitespace
        if normalize_whitespace:
            text = _WHITESPACE.sub(' ', text).strip()

        return text

    def normalize_batch(
        self,
        texts: List[str],
        normalize_whitespace: bool = True,
    ) -> List[str]:
        """
        Normalize a list of text strings efficiently.

        Args:
            texts: List of input strings.
            normalize_whitespace: Passed through to normalize().

        Returns:
            List of normalized strings (same order as input).

        Example:
            >>> slang.normalize_batch(["gw udah makan", "km blm tidur?"])
            ['saya sudah makan', 'kamu belum tidur?']
        """
        return [self.normalize(t, normalize_whitespace) for t in texts]

    def add(self, word: str, replacement: str) -> None:
        """
        Add a single entry to the slang dictionary.

        Triggers regex recompilation. For adding many entries at once,
        prefer bulk_add() to avoid repeated recompilation.

        Args:
            word: Slang word (stored as lowercase).
            replacement: Standard replacement string.

        Example:
            >>> normalizer.add("npwp", "nomor pokok wajib pajak")
        """
        self.mapping[word.lower()] = replacement
        self._compile_pattern()

    def bulk_add(self, mapping: Dict[str, str]) -> None:
        """
        Add multiple entries at once with a single regex recompilation.

        More efficient than calling add() repeatedly when inserting
        many domain-specific terms.

        Args:
            mapping: Dict of {slang: replacement} pairs.

        Example:
            >>> normalizer.bulk_add({
            ...     "kk": "kakak",
            ...     "adek": "adik",
            ...     "bokap": "ayah",
            ...     "nyokap": "ibu",
            ... })
        """
        self.mapping.update({k.lower(): v for k, v in mapping.items()})
        self._compile_pattern()

    def remove(self, word: str) -> bool:
        """
        Remove a word from the dictionary.

        Args:
            word: Slang word to remove.

        Returns:
            True if the word was found and removed, False otherwise.
        """
        word_lower = word.lower()
        if word_lower in self.mapping:
            del self.mapping[word_lower]
            self._compile_pattern()
            return True
        return False

    def reset(self) -> None:
        """
        Reset dictionary to built-in defaults, discarding all custom changes.

        Example:
            >>> normalizer.add("x", "ekstra")
            >>> "x" in normalizer
            True
            >>> normalizer.reset()
            >>> "x" in normalizer
            False
        """
        self.mapping = {k.lower(): v for k, v in _DEFAULT_SLANG.items()}
        self._compile_pattern()

    def export(self) -> Dict[str, str]:
        """
        Export the current mapping as a plain dictionary.

        Returns:
            A copy of the current {slang: replacement} mapping.
        """
        return self.mapping.copy()

    def lookup(self, word: str) -> Optional[str]:
        """
        Look up a single slang word without normalizing a full sentence.

        Args:
            word: Word to look up (case-insensitive).

        Returns:
            The replacement string, or None if not found.

        Example:
            >>> slang.lookup("bgt")
            'banget'
            >>> slang.lookup("makan")
            None
        """
        return self.mapping.get(word.lower())

    # ─── Dunder helpers ──────────────────────────────────────────────────────

    def __len__(self) -> int:
        """Return number of entries in the slang dictionary."""
        return len(self.mapping)

    def __contains__(self, word: str) -> bool:
        """Check if a word is in the slang dictionary (case-insensitive)."""
        return word.lower() in self.mapping

    def __repr__(self) -> str:
        return f"SlangNormalizer(entries={len(self.mapping)})"


# Backward-compatible alias
SlangDictionary = SlangNormalizer

# ─────────────────────────────────────────────────────────────────────────────
# MODULE-LEVEL CONVENIENCE SINGLETON
#
# Import and use directly without instantiation:
#   from basa.core.slang import slang
#   slang.normalize("gw gamau pergi")
# ─────────────────────────────────────────────────────────────────────────────
slang = SlangNormalizer()