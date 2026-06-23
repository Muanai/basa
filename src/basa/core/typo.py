"""
BASA - Typo Correction Module
==============================
Detects and corrects out-of-vocabulary words using Levenshtein distance
against a user-supplied vocabulary set.

Design philosophy:
    - Vocabulary is NOT bundled into the library core. Every domain has
      different vocabulary needs (fintech, e-commerce, ML, telecom), so
      the caller is responsible for providing a relevant word list.
    - The corrector is intentionally conservative: short words and
      low-confidence matches are left untouched to avoid false positives.
    - A lookup cache prevents redundant computation when the same token
      appears many times in a corpus (very common in real-world data).

Limitations (to be addressed in v0.2):
    - Linear scan over vocab is O(|vocab| × |word| × |candidate|).
      For large vocabularies (50 k+ words) consider replacing the inner
      loop with a BK-Tree or SymSpell index.
    - Correction is purely character-level; no phonetic or semantic context
      is used. The closest-distance word wins regardless of meaning.

Pipeline position:
    Typo correction should run AFTER slang normalization and repeated-
    character reduction, so that tokens like "gkkkk" are already collapsed
    to "gk" (and then translated to "tidak") before the corrector sees them.

    Recommended order:
        lowercase → repeated-char normalization → slang replacement
        → typo correction → whitespace cleanup

Usage:
    from basa.core.typo import TypoCorrector

    corrector = TypoCorrector(min_word_length=4)
    corrector.add_to_vocab({"makan", "minum", "masak", "mander"})

    corrector.correct("mander")   # → "mander" (in vocab, no change)
    corrector.correct("mnder")    # → "mander" (distance 1, corrected)
    corrector.correct("ok")       # → "ok" (below min_word_length, skipped)

    # Batch sentence correction
    corrector.correct_text("saya mkan dan mnder")
    # → "saya makan dan mander"

    # Inspect cache hit rate (useful for profiling)
    print(corrector.cache_info())

Notes:
    - All comparisons are lowercased internally.
    - The module-level singleton `typo` ships with an empty vocabulary.
      Add domain words via add_to_vocab() or pass vocab= at construction.
"""

from __future__ import annotations

from typing import Dict, Optional, Set, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# LEVENSHTEIN DISTANCE
# ─────────────────────────────────────────────────────────────────────────────

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Compute the Levenshtein (edit) distance between two strings.

    The distance counts the minimum number of single-character edits
    (insertions, deletions, or substitutions) required to transform
    s1 into s2.

    Implementation uses the standard iterative DP approach with a
    single previous-row buffer, keeping memory usage O(min(|s1|, |s2|)).

    Args:
        s1: First string.
        s2: Second string.

    Returns:
        Non-negative integer representing the edit distance.

    Examples:
        >>> levenshtein_distance("makan", "makan")
        0
        >>> levenshtein_distance("mkan", "makan")
        1
        >>> levenshtein_distance("mnder", "mander")
        1
        >>> levenshtein_distance("xyz", "abc")
        3
    """
    # Ensure s1 is the longer string (optimises the inner loop slightly)
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    # Edge case: one string is empty
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)

    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions   = previous_row[j + 1] + 1
            deletions    = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


# ─────────────────────────────────────────────────────────────────────────────
# TYPO CORRECTOR
# ─────────────────────────────────────────────────────────────────────────────

class TypoCorrector:
    """
    Context-free typo corrector based on minimum Levenshtein distance.

    The corrector scans an unknown token against a vocabulary set and
    returns the closest-matching word within a configurable edit distance.
    Two safety guards prevent aggressive over-correction:

    1. ``min_word_length``: tokens shorter than this threshold are returned
       unchanged. Very short words (1–3 chars) have many near-neighbours
       at distance 1–2, making false positives very likely.

    2. ``min_confidence``: a soft ratio guard. After the best candidate
       is found, confidence is computed as::

           confidence = 1 - (edit_distance / len(word))

       If confidence is below this threshold the original word is kept.
       Default 0.5 means at most half the characters may be wrong.

    Args:
        vocab:            Initial vocabulary set (lowercase recommended).
        min_word_length:  Minimum token length to attempt correction.
                          Tokens below this length are returned as-is.
                          Default: 4.
        min_confidence:   Minimum correction confidence in [0, 1].
                          Default: 0.5.

    Example:
        >>> corrector = TypoCorrector(min_word_length=4)
        >>> corrector.add_to_vocab({"makan", "minum", "masak"})
        >>> corrector.correct("mkan")
        'makan'
        >>> corrector.correct("ok")   # length 2 < min_word_length
        'ok'
    """

    def __init__(
        self,
        vocab: Optional[Set[str]] = None,
        min_word_length: int = 4,
        min_confidence: float = 0.5,
    ) -> None:
        self.vocab: Set[str] = {w.lower() for w in vocab} if vocab else set()
        self.min_word_length = min_word_length
        self.min_confidence  = min_confidence

        # ── Lookup cache ─────────────────────────────────────────────────────
        # Maps lowercased token → corrected word.
        # In real-world corpora the same misspelling often appears hundreds of
        # times (e.g. "gk", "bgt", "udh"). Caching avoids recomputing the
        # full vocab scan on every occurrence.
        # The cache is invalidated whenever the vocabulary changes.
        self._cache: Dict[str, str] = {}

        # ── Cache statistics ─────────────────────────────────────────────────
        # Useful for profiling and tuning cache effectiveness.
        self._cache_hits:   int = 0
        self._cache_misses: int = 0

    # ─── Internal ────────────────────────────────────────────────────────────

    def _invalidate_cache(self) -> None:
        """
        Clear the lookup cache.

        Must be called whenever self.vocab is mutated so that stale
        corrections are not returned for newly added words.
        """
        self._cache.clear()
        self._cache_hits   = 0
        self._cache_misses = 0

    # ─── Vocabulary management ───────────────────────────────────────────────

    def add_to_vocab(self, words: Set[str]) -> None:
        """
        Add words to the vocabulary and invalidate the lookup cache.

        Args:
            words: Set of words to add (stored as lowercase).

        Example:
            >>> corrector.add_to_vocab({"lightgbm", "catboost", "xgboost"})
        """
        self.vocab.update(w.lower() for w in words)
        self._invalidate_cache()

    def remove_from_vocab(self, words: Set[str]) -> None:
        """
        Remove words from the vocabulary and invalidate the lookup cache.

        Args:
            words: Set of words to remove.

        Example:
            >>> corrector.remove_from_vocab({"kredivo"})
        """
        self.vocab -= {w.lower() for w in words}
        self._invalidate_cache()

    def clear_vocab(self) -> None:
        """
        Empty the vocabulary entirely and invalidate the cache.

        Example:
            >>> corrector.clear_vocab()
            >>> len(corrector)
            0
        """
        self.vocab.clear()
        self._invalidate_cache()

    # ─── Correction ──────────────────────────────────────────────────────────

    def correct(self, word: str, max_dist: int = 2) -> str:
        """
        Correct a single token against the vocabulary.

        Decision logic:
            1. If vocab is empty → return original (nothing to compare).
            2. If token is already in vocab → return original (correct).
            3. If len(token) < min_word_length → return original (too risky).
            4. Check cache → return cached result if available.
            5. Linear scan over vocab with length-delta pruning.
            6. Apply confidence filter → return original if below threshold.

        Args:
            word:     Input token (any case).
            max_dist: Maximum Levenshtein distance to consider a correction.
                      Higher values are more permissive but riskier.
                      Default: 2.

        Returns:
            Corrected word (lowercase) if a confident match is found,
            otherwise the original word unchanged.

        Examples:
            >>> corrector.correct("mkan")    # dist 1 from "makan"
            'makan'
            >>> corrector.correct("ok")      # below min_word_length
            'ok'
            >>> corrector.correct("xyz123")  # no close match in vocab
            'xyz123'
        """
        word_lower = word.lower()

        # Guard 1: No vocab loaded — nothing to do
        if not self.vocab:
            return word

        # Guard 2: Word already in vocab — already correct
        if word_lower in self.vocab:
            return word

        # Guard 3: Word too short — correction is too risky
        # e.g. "di", "ya", "ok" have many neighbours at distance 1–2
        if len(word_lower) < self.min_word_length:
            return word

        # Guard 4: Return cached result if available
        if word_lower in self._cache:
            self._cache_hits += 1
            return self._cache[word_lower]

        self._cache_misses += 1

        # ── Linear scan with length-delta pruning ────────────────────────────
        # Skipping candidates whose length differs by more than max_dist
        # avoids computing Levenshtein for obviously too-different words,
        # providing a significant speedup for large vocabularies.
        best_match = word
        min_dist   = float('inf')

        for candidate in self.vocab:
            # Fast pre-filter: if lengths differ by more than max_dist,
            # the edit distance is guaranteed to exceed max_dist — skip.
            if abs(len(word_lower) - len(candidate)) > max_dist:
                continue

            dist = levenshtein_distance(word_lower, candidate)

            if dist < min_dist and dist <= max_dist:
                min_dist   = dist
                best_match = candidate

        # ── Confidence filter ────────────────────────────────────────────────
        # confidence = fraction of characters that are "correct".
        # e.g. "mkan" (len 4) corrected to "makan" (dist 1):
        #   confidence = 1 - 1/4 = 0.75  →  accepted if min_confidence ≤ 0.75
        if best_match != word:
            confidence = 1.0 - (min_dist / max(len(word_lower), 1))
            if confidence < self.min_confidence:
                best_match = word   # Not confident enough — keep original

        # Store result in cache before returning
        self._cache[word_lower] = best_match
        return best_match

    def correct_text(self, text: str, max_dist: int = 2) -> str:
        """
        Correct all tokens in a text string.

        Splits on whitespace, corrects each token independently, then
        rejoins with a single space. Punctuation attached to words
        (e.g. "mkan,") is treated as part of the token and may not
        match the vocab — consider stripping punctuation upstream.

        Args:
            text:     Input text string.
            max_dist: Passed through to correct().

        Returns:
            Text with out-of-vocab tokens corrected where possible.

        Example:
            >>> corrector.correct_text("saya mkan dan mnder sore ini")
            'saya makan dan mander sore ini'
        """
        if not text:
            return text

        corrected = [self.correct(w, max_dist) for w in text.split()]
        return " ".join(corrected)

    def suggest(self, word: str, max_dist: int = 2, top_k: int = 3) -> List[str]:
        """
        Suggest closest vocabulary matches for an unknown word.

        Unlike correct(), this returns a list of possibilities without
        forcing a replacement, making it safe for exploratory pipelines.

        Args:
            word: Input token (any case).
            max_dist: Maximum Levenshtein distance to consider.
            top_k: Maximum number of suggestions to return.

        Returns:
            List of candidate strings, sorted by closest edit distance.
        """
        word_lower = word.lower()

        if not self.vocab:
            return []

        if word_lower in self.vocab:
            return [word_lower]

        candidates = []
        for candidate in self.vocab:
            if abs(len(word_lower) - len(candidate)) > max_dist:
                continue

            dist = levenshtein_distance(word_lower, candidate)
            if dist <= max_dist:
                candidates.append((dist, candidate))

        # Urutkan berdasarkan jarak terkecil, lalu ambil top_k
        candidates.sort(key=lambda x: x[0])
        return [c[1] for c in candidates[:top_k]]

    # ─── Diagnostics ─────────────────────────────────────────────────────────

    def cache_info(self) -> Dict[str, int]:
        """
        Return cache hit/miss statistics.

        Useful for profiling: a high hit rate indicates the cache is
        working well; a low rate may suggest highly varied input.

        Returns:
            Dict with keys ``hits``, ``misses``, and ``size``.

        Example:
            >>> corrector.cache_info()
            {'hits': 120, 'misses': 35, 'size': 35}
        """
        return {
            "hits":   self._cache_hits,
            "misses": self._cache_misses,
            "size":   len(self._cache),
        }

    # ─── Dunder helpers ──────────────────────────────────────────────────────

    def __len__(self) -> int:
        """Return the number of words in the vocabulary."""
        return len(self.vocab)

    def __contains__(self, word: str) -> bool:
        """Check if a word is in the vocabulary (case-insensitive)."""
        return word.lower() in self.vocab

    def __repr__(self) -> str:
        return (
            f"TypoCorrector("
            f"vocab_size={len(self.vocab)}, "
            f"min_word_length={self.min_word_length}, "
            f"min_confidence={self.min_confidence})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# MODULE-LEVEL CONVENIENCE SINGLETON
#
# Ships with an empty vocabulary — the caller must populate it.
#
# Quick start:
#   from basa.core.typo import typo
#   typo.add_to_vocab({"makan", "minum", "masak"})
#   typo.correct_text("saya mkan dan mnder")
#
# For domain-specific use:
#   from basa.core.typo import TypoCorrector
#   corrector = TypoCorrector(vocab=my_word_set, min_word_length=4)
# ─────────────────────────────────────────────────────────────────────────────
typo = TypoCorrector()