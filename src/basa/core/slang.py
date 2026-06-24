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
    "aku":   "aku",
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
    "beliau":"beliau",
    # Plural
    "mrk":   "mereka",
    "mereka":"mereka",
    "qt":    "kita",
    "kita":  "kita",
    "kln":   "kalian",
    "kalian":"kalian",
    # Reflexive
    "sendiri":"sendiri",
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
    "ibu":    "ibu",           # already standard, included for completeness
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
    "suami":  "suami",         # already standard
    "istri":  "istri",         # already standard
    "anak":   "anak",          # already standard
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
    "bukan":   "bukan",
    "bkn":     "bukan",
    "bknnya":  "bukannya",
    "jangan":  "jangan",
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
    "pergi":     "pergi",
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
    "traktir":   "traktir",
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
    "tolong":       "tolong",
    # Apology
    "mf":           "maaf",
    "afwan":        "maaf",         # Arabic-Indonesian
    "maap":         "maaf",
    "sori":         "maaf",
    "sory":         "maaf",
    "sorry":        "maaf",
    "sorri":        "maaf",
    "minta maaf":   "minta maaf",
    "mnt maaf":     "minta maaf",
    # Agreement
    "ok":           "oke",
    "okk":          "oke",
    "okee":         "oke",
    "okelah":       "oke",
    "oke":          "oke",
    "sip":          "baik",
    "siapp":        "siap",
    "siap":         "siap",
    "iy":           "iya",
    "iya":          "iya",
    "iyap":         "iya",
    "yap":          "ya",
    "yep":          "ya",
    "yup":          "ya",
    "yupp":         "ya",
    "yeah":         "ya",
    "yoi":          "iya",          # Jakartan slang
    "mantul":       "mantap betul",
    # Greetings
    "halo":         "halo",
    "hai":          "hai",
    "hi":           "hai",
    "hey":          "hei",
    "hei":          "hei",
    "selamat pagi": "selamat pagi",
    "selamat siang":"selamat siang",
    "selamat sore": "selamat sore",
    "selamat malam":"selamat malam",
    "met pagi":     "selamat pagi",
    "met siang":    "selamat siang",
    "met sore":     "selamat sore",
    "met malam":    "selamat malam",
    "selamat datang":"selamat datang",
    "slmt dtng":    "selamat datang",
    "selamat tinggal": "selamat tinggal",
    "sampai jumpa": "sampai jumpa",
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
    "permisi":      "permisi",
    "prmisi":       "permisi",
    "silakan":      "silakan",
    "silahkan":     "silakan",
    "monggo":       "silakan",
    "dengan senang hati": "dengan senang hati",
    "sama-sama":    "sama-sama",
    "samasama":     "sama-sama",
    "samsama":      "sama-sama",
    "sama sama":    "sama-sama",
    "kembali":      "kembali",
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
    "viral":    "viral",
    "relate":   "relatable",
    "selfie":   "foto sendiri",
    "caption":  "keterangan foto",
    "story":    "cerita",
    "feeds":    "beranda",
    "sih":      "sih",             # discourse particle — keep as-is
}

# Discourse markers and meta-commentary
_DISCOURSE_MARKERS: Dict[str, str] = {
    "mksd":       "maksud",
    "mksdnya":    "maksudnya",
    "intinya":    "intinya",
    "pokoknya":   "pokoknya",
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
    "gebetan":"gebetan",
    "mantan": "mantan",
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
    "demam":   "demam",
    "btk":     "batuk",
    "batuk":   "batuk",
    "plk":     "pilek",
    "pilek":   "pilek",
    "ml":      "mual",
    "mual":    "mual",
    "mntah":   "muntah",
    "muntah":  "muntah",
    "alrgi":   "alergi",
    "alergi":  "alergi",
    "sesak":   "sesak napas",
    "sakit kepala": "sakit kepala",
    "sktkpl":  "sakit kepala",
    "pusing":  "pusing",
    "vertigo": "vertigo",
    "diare":   "diare",
    "mencret": "diare",
    "mules":   "mulas",
    "mulas":   "mulas",
    "gatal":   "gatal",
    "bentol":  "bentol",
    "luka":    "luka",
    "lebam":   "memar",
    "memar":   "memar",
    "patah":   "patah",
    "keseleo": "keseleo",
    "kslng":   "keseleo",
    # Medical personnel & places
    "obt":     "obat",
    "obat":    "obat",
    "dkter":   "dokter",
    "dokter":  "dokter",
    "dr":      "dokter",
    "prwt":    "perawat",
    "perawat": "perawat",
    "rwt":     "rawat",
    "rawat":   "rawat",
    "opname":  "rawat inap",
    "rawat inap": "rawat inap",
    "ugd":     "unit gawat darurat",
    "igd":     "instalasi gawat darurat",
    "poli":    "poliklinik",
    "apotek":  "apotek",
    "apotk":   "apotek",
    "resep":   "resep dokter",
    "rsep":    "resep dokter",
    "suntik":  "suntik",
    "vaksin":  "vaksin",
    "imunisasi":"imunisasi",
    "cek darah":"cek darah",
    "tes pcr": "tes pcr",
    "rapid test":"tes cepat",
    # Wellness & fitness
    "jalan2":  "jalan-jalan",
    "olrga":   "olahraga",
    "olahraga":"olahraga",
    "gym":     "olahraga",
    "lari":    "berlari",
    "jogging": "joging",
    "joging":  "joging",
    "renang":  "berenang",
    "senam":   "senam",
    "yoga":    "yoga",
    "meditasi":"meditasi",
    "tdr":     "tidur",
    "tidur":   "tidur",
    "tidur siang": "tidur siang",
    "tdrsiang":"tidur siang",
    "begadang":"begadang",
    "bgdng":   "begadang",
    "istrhat": "istirahat",
    "istrht":  "istirahat",
    "istirahat":"istirahat",
    "sehat":   "sehat",
    "shat":    "sehat",
    "sembuh":  "sembuh",
    "smbh":    "sembuh",
    "lekas sembuh": "lekas sembuh",
    "cpt smbh":"lekas sembuh",
    "get well soon": "lekas sembuh",
    "gws":     "lekas sembuh",
    "karantina":"karantina",
    "isolasi": "isolasi",
    "isoman":  "isolasi mandiri",
}

# ─────────────────────────────────────────────────────────────────────────────
# EXTENDED CATEGORIES (added to reach comprehensive coverage)
# ─────────────────────────────────────────────────────────────────────────────

# Emotions, feelings & expressions
_EMOTIONS_EXPRESSIONS: Dict[str, str] = {
    # Happiness / excitement
    "senang":    "senang",
    "gembira":   "gembira",
    "bahagia":   "bahagia",
    "happy":     "bahagia",
    "excited":   "bersemangat",
    "semngt":    "semangat",
    "smngat":    "semangat",
    "smgt":      "semangat",
    "bersemgt":  "bersemangat",
    "girang":    "girang",
    "riang":     "riang",
    "hore":      "hore",
    "yey":       "hore",
    "yeay":      "hore",
    "yay":       "hore",
    "asoy":      "asyik",
    "asyik":     "asyik",
    "seru":      "seru",
    "keren":     "keren",
    "krn2":      "keren-keren",
    "mantap":    "mantap",
    "mantab":    "mantap",
    "gokil":     "luar biasa",
    "gila":      "luar biasa",
    "gile":      "luar biasa",
    "gilak":     "luar biasa",
    "parah":     "luar biasa",
    "lebay":     "berlebihan",
    "lbay":      "berlebihan",
    # Sadness / disappointment
    "sedih":     "sedih",
    "sdh2":      "sedih",
    "galau":     "galau",
    "gundah":    "gundah",
    "kecewa":    "kecewa",
    "kcewa":     "kecewa",
    "kzl":       "kesal",
    "kesal":     "kesal",
    "bete":      "kesal",
    "bt":        "kesal",
    "gondok":    "kesal",
    "sewot":     "kesal",
    "jutek":     "judes",
    "cemberut":  "cemberut",
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
    "kaget":     "kaget",
    "syok":      "syok",
    "shock":     "syok",
    "tercengang":"tercengang",
    "bengong":   "bengong",
    "bnggong":   "bengong",
    "melongo":   "terpana",
    "heran":     "heran",
    "bingung":   "bingung",
    "bnggung":   "bingung",
    "pusing":    "pusing",
    "mumet":     "pusing",
    "mupeng":    "sangat menginginkan",
    # Love / affection
    "sayang":    "sayang",
    "syangku":   "sayangku",
    "cinta":     "cinta",
    "cintrong":  "cinta",
    "suka":      "suka",
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
    "putus":     "putus",
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
    "santai":    "santai",
    "santey":    "santai",
    "ndak":      "tidak",
    "enggak":    "tidak",
}

# Food & drink vocabulary
_FOOD_DRINK: Dict[str, str] = {
    # General food terms
    "mkan":      "makan",
    "mkanan":    "makanan",
    "makanan":   "makanan",
    "lauk":      "lauk-pauk",
    "nasi":      "nasi",
    "ns":        "nasi",
    "sayur":     "sayuran",
    "syr":       "sayuran",
    "daging":    "daging",
    "ayam":      "ayam",
    "ikan":      "ikan",
    "tahu":      "tahu",
    "tempe":     "tempe",
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
    "gorengan":  "gorengan",
    "grngn":     "gorengan",
    "batagor":   "bakso tahu goreng",
    "siomay":    "siomay",
    "seblak":    "seblak",
    "cireng":    "aci goreng",
    "cilok":     "aci dicolok",
    "baso":      "bakso",
    "bakso":     "bakso",
    "bks":       "bakso",
    "sate":      "sate",
    "gado2":     "gado-gado",
    "gudeg":     "gudeg",
    "rendang":   "rendang",
    "soto":      "soto",
    "rawon":     "rawon",
    "opor":      "opor",
    "pecel":     "pecel",
    "lontong":   "lontong",
    "ketupat":   "ketupat",
    "bubur":     "bubur",
    "blr":       "bubur",
    "nasi uduk": "nasi uduk",
    "nsuduk":    "nasi uduk",
    "warteg":    "warung tegal",
    "wrtg":      "warung tegal",
    # Drinks
    "minum":     "minum",
    "mnum":      "minum",
    "minuman":   "minuman",
    "mnuman":    "minuman",
    "air":       "air",
    "es":        "es",
    "susu":      "susu",
    "kopi":      "kopi",
    "kpi":       "kopi",
    "teh":       "teh",
    "teh manis": "teh manis",
    "tehmanis":  "teh manis",
    "teman":     "teman",      # override prevention — 'teh' already mapped
    "jus":       "jus",
    "juice":     "jus",
    "boba":      "boba",
    "bubble tea":"boba teh",
    "kopi susu": "kopi susu",
    "kopsu":     "kopi susu",
    "americano": "kopi americano",
    "matcha":    "matcha",
    "cola":      "cola",
    "soda":      "soda",
    "minol":     "minuman beralkohol",
    # Taste / quality
    "enak":      "enak",
    "enakk":     "enak",
    "nyaman":    "nyaman",
    "lezat":     "lezat",
    "mantul":    "mantap betul",
    "kriuk":     "renyah",
    "gurih":     "gurih",
    "pedas":     "pedas",
    "pedes":     "pedas",
    "manis":     "manis",
    "asin":      "asin",
    "asem":      "asam",
    "pahit":     "pahit",
    "hambar":    "hambar",
    "basi":      "basi",
    "bukan enak":"tidak enak",
    "gaenak":    "tidak enak",
    "ga enak":   "tidak enak",
    "abis":      "habis",
    "keabisan":  "kehabisan",
    "khabisan":  "kehabisan",
    # Meal times / hunger
    "makan siang":"makan siang",
    "makanmalam": "makan malam",
    "makan pagi": "makan pagi",
    "sarapan":   "sarapan",
    "srpn":      "sarapan",
    "siang":     "siang",
    "malem":     "malam",
    "laper":     "lapar",
    "laperan":   "sedang lapar",
    "kelaperan": "sangat lapar",
    "ngidam":    "mengidam",
    "nagih":     "ketagihan",
    "ketagihan": "ketagihan",
    "kenyang":   "kenyang",
    "kenyangn":  "kekenyangan",
    "kekenyangan":"kekenyangan",
}

# Clothing & fashion vocabulary
_CLOTHING_FASHION: Dict[str, str] = {
    # Garments
    "baju":      "baju",
    "bj":        "baju",
    "kaos":      "kaus",
    "kos":       "kaus",
    "kemeja":    "kemeja",
    "kmja":      "kemeja",
    "jaket":     "jaket",
    "jkt":       "jaket",
    "celana":    "celana",
    "cln":       "celana",
    "rok":       "rok",
    "dress":     "gaun",
    "gaun":      "gaun",
    "jilbab":    "jilbab",
    "jlbb":      "jilbab",
    "hijab":     "hijab",
    "hijaber":   "pengguna hijab",
    "kerudung":  "kerudung",
    "krdng":     "kerudung",
    "mukena":    "mukena",
    "gamis":     "gamis",
    "sarung":    "sarung",
    "koko":      "baju koko",
    "batik":     "batik",
    "daster":    "daster",
    "piyama":    "piyama",
    "pjm":       "piyama",
    "sweater":   "sweater",
    "sweter":    "sweater",
    "hoodie":    "hoodie",
    "hudi":      "hoodie",
    "cardigan":  "kardigan",
    "outer":     "jaket luar",
    "outher":    "jaket luar",
    "vest":      "rompi",
    "rompi":     "rompi",
    # Footwear
    "sepatu":    "sepatu",
    "spt2":      "sepatu-sepatu",
    "sandal":    "sandal",
    "sdl":       "sandal",
    "sneakers":  "sepatu kets",
    "snakers":   "sepatu kets",
    "boots":     "sepatu bot",
    "heels":     "sepatu hak tinggi",
    "higheels":  "sepatu hak tinggi",
    "flatshoes": "sepatu flat",
    "slippers":  "sandal",
    # Accessories
    "tas":       "tas",
    "tote bag":  "tas tote",
    "totebag":   "tas tote",
    "dompet":    "dompet",
    "dmpt":      "dompet",
    "gelang":    "gelang",
    "kalung":    "kalung",
    "anting":    "anting",
    "cincin":    "cincin",
    "jam tangan":"jam tangan",
    "jamtgn":    "jam tangan",
    "kacamata":  "kacamata",
    "kacmt":     "kacamata",
    "topi":      "topi",
    "sabuk":     "sabuk",
    "ikat pinggang": "ikat pinggang",
    # Fashion terms
    "outfit":    "pakaian",
    "ootd":      "pakaian hari ini",
    "mix match": "padupadan",
    "mixmatch":  "padupadan",
    "casual":    "kasual",
    "formal":    "formal",
    "modis":     "modis",
    "stylish":   "bergaya",
    "trendy":    "trendi",
    "vintage":   "jadul bergaya",
    "thrift":    "beli baju bekas",
    "thrifting": "belanja baju bekas",
    "preloved":  "bekas pakai",
    "ukuran":    "ukuran",
    "ukrn":      "ukuran",
    "size":      "ukuran",
    "muat":      "muat",
    "kebesaran": "terlalu besar",
    "kekecilan": "terlalu kecil",
    "sempit":    "sempit",
    "longgar":   "longgar",
    "ketat":     "ketat",
}

# Transportation vocabulary
_TRANSPORTATION: Dict[str, str] = {
    # Vehicles
    "motor":     "motor",
    "mtr":       "motor",
    "mobil":     "mobil",
    "mbl":       "mobil",
    "sepeda":    "sepeda",
    "spd":       "sepeda",
    "angkot":    "angkutan kota",
    "angkutan":  "angkutan",
    "bus":       "bus",
    "busway":    "bus transjakarta",
    "transjakarta": "transjakarta",
    "tj":        "transjakarta",
    "kereta":    "kereta",
    "krl":       "kereta rel listrik",
    "mrt":       "mass rapid transit",
    "lrt":       "light rail transit",
    "commuter":  "kereta komuter",
    "komuter":   "kereta komuter",
    "pesawat":   "pesawat",
    "pswt":      "pesawat",
    "bandara":   "bandara",
    "bdr":       "bandara",
    "kapal":     "kapal",
    "kpl":       "kapal",
    "ojek":      "ojek",
    "ojol":      "ojek online",
    "gojek":     "gojek",
    "grab":      "grab",
    "taxi":      "taksi",
    "taksi":     "taksi",
    "becak":     "becak",
    "delman":    "delman",
    "bentor":    "becak motor",
    "bajaj":     "bajaj",
    "bensin":    "bensin",
    "bnsn":      "bensin",
    "solar":     "solar",
    "bbm":       "bahan bakar minyak",
    "pertamax":  "pertamax",
    "pertalite":  "pertalite",
    # Navigation / travel
    "jalan":     "jalan",
    "jln":       "jalan",
    "macet":     "macet",
    "kemacetan": "kemacetan",
    "mct":       "macet",
    "mudik":     "mudik",
    "pulang kampung": "pulang kampung",
    "plkmpng":   "pulang kampung",
    "perjalanan":"perjalanan",
    "prjlnan":   "perjalanan",
    "rute":      "rute",
    "jarak":     "jarak",
    "jrk":       "jarak",
    "deket":     "dekat",
    "jauh":      "jauh",
    "parkir":    "parkir",
    "prk":       "parkir",
    "numpang":   "menumpang",
    "nunut":     "menumpang",
    "nebeng":    "menumpang",
    "diantar":   "diantarkan",
    "dijemput":  "dijemput",
    "jemput":    "jemput",
    "antar":     "antar",
    "antarkan":  "antarkan",
    "nyetir":    "mengemudi",
    "nyupir":    "mengemudikan",
    "setir":     "kemudi",
    "rem":       "rem",
    "klakson":   "klakson",
    "spion":     "kaca spion",
    "gps":       "navigasi",
    "maps":      "peta navigasi",
    "gmaps":     "google maps",
    "waze":      "waze",
}

# Religion, culture & social life
_RELIGION_CULTURE: Dict[str, str] = {
    # Islamic expressions (very common in Indonesian daily speech)
    "insya allah": "insya allah",
    "insyaallah": "insya allah",
    "inshallah":  "insya allah",
    "ia":         "insya allah",
    "alhamdulillah": "alhamdulillah",
    "alhdlh":     "alhamdulillah",
    "alhdlll":    "alhamdulillah",
    "amdlh":      "alhamdulillah",
    "alhamdu":    "alhamdulillah",
    "masya allah":"masya allah",
    "masyaallah": "masya allah",
    "subhanallah":"subhanallah",
    "subhankl":   "subhanallah",
    "astaghfirullah": "astaghfirullah",
    "astagfirullah": "astaghfirullah",
    "astaga":     "astaga",
    "astghfr":    "astaghfirullah",
    "bismillah":  "bismillah",
    "bsmllh":     "bismillah",
    "bismillahirrahmanirrahim": "bismillah",
    "allahu akbar": "allahu akbar",
    "allahuakbar": "allahu akbar",
    "aamiin":     "amin",
    "aminn":      "amin",
    "jazakallah": "semoga Allah membalas kebaikanmu",
    "jazakallahu khair": "semoga Allah membalas kebaikanmu",
    "barakallah": "semoga Allah memberkahimu",
    "semoga":     "semoga",
    "doa":        "doa",
    "sholat":     "salat",
    "solat":      "salat",
    "shalat":     "salat",
    "salat":      "salat",
    "puasa":      "puasa",
    "sahur":      "sahur",
    "buka puasa": "buka puasa",
    "bukpus":     "buka puasa",
    "bukber":     "buka bersama",
    "ramadan":    "ramadan",
    "ramadhan":   "ramadan",
    "lebaran":    "lebaran",
    "idul fitri": "idul fitri",
    "idulfitri":  "idul fitri",
    "idul adha":  "idul adha",
    "idulfitri":  "idul fitri",
    "eid":        "lebaran",
    "fitrah":     "zakat fitrah",
    "zakat":      "zakat",
    "infak":      "infak",
    "sedekah":    "sedekah",
    "masjid":     "masjid",
    "msdjd":      "masjid",
    "mushola":    "musala",
    "musholla":   "musala",
    "pesantren":  "pesantren",
    "psntrn":     "pesantren",
    "ustadz":     "ustaz",
    "ustad":      "ustaz",
    "kyai":       "kiai",
    "kiai":       "kiai",
    # National / cultural
    "merah putih":"merah putih",
    "pancasila":  "pancasila",
    "indonesia":  "indonesia",
    "nusantara":  "nusantara",
    "bhineka":    "bhinneka",
    "proklamasi": "proklamasi",
    "kemerdekaan":"kemerdekaan",
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
    "lamaran":    "lamaran",
    "tunangan":   "tunangan",
    "tunang":     "tunangan",
    "akad":       "akad nikah",
    "resepsi":    "resepsi",
    "undangan":   "undangan",
    "undngn":     "undangan",
    "kondangan":  "menghadiri pernikahan",
    "kondngan":   "kondangan",
    "tahlilan":   "tahlilan",
    "syukuran":   "syukuran",
    "selamatan":  "selamatan",
    "arisan":     "arisan",
    "pengajian":  "pengajian",
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
    "mahasiswa": "mahasiswa",
    "mhsw":      "mahasiswa",
    "mahasiswi": "mahasiswi",
    "dosen":     "dosen",
    "dsn":       "dosen",
    "guru":      "guru",
    "gr":        "guru",
    "kepala sekolah": "kepala sekolah",
    "kepsek":    "kepala sekolah",
    "kpsek":     "kepala sekolah",
    # Academic activities
    "belajar":   "belajar",
    "bljar":     "belajar",
    "bljr":      "belajar",
    "ngajar":    "mengajar",
    "ngjar":     "mengajar",
    "ujian":     "ujian",
    "ujin":      "ujian",
    "ulangan":   "ulangan",
    "ulngn":     "ulangan",
    "tugas":     "tugas",
    "tgs":       "tugas",
    "pr":        "pekerjaan rumah",
    "homework":  "pekerjaan rumah",
    "hw":        "pekerjaan rumah",
    "presentasi":"presentasi",
    "presntsi":  "presentasi",
    "prsnts":    "presentasi",
    "laporan":   "laporan",
    "lprn":      "laporan",
    "makalah":   "makalah",
    "mklh":      "makalah",
    "skripsi":   "skripsi",
    "skrpsi":    "skripsi",
    "skrip":     "skripsi",
    "thesis":    "tesis",
    "tesis":     "tesis",
    "disertasi": "disertasi",
    "sidang":    "sidang",
    "wisuda":    "wisuda",
    "wsd":       "wisuda",
    "yudisium":  "yudisium",
    "ospek":     "orientasi studi",
    "maba":      "mahasiswa baru",
    "mhs baru":  "mahasiswa baru",
    "senior":    "senior",
    "junior":    "junior",
    # Grades & results
    "nilai":     "nilai",
    "nlai":      "nilai",
    "rapor":     "rapor",
    "raport":    "rapor",
    "ipk":       "indeks prestasi kumulatif",
    "ip":        "indeks prestasi",
    "cum laude": "cum laude",
    "lulus":     "lulus",
    "lls":       "lulus",
    "gagal":     "gagal",
    "ggl":       "gagal",
    "tidak lulus":"tidak lulus",
    "remedial":  "remedial",
    "remidi":    "remedial",
    "ngulang":   "mengulang",
    "nunggak":   "tidak naik kelas",
    "naik kelas":"naik kelas",
    "naikin":    "menaikkan",
    "beasiswa":  "beasiswa",
    "beasiwa":   "beasiswa",
    "bsw":       "beasiswa",
    "beasiswaku":"beasiswaku",
    "daftar":    "daftar",
    "dft":       "daftar",
    "pendaftaran":"pendaftaran",
    "pndftran":  "pendaftaran",
    "seleksi":   "seleksi",
    "snbt":      "seleksi nasional berdasarkan tes",
    "utbk":      "ujian tulis berbasis komputer",
    "sbmptn":    "seleksi bersama masuk perguruan tinggi negeri",
    "ppdb":      "penerimaan peserta didik baru",
    "les":       "les",
    "les privat":"les privat",
    "bimbel":    "bimbingan belajar",
    "bmbl":      "bimbingan belajar",
    "tryout":    "uji coba",
    "to":        "uji coba",
}

# Work & office vocabulary
_WORK_OFFICE: Dict[str, str] = {
    # Job types & positions
    "kerja":     "kerja",
    "krja":      "kerja",
    "kerjaan":   "pekerjaan",
    "krjaan":    "pekerjaan",
    "pekerjaan": "pekerjaan",
    "kantor":    "kantor",
    "kntr":      "kantor",
    "perusahaan":"perusahaan",
    "prusahaan": "perusahaan",
    "prshn":     "perusahaan",
    "bos":       "atasan",
    "boss":      "atasan",
    "atasan":    "atasan",
    "rekan":     "rekan kerja",
    "rekan kerja":"rekan kerja",
    "kolega":    "kolega",
    "karyawan":  "karyawan",
    "krywn":     "karyawan",
    "pegawai":   "pegawai",
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
    "magang":    "magang",
    "mgang":     "magang",
    "kontrak":   "kontrak",
    "kntrak":    "kontrak",
    "tetap":     "tetap",
    "resign":    "mengundurkan diri",
    "resignasi": "pengunduran diri",
    "dipecat":   "dipecat",
    "phk":       "pemutusan hubungan kerja",
    # Work activities
    "rapat":     "rapat",
    "rpt":       "rapat",
    "meeting":   "rapat",
    "mtg":       "rapat",
    "zoom":      "rapat video",
    "gmeet":     "google meet",
    "presentasi":"presentasi",
    "deadline":  "batas waktu",
    "dl":        "batas waktu",
    "dl nya":    "batas waktunya",
    "submit":    "kirimkan",
    "sbmt":      "kirimkan",
    "revisi":    "revisi",
    "rvisi":     "revisi",
    "approval":  "persetujuan",
    "approved":  "disetujui",
    "acc":       "disetujui",
    "reject":    "ditolak",
    "ditolak":   "ditolak",
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
    "target":    "target",
    "kpi":       "indikator kinerja utama",
    "okr":       "tujuan dan hasil kunci",
    "brainstorm":"curah gagasan",
    "brnstrm":   "curah gagasan",
    # Finance / salary
    "gaji":      "gaji",
    "gji":       "gaji",
    "gajinya":   "gajinya",
    "slip gaji": "slip gaji",
    "thr":       "tunjangan hari raya",
    "bonus":     "bonus",
    "kenaikan gaji": "kenaikan gaji",
    "naik gaji": "naik gaji",
    "lembur":    "lembur",
    "lmbr":      "lembur",
    "overtime":  "lembur",
    "ot":        "lembur",
    "cuti":      "cuti",
    "ct":        "cuti",
    "izin":      "izin",
    "sakit":     "sakit",
    "absen":     "absen",
    "absensi":   "absensi",
    "check in":  "masuk kerja",
    "checkin":   "masuk kerja",
    "check out": "keluar kerja",
    "checkout":  "keluar kerja",
    # Tools / digital work
    "email":     "surel",
    "surel":     "surel",
    "mailing":   "mengirim surel",
    "cc":        "tembusan",
    "bcc":       "tembusan tersembunyi",
    "forward":   "teruskan",
    "reply":     "balas",
    "chat":      "pesan",
    "slack":     "slack",
    "teams":     "microsoft teams",
    "ms teams":  "microsoft teams",
    "excel":     "microsoft excel",
    "word":      "microsoft word",
    "ppt":       "powerpoint",
    "powerpoint":"presentasi powerpoint",
    "pdf":       "pdf",
    "file":      "berkas",
    "folder":    "folder",
    "drive":     "google drive",
    "cloud":     "komputasi awan",
    "database":  "basis data",
    "server":    "server",
    "sistem":    "sistem",
    "aplikasi":  "aplikasi",
    "app":       "aplikasi",
    "apk":       "aplikasi",
    "software":  "perangkat lunak",
    "hardware":  "perangkat keras",
}

# Numbers, measurements & quantity expressions
_NUMBERS_QUANTITY: Dict[str, str] = {
    # Cardinal shortcuts
    "satu":      "satu",
    "dua":       "dua",
    "tiga":      "tiga",
    "empat":     "empat",
    "lima":      "lima",
    "enam":      "enam",
    "tujuh":     "tujuh",
    "delapan":   "delapan",
    "sembilan":  "sembilan",
    "sepuluh":   "sepuluh",
    "sebelas":   "sebelas",
    "dua belas": "dua belas",
    "dua puluh": "dua puluh",
    "seratus":   "seratus",
    "seribu":    "seribu",
    "sejuta":    "satu juta",
    "semiliar":  "satu miliar",
    # Informal number abbreviations
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
    # Quantity / measurement
    "banyak":    "banyak",
    "sedikit":   "sedikit",
    "sebagian":  "sebagian",
    "semua":     "semua",
    "seluruh":   "seluruh",
    "slrh":      "seluruh",
    "sebagian besar": "sebagian besar",
    "rata2":     "rata-rata",
    "ratarata":  "rata-rata",
    "kira2":     "kira-kira",
    "kirakira":  "kira-kira",
    "sekitar":   "sekitar",
    "sktr":      "sekitar",
    "hampir":    "hampir",
    "hmpr":      "hampir",
    "lebih dari":"lebih dari",
    "kurang dari":"kurang dari",
    "paling":    "paling",
    "plng2":     "paling-paling",
    # Time quantities
    "sebentar":  "sebentar",
    "sbntr":     "sebentar",
    "sebentar lagi": "sebentar lagi",
    "sbntr lg":  "sebentar lagi",
    "sesaat":    "sesaat",
    "sejenak":   "sejenak",
    "lama":      "lama",
    "lamaaa":    "lama",
    "selamanya": "selamanya",
    "slmanya":   "selamanya",
    "sementara": "sementara",
    "smntara":   "sementara",
    "tiba2":     "tiba-tiba",
    "tibatiba":  "tiba-tiba",
    "mendadak":  "mendadak",
    "mndak":     "mendadak",
    "dadakan":   "mendadak",
    "segera":    "segera",
    "ssgera":    "segera",
    "cepat":     "cepat",
    "cpat":      "cepat",
    "lambat":    "lambat",
    "pelan":     "pelan",
    "plan2":     "pelan-pelan",
}

# Common compound slang expressions & phrases
_COMPOUND_EXPRESSIONS: Dict[str, str] = {
    # Common chat openers / fillers
    "eh iya":      "oh iya",
    "oh iya":      "oh iya",
    "oh ya":       "oh ya",
    "ya kan":      "ya kan",
    "gitu kan":    "begitu kan",
    "gitu dong":   "begitu dong",
    "masa iya":    "masa iya",
    "masa sih":    "masa sih",
    "beneran ga":  "sungguh tidak",
    "beneran nih": "sungguh ini",
    "serius":      "serius",
    "srius":       "serius",
    "serius nih":  "serius ini",
    "bisa ga":     "bisa tidak",
    "bisa gak":    "bisa tidak",
    "boleh ga":    "boleh tidak",
    "boleh gak":   "boleh tidak",
    "mau ga":      "mau tidak",
    "mau gak":     "mau tidak",
    "tau ga":      "tahu tidak",
    "tau gak":     "tahu tidak",
    "gimana caranya": "bagaimana caranya",
    "gmn caranya": "bagaimana caranya",
    "gue juga":    "saya juga",
    "gw juga":     "saya juga",
    "aku juga":    "aku juga",
    "kamu juga":   "kamu juga",
    "kita juga":   "kita juga",
    "kayaknya sih":"sepertinya",
    "kayaknya iya":"sepertinya iya",
    "buat apa":    "untuk apa",
    "bwt apa":     "untuk apa",
    "ngapain":     "sedang apa",
    "ngapain aja": "sedang apa saja",
    "lagi ngapain":"sedang apa",
    "udah makan":  "sudah makan",
    "udah mkan":   "sudah makan",
    "blm makan":   "belum makan",
    "lagi makan":  "sedang makan",
    "lagi dimana": "sedang di mana",
    "lg dmn":      "sedang di mana",
    "otw ke":      "dalam perjalanan ke",
    "nyampe blm":  "sudah sampai belum",
    "sampai blm":  "sudah sampai belum",
    # Agreement / disagreement fillers
    "emang bener": "memang benar",
    "bener juga":  "benar juga",
    "iya bener":   "iya benar",
    "iya sih":     "iya sih",
    "iya dong":    "iya dong",
    "nggak dong":  "tidak dong",
    "nggak sih":   "tidak sih",
    "ya ga":       "ya tidak",
    "ga juga":     "tidak juga",
    "gak juga":    "tidak juga",
    "bukan gitu":  "bukan begitu",
    "bukan itu":   "bukan itu",
    "bukan disini":"bukan di sini",
    "maksudnya gimana": "maksudnya bagaimana",
    "mksdnya gmn": "maksudnya bagaimana",
    # Temporal phrases
    "kapan2":      "kapan-kapan",
    "kapan2 ya":   "kapan-kapan ya",
    "ntar aja":    "nanti saja",
    "nanti aja":   "nanti saja",
    "besok aja":   "besok saja",
    "bsk aja":     "besok saja",
    "tar aja":     "nanti saja",
    "sekarang juga": "sekarang juga",
    "skrg juga":   "sekarang juga",
    "dari tadi":   "dari tadi",
    "dr tadi":     "dari tadi",
    "dari dulu":   "dari dulu",
    "dr dulu":     "dari dulu",
    "udah lama":   "sudah lama",
    "udh lma":     "sudah lama",
    "baru aja":    "baru saja",
    "br aja":      "baru saja",
    # Request / instruction
    "tolong bantu":"tolong bantu",
    "tlg bantu":   "tolong bantu",
    "mohon maaf":  "mohon maaf",
    "mohon maklum":"mohon maklum",
    "harap maklum":"harap maklum",
    "dengan hormat":"dengan hormat",
    "atas perhatiannya": "atas perhatiannya",
    "atas kerjasamanya": "atas kerjasamanya",
    "terima kasih banyak": "terima kasih banyak",
    "makasih banyak": "terima kasih banyak",
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