import re
from typing import Dict, Optional

_DEFAULT_SLANG = {
    "gw": "saya",
    "gue": "saya",
    "gua": "saya",
    "lu": "kamu",
    "lo": "kamu",
    "elo": "kamu",
    "gk": "tidak",
    "ga": "tidak",
    "ngga": "tidak",
    "nggak": "tidak",
    "gak": "tidak",
    "udh": "sudah",
    "dah": "sudah",
    "bgt": "banget",
    "bngt": "banget",
    "klo": "kalau",
    "kalo": "kalau",
    "krn": "karena",
    "karna": "karena",
    "yg": "yang",
    "dgn": "dengan",
    "tp": "tapi",
    "tpi": "tapi",
    "jg": "juga",
    "aja": "saja",
    "syg": "sayang",
    "bkn": "bukan",
    "sm": "sama",
    "utk": "untuk",
    "dr": "dari",
    "blm": "belum",
    "pd": "pada",
    "dlm": "dalam",
    "bs": "bisa",
    "jd": "jadi",
    "otw": "dalam perjalanan"
}

class SlangDictionary:
    def __init__(self, custom_mapping: Optional[Dict[str, str]] = None):
        self.mapping = _DEFAULT_SLANG.copy()
        if custom_mapping:
            self.mapping.update(custom_mapping)
        self._regex = None
        self._compile_pattern()

    def _compile_pattern(self):
        sorted_keys = sorted(self.mapping.keys(), key=len, reverse=True)
        escaped_keys = [re.escape(k) for k in sorted_keys]
        pattern = r'\b(' + '|'.join(escaped_keys) + r')\b'
        self._regex = re.compile(pattern, re.IGNORECASE)

    def add(self, word: str, replacement: str):
        self.mapping[word.lower()] = replacement
        self._compile_pattern()

    def remove(self, word: str):
        word_lower = word.lower()
        if word_lower in self.mapping:
            del self.mapping[word_lower]
            self._compile_pattern()

    def normalize(self, text: str) -> str:
        if not text:
            return text

        def _replace(match):
            word = match.group(1).lower()
            return self.mapping.get(word, word)

        return self._regex.sub(_replace, text)

slang = SlangDictionary()