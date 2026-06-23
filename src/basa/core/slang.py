"""
BASA - Slang Normalization Module
===================================
Converts informal/colloquial Indonesian text (including Javanese/Sundanese
particles) into standardized Indonesian.

Supported categories:
    - Pronouns (aku/kamu shortcuts)
    - Negation (ga/gak/nggak → tidak)
    - Compound negation (gamau, gabisa, gatau → tidak mau, dll)
    - Conjunctions & prepositions (abbreviations like yg, dgn, krn)
    - Common verbs (udah, blm, mo, tau, liat, dll)
    - Adjectives & adverbs (bgt, bener, dll)
    - Question words (knp, gmn, kmn, dll)
    - Greetings & responses (makasih, ok, sip, dll)
    - Temporal & location (skrg, ntr, kmrn, sini, dll)
    - Internet slang → Indonesian equivalent (btw, lol, omg, dll)
    - E-commerce & finance (ongkir, rekber, tf, dll)
    - Youth & Gen-Z slang (mager, baper, gabut, dll)
    - Javanese/Sundanese particles (nggih, mboten, monggo, dll)

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
    "aq":   "aku",
    "ak":   "aku",
    "akuh": "aku",
    "w":    "saya",
    "gw":   "saya",
    "gue":  "saya",
    "gua":  "saya",
    # Second person
    "u":    "kamu",
    "lu":   "kamu",
    "lo":   "kamu",
    "loe":  "kamu",
    "elo":  "kamu",
    "elu":  "kamu",
    "km":   "kamu",
    # Third person
    "dy":   "dia",
    "dya":  "dia",
    # Plural
    "mrk":  "mereka",
    "qt":   "kita",
    "kln":  "kalian",
}

# Kinship & address terms
_KINSHIP: Dict[str, str] = {
    "kk":    "kakak",
    "kak":   "kakak",
    "adk":   "adik",
    "adk":   "adik",
    "bpk":   "bapak",
    "ayh":   "ayah",
    "ibu":   "ibu",           # already standard, included for completeness
    "klg":   "keluarga",
    "klrg":  "keluarga",
    "kel":   "keluarga",
    "ortu":  "orang tua",
    "ortuku": "orang tuaku",
    "suami": "suami",         # already standard
    "istri": "istri",         # already standard
    "anak":  "anak",          # already standard
}

# Standalone negation words
_NEGATION: Dict[str, str] = {
    "g":      "tidak",
    "ga":     "tidak",
    "gak":    "tidak",
    "gk":     "tidak",
    "ngga":   "tidak",
    "nggak":  "tidak",
    "engga":  "tidak",
    "enggak": "tidak",
    "kagak":  "tidak",
    "nope":   "tidak",
    "nop":    "tidak",
}

# Compound negation — written as one word without spaces (very common in chat)
# e.g. "gamau" = "ga" + "mau" = "tidak mau"
# NOTE: These MUST be registered before single-char negation in the dict so
# that the longest-first sort in _compile_pattern() handles them correctly.
_COMPOUND_NEGATION: Dict[str, str] = {
    "gamau":   "tidak mau",
    "gmau":    "tidak mau",
    "gabisa":  "tidak bisa",
    "gbisa":   "tidak bisa",
    "gakbisa": "tidak bisa",
    "gapunya": "tidak punya",
    "gpunya":  "tidak punya",
    "gasuka":  "tidak suka",
    "gsuka":   "tidak suka",
    "gaada":   "tidak ada",
    "gada":    "tidak ada",   # gaada → gada after vowel reduction
    "gatau":   "tidak tahu",
    "gtau":    "tidak tahu",
    "gatahu":  "tidak tahu",
    "gaperlu": "tidak perlu",
    "gperlu":  "tidak perlu",
    "gaboleh": "tidak boleh",
    "gboleh":  "tidak boleh",
}

# Conjunctions, prepositions, and formal abbreviations
_CONJUNCTIONS: Dict[str, str] = {
    "tp":    "tapi",
    "tpi":   "tapi",
    "trs":   "terus",
    "trus":  "terus",
    "dr":    "dari",
    "sm":    "sama",
    "ama":   "sama",
    "dpt":   "dapat",
    "tdk":   "tidak",
    "krn":   "karena",
    "krna":  "karena",
    "karna": "karena",
    "utk":   "untuk",
    "bwt":   "buat",
    "spy":   "supaya",
    "klo":   "kalau",
    "kalo":  "kalau",
    "yg":    "yang",
    "dgn":   "dengan",
    "dg":    "dengan",
    "jg":    "juga",
    "bkn":   "bukan",
    "pd":    "pada",
    "dlm":   "dalam",
    # Formal abbreviations
    "dll":   "dan lain-lain",
    "dsb":   "dan sebagainya",
    "dst":   "dan seterusnya",
    "tsb":   "tersebut",
    "yth":   "yang terhormat",
    "nb":    "catatan",
}

# Verbs and auxiliary verbs
_VERBS: Dict[str, str] = {
    "udh":     "sudah",
    "sdh":     "sudah",
    "dah":     "sudah",
    "udah":    "sudah",
    "udeh":    "sudah",
    "blm":     "belum",
    "blum":    "belum",
    "lg":      "sedang",
    "lgi":     "sedang",
    "bs":      "bisa",
    "bsa":     "bisa",
    "jd":      "jadi",
    "mo":      "mau",
    "mw":      "mau",
    "tau":     "tahu",
    "taw":     "tahu",
    "pake":    "pakai",
    "make":    "pakai",
    "liat":    "lihat",
    "liad":    "lihat",
    "ngerti":  "mengerti",
    "ngarti":  "mengerti",
    "nanya":   "bertanya",
    "nyari":   "mencari",
    "nyoba":   "mencoba",
    "ngomong": "berbicara",
    "nunggu":  "menunggu",
    "lakuin":  "lakukan",
    "byr":     "bayar",
    "hrs":     "harus",
    "blh":     "boleh",
    "prlu":    "perlu",
    "blg":     "bilang",
    "sk":      "suka",
    "dtg":     "datang",
    "dateng":  "datang",
    "pergi":   "pergi",
}

# Adjectives, adverbs, and discourse particles
_ADJECTIVES_ADVERBS: Dict[str, str] = {
    "bgt":   "banget",
    "bngt":  "banget",
    "bnget": "banget",
    "bget":  "banget",
    "bener": "benar",
    "bnr":   "benar",
    "bner":  "benar",
    "cepet": "cepat",
    "ttp":   "tetap",
    "lbh":   "lebih",
    "krg":   "kurang",
    "sdkt":  "sedikit",
    "dikit": "sedikit",
    "dkit":  "sedikit",
    "hny":   "hanya",
    "bbrp":  "beberapa",
    "emg":   "memang",
    "emang": "memang",
    "aja":   "saja",
    "doang": "saja",
    "kek":   "seperti",
    "kayak": "seperti",
    "kyk":   "seperti",
    "syg":   "sayang",
    # Common informal particles mapped to nearest standard equivalent
    "nih":   "ini",
    "tuh":   "itu",
    "yuk":   "ayo",
    "ae":    "saja",         # Sundanese/Javanese particle
    "wae":   "saja",         # Sundanese: just/only
    "tok":   "saja",         # Javanese: only
}

# Question words
_QUESTION_WORDS: Dict[str, str] = {
    "knp":    "kenapa",
    "gmn":    "bagaimana",
    "gimana": "bagaimana",
    "gmna":   "bagaimana",
    "gimna":  "bagaimana",
    "kmn":    "kemana",
    "dmn":    "di mana",
    "drmn":   "dari mana",
    "drmana": "dari mana",
    "kpn":    "kapan",
    "manaa":  "mana",
}

# Greetings, affirmations, and common social responses
_GREETINGS_RESPONSES: Dict[str, str] = {
    # Thanks
    "makasih":     "terima kasih",
    "makasi":      "terima kasih",
    "mksh":        "terima kasih",
    "mksih":       "terima kasih",
    "trims":       "terima kasih",
    "thx":         "terima kasih",
    "ty":          "terima kasih",
    # Requests
    "pls":         "tolong",
    "pliss":       "tolong",
    "plz":         "tolong",
    "tlg":         "tolong",
    # Apology
    "mf":          "maaf",
    "afwan":       "maaf",         # Arabic-Indonesian
    # Agreement
    "ok":          "oke",
    "okee":        "oke",
    "okelah":      "oke",
    "sip":         "baik",
    "iy":          "iya",
    "yap":         "ya",
    "yep":         "ya",
    "mantul":      "mantap betul",
    # Javanese / Sundanese particles (polite registers)
    "nggih":       "iya",          # Javanese: yes (polite)
    "inggih":      "iya",          # Javanese: yes (formal)
    "mboten":      "tidak",        # Javanese: no/not
    "monggo":      "silakan",      # Javanese: please go ahead
    "suwun":       "terima kasih", # Javanese: thank you
    "matur suwun": "terima kasih", # Javanese: thank you (full form)
    "nuwun":       "terima kasih", # Javanese: thank you
    # Arabic-Indonesian
    "syukron":     "terima kasih",
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
}

# Internet slang — mapped to Indonesian equivalents (not English)
_INTERNET_SLANG: Dict[str, str] = {
    "otw":    "dalam perjalanan",
    "btw":    "omong-omong",
    "fyi":    "sebagai informasi",
    "imo":    "menurut saya",
    "imho":   "menurut saya",
    "cmiiw":  "koreksi jika saya salah",
    "lol":    "tertawa",
    "wkwk":   "tertawa",
    "wkwwk":  "tertawa",
    "wkwkwk": "tertawa",
    "awokwok":"tertawa",
    "xixi":   "tertawa",     # Chinese laughter, common in Indonesian social media
    "lmao":   "tertawa keras",
    "omg":    "astaga",
    "idk":    "saya tidak tahu",
    "tbh":    "sejujurnya",
    "ngl":    "sejujurnya",
    "nvm":    "lupakan saja",
    "jk":     "bercanda",
    "np":     "tidak masalah",
    "afk":    "pergi sebentar",
    "brb":    "segera kembali",
    "dm":     "pesan langsung",
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
    "jastip": "jasa titip",
    "pesen":  "pesan",
    "minat":  "berminat",
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
    "sbnrnya":  "sebenarnya",
    "sbnr":     "sebenarnya",
    "mending":  "lebih baik",
    "sih":      "sih",             # discourse particle — keep as-is
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