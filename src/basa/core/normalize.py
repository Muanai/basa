"""
BASA - Top-level Normalization API
====================================
Provides the simple 1-line normalization interface for the library.

Pipeline (in order):
    1. Lowercase               – optional, default True
    2. Slang normalization     – replaces slang + reduces repeated chars
    3. Typo correction         – Levenshtein-based, strictly opt-in
    4. Punctuation reduction   – collapses repeated punctuation (!!!! → !)
    5. Whitespace cleanup      – trims and collapses multiple spaces

Design philosophy:
    - Conservative by default: only safe, lossless transforms are enabled.
    - Destructive features (typo correction) are strictly opt-in.
    - ``_normalize_single`` handles one string; ``normalize`` handles both
      str and List[str] inputs so adding new parameters never breaks the
      batch path.

Usage:
    >>> from basa import normalize
    >>> normalize("GW GKKKK NGERTIII BNGTTTT!!!!!")
    'saya tidak mengerti banget!'

    >>> normalize("Jokowi pergi ke Jakarta", lowercase=False)
    'Jokowi pergi ke Jakarta'

    >>> normalize(["gw mkan", "dia mnum"], apply_slang=True)
    ['saya makan', 'dia minum']
"""

from __future__ import annotations

import re

from .slang import slang as slang_engine
from .typo import typo as typo_engine

# ─────────────────────────────────────────────────────────────────────────────
# SLANG OUTPUT WHITELIST
# ─────────────────────────────────────────────────────────────────────────────
# All normalised values produced by the slang engine (e.g. "mahal", "terima
# kasih", "saudara") must never be treated as typos.  We pre-compute the set
# once at import time and pass it to the typo engine as a protected vocab so
# that words which are already correct are not mis-corrected to whatever small
# vocabulary the caller happens to have loaded.
_SLANG_OUTPUT_WORDS: frozenset = frozenset(
    token for value in slang_engine.mapping.values() for token in value.lower().split()
)
typo_engine.set_protected(_SLANG_OUTPUT_WORDS)


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def _reduce_punctuation(text: str) -> str:
    """
    Collapse runs of repeated punctuation characters to a single character.

    Only targets common sentence-ending / emphasis punctuation so that
    legitimate patterns (e.g. ellipsis "...") are also collapsed cleanly.
    This is intentionally narrow to avoid touching hyphens, slashes, etc.

    Affected characters: . , ! ? ~ * - _

    Examples:
        >>> _reduce_punctuation("bagus banget!!!!!")
        'bagus banget!'
        >>> _reduce_punctuation("hmmm.....serius???")
        'hmmm.serius?'
        >>> _reduce_punctuation("seru~~~~ banget~~")
        'seru~ banget~'
    """
    # Match 2+ consecutive occurrences of the same punctuation character
    return re.sub(r"([.!?,~*\-_])\1+", r"\1", text)


def _normalize_single(
    text: str,
    apply_slang: bool,
    apply_typo: bool,
    lowercase: bool,
    normalize_punctuation: bool,
    normalize_whitespace: bool,
) -> str:
    """
    Apply the full normalization pipeline to a single string.

    This is the internal workhorse. ``normalize()`` delegates here for
    every input string so that adding new parameters only requires
    updating the signature in one place.

    Args:
        text:                  Input string (assumed to be a non-empty str).
        apply_slang:           If True, run slang normalization.
        apply_typo:            If True, run typo correction (opt-in).
        lowercase:             If True, convert to lowercase first.
        normalize_punctuation: If True, collapse repeated punctuation.
        normalize_whitespace:  If True, trim and collapse multiple spaces.

    Returns:
        Normalized string.
    """
    # ── Stage 1: Lowercase ───────────────────────────────────────────────────
    # Must come first so slang matching is case-insensitive.
    if lowercase:
        text = text.lower()

    # ── Stage 2: Slang Normalization ─────────────────────────────────────────
    # Handles repeated-char reduction AND slang dict lookup.
    # e.g. "GKKKK" → (lower) "gkkkk" → (char reduce) "gk" → "tidak"
    # We defer whitespace normalization to Stage 5.
    if apply_slang:
        text = slang_engine.normalize(
            text, normalize_whitespace=False, lowercase=lowercase
        )

    # ── Stage 3: Typo Correction (Strictly Opt-in) ───────────────────────────
    # Safeguard: skip if vocab is empty to prevent no-op full-corpus scans.
    if apply_typo and typo_engine.vocab:
        text = typo_engine.correct_text(text)

    # ── Stage 4: Punctuation Reduction ───────────────────────────────────────
    # e.g. "!!!!!" → "!", "?????" → "?", "....." → "."
    if normalize_punctuation:
        text = _reduce_punctuation(text)

    # ── Stage 5: Whitespace Cleanup ──────────────────────────────────────────
    if normalize_whitespace:
        text = re.sub(r"\s+", " ", text).strip()

    return text


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────


def normalize(
    text: str | list[str],
    apply_slang: bool = True,
    apply_typo: bool = False,
    lowercase: bool = True,
    normalize_punctuation: bool = True,
    normalize_whitespace: bool = True,
) -> str | list[str]:
    """
    Normalize informal Indonesian text with a single line of code.

    Applies a configurable pipeline of normalization stages to the input.
    Accepts a single string or a list of strings.

    Design Notes:
        - ``lowercase=True`` by default so slang matching works reliably.
          Set ``lowercase=False`` when case matters (e.g. for NER tasks).
        - ``apply_typo=False`` by default. Typo correction is opt-in because
          it requires a populated vocabulary and can corrupt domain-specific
          terms (e.g. "xgboost", "lightgbm", proper nouns). Always load
          your vocabulary via ``basa.typo.add_to_vocab()`` before enabling.

    Args:
        text:                  Input string or list of strings to normalize.
        apply_slang:           If True (default), apply slang dictionary
                               lookup and repeated-character reduction.
        apply_typo:            If True, apply Levenshtein-based typo
                               correction. Default False. Silently skipped
                               if the typo engine's vocabulary is empty.
        lowercase:             If True (default), convert text to lowercase
                               before processing. Set False to preserve
                               casing (e.g. for NER pipelines).
        normalize_punctuation: If True (default), collapse repeated
                               punctuation marks (e.g. "!!!" → "!").
        normalize_whitespace:  If True (default), trim leading/trailing
                               whitespace and collapse internal runs of
                               spaces to a single space.

    Returns:
        Normalized string if input is str, or list of the same length if
        input is a list. Non-string elements (``None``, ``""``, integers,
        etc.) inside a list are passed through unchanged so that the output
        index always matches the input index.

    Examples:
        >>> from basa import normalize

        >>> normalize("GW GKKKK NGERTIII BNGTTTT!!!!!")
        'saya tidak mengerti banget!'

        >>> normalize("gw gk ngerti bngt sihhhh!!!")
        'saya tidak mengerti banget sih!'

        >>> normalize("Jokowi pergi ke Jakarta", lowercase=False)
        'Jokowi pergi ke Jakarta'

        >>> normalize(["gw mkan", "dia mnum"])
        ['saya makan', 'dia minum']

        >>> normalize(["halo", "", None])
        ['halo', '', None]

        >>> normalize("harga naik terus????", normalize_punctuation=True)
        'harga naik terus?'
    """
    # ── Batch path ────────────────────────────────────────────────────────────
    # Delegates each element to _normalize_single — adding new parameters
    # here only requires updating _normalize_single's signature, not this call.
    #
    # Guard note: the isinstance check is a *ternary guard*, not a filter, so
    # non-string elements (None, "", integers) are passed through unchanged and
    # the output list is always the same length as the input list.
    if isinstance(text, list):
        return [
            _normalize_single(
                t,
                apply_slang=apply_slang,
                apply_typo=apply_typo,
                lowercase=lowercase,
                normalize_punctuation=normalize_punctuation,
                normalize_whitespace=normalize_whitespace,
            )
            if isinstance(t, str) and t
            else t
            for t in text
        ]

    # ── Guard: invalid / empty input ─────────────────────────────────────────
    if not text or not isinstance(text, str):
        return text

    return _normalize_single(
        text,
        apply_slang=apply_slang,
        apply_typo=apply_typo,
        lowercase=lowercase,
        normalize_punctuation=normalize_punctuation,
        normalize_whitespace=normalize_whitespace,
    )
