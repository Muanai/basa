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

import re
from collections import defaultdict
from collections.abc import Iterable

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

    previous_row: list[int] = list(range(len(s2) + 1))

    for i, c1 in enumerate(s1):
        current_row: list[int] = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def _bounded_levenshtein(s1: str, s2: str, max_dist: int) -> int:
    """
    Compute Levenshtein edit distance bounded by ``max_dist``.

    Short-circuits immediately when string lengths differ by more than
    ``max_dist``, and exits early if the minimum value in a DP row exceeds
    ``max_dist``.

    Returns:
        Exact edit distance if ``<= max_dist``, otherwise ``max_dist + 1``.
    """
    if max_dist < 0:
        return 0 if s1 == s2 else 1

    if abs(len(s1) - len(s2)) > max_dist:
        return max_dist + 1

    # Strip matching prefix and suffix (invariant under Levenshtein distance)
    start = 0
    len1, len2 = len(s1), len(s2)
    while start < len1 and start < len2 and s1[start] == s2[start]:
        start += 1
    while len1 > start and len2 > start and s1[len1 - 1] == s2[len2 - 1]:
        len1 -= 1
        len2 -= 1

    s1 = s1[start:len1]
    s2 = s2[start:len2]

    m, n = len(s1), len(s2)
    if m < n:
        s1, s2 = s2, s1
        m, n = n, m

    if n == 0:
        return m if m <= max_dist else max_dist + 1

    if m - n > max_dist:
        return max_dist + 1

    inf = max_dist + 1
    prev: list[int] = list(range(n + 1))
    curr: list[int] = [0] * (n + 1)

    for i in range(m):
        c1 = s1[i]
        j_start = i - max_dist
        if j_start < 0:
            j_start = 0
        j_end = i + max_dist + 1
        if j_end > n:
            j_end = n

        curr[0] = i + 1
        if j_start > 0:
            curr[j_start] = inf
        row_min = curr[j_start]

        for j in range(j_start, j_end):
            cost = prev[j] if c1 == s2[j] else prev[j] + 1
            ins = prev[j + 1] + 1
            if ins < cost:
                cost = ins
            dele = curr[j] + 1
            if dele < cost:
                cost = dele
            curr[j + 1] = cost
            if cost < row_min:
                row_min = cost

        if j_end < n:
            curr[j_end + 1] = inf
        if row_min > max_dist:
            return inf
        prev, curr = curr, prev

    return prev[n]


# ─────────────────────────────────────────────────────────────────────────────
# SYMSPELL-STYLE DELETE INDEX
# ─────────────────────────────────────────────────────────────────────────────


class _DeleteIndex:
    """
    SymSpell-style symmetric delete index for sub-linear candidate lookup.

    Stores all substrings obtained by deleting up to ``max_edit_distance``
    characters from each vocabulary word. Any query within edit distance
    ``d <= max_edit_distance`` of a vocabulary word is guaranteed to share at
    least one delete key with that word.
    """

    def __init__(self, max_edit_distance: int = 2) -> None:
        self.max_edit_distance = max_edit_distance
        self._words: set[str] = set()
        self._deletes: defaultdict[str, set[str]] = defaultdict(set)

    @staticmethod
    def _generate_deletes(word: str, max_dist: int) -> set[str]:
        """Return ``word`` and all deletions up to ``max_dist`` characters."""
        result: set[str] = {word}
        frontier: set[str] = {word}
        for _ in range(max_dist):
            next_frontier: set[str] = set()
            for token in frontier:
                for idx in range(len(token)):
                    deleted = token[:idx] + token[idx + 1 :]
                    if deleted not in result:
                        result.add(deleted)
                        next_frontier.add(deleted)
            if not next_frontier:
                break
            frontier = next_frontier
        return result

    def add(self, word: str) -> None:
        """Index a single lowercased word."""
        if word in self._words:
            return
        self._words.add(word)
        for key in self._generate_deletes(word, self.max_edit_distance):
            self._deletes[key].add(word)

    def remove(self, word: str) -> None:
        """Remove a single lowercased word from the index."""
        if word not in self._words:
            return
        self._words.remove(word)
        for key in self._generate_deletes(word, self.max_edit_distance):
            bucket = self._deletes.get(key)
            if bucket is not None:
                bucket.discard(word)
                if not bucket:
                    del self._deletes[key]

    def clear(self) -> None:
        """Clear all indexed words and delete buckets."""
        self._words.clear()
        self._deletes.clear()

    def candidates(self, word: str, max_dist: int) -> set[str]:
        """
        Return candidate vocabulary words potentially within ``max_dist``.

        Falls back to a length-filtered scan over indexed words when
        ``max_dist`` exceeds ``self.max_edit_distance``.
        """
        if max_dist <= self.max_edit_distance:
            matches: set[str] = set()
            for key in self._generate_deletes(word, max_dist):
                bucket = self._deletes.get(key)
                if bucket is not None:
                    matches.update(bucket)
            return matches

        return {w for w in self._words if abs(len(w) - len(word)) <= max_dist}


_SKIP_TOKEN_RE: re.Pattern[str] = re.compile(
    r"^(?:https?://\S+|www\.\S+|\S+@\S+\.\S+|[@#]\S+|.*\d.*)$",
    re.IGNORECASE,
)
_EDGE_PUNCT_RE: re.Pattern[str] = re.compile(r"^([^a-zA-Z]*)([a-zA-Z]+)([^a-zA-Z]*)$")


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
        vocab: set[str] | None = None,
        min_word_length: int = 4,
        min_confidence: float = 0.5,
    ) -> None:
        self.vocab: set[str] = {w.lower() for w in vocab} if vocab else set()
        self.min_word_length = min_word_length
        self.min_confidence = min_confidence

        self._index = _DeleteIndex(max_edit_distance=2)
        for word in self.vocab:
            self._index.add(word)

        # ── Protected vocab (whitelist) ───────────────────────────────────────
        # Words in this set are always returned unchanged by correct(), even
        # when they are not in self.vocab.  This lets normalize.py silently
        # shield all slang-output values (e.g. "mahal", "terima kasih") from
        # being mis-corrected back to a short user vocab like {"nasi", "goreng"}.
        # Managed internally — not exposed as a public vocabulary to the caller.
        self._protected: set[str] = set()

        # ── Lookup cache ─────────────────────────────────────────────────────
        # Maps lowercased token → corrected word.
        # In real-world corpora the same misspelling often appears hundreds of
        # times (e.g. "gk", "bgt", "udh"). Caching avoids recomputing the
        # full vocab scan on every occurrence.
        # The cache is invalidated whenever the vocabulary changes.
        self._cache: dict[str, str] = {}

        # ── Cache statistics ─────────────────────────────────────────────────
        # Useful for profiling and tuning cache effectiveness.
        self._cache_hits: int = 0
        self._cache_misses: int = 0

    # ─── Internal ────────────────────────────────────────────────────────────

    def _invalidate_cache(self) -> None:
        """
        Clear the lookup cache.

        Must be called whenever self.vocab is mutated so that stale
        corrections are not returned for newly added words.
        """
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    # ─── Protected vocab management ──────────────────────────────────────────

    def set_protected(self, words: Iterable[str]) -> None:
        """
        Replace the internal whitelist with the given words.

        Words in the protected set are always returned as-is by correct(),
        bypassing both the Levenshtein scan and the confidence filter.
        This is used by normalize.py to shield slang-output values from
        accidental re-correction.

        Args:
            words: Iterable of words to protect (multi-word values are
                   split on whitespace so each token is protected individually).

        Example:
            >>> corrector.set_protected({"mahal", "terima kasih"})
        """
        self._protected = {
            token for phrase in words for token in phrase.lower().split()
        }
        self._invalidate_cache()

    # ─── Vocabulary management ───────────────────────────────────────────────

    def add_to_vocab(self, words: Iterable[str]) -> None:
        """
        Add words to the vocabulary and invalidate the lookup cache.

        Args:
            words: Iterable of words to add (stored as lowercase).

        Example:
            >>> corrector.add_to_vocab({"lightgbm", "catboost", "xgboost"})
        """
        for w in words:
            lw = w.lower()
            self.vocab.add(lw)
            self._index.add(lw)
        self._invalidate_cache()

    def remove_from_vocab(self, words: Iterable[str]) -> None:
        """
        Remove words from the vocabulary and invalidate the lookup cache.

        Args:
            words: Iterable of words to remove.

        Example:
            >>> corrector.remove_from_vocab({"kredivo"})
        """
        for w in words:
            lw = w.lower()
            self.vocab.discard(lw)
            self._index.remove(lw)
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
        self._index.clear()
        self._invalidate_cache()

    def load_default_vocab(self) -> None:
        """Populate the vocabulary with BASA's built-in Indonesian word list."""
        from .vocab import DEFAULT_VOCAB

        self.add_to_vocab(DEFAULT_VOCAB)

    def _find_candidates(self, word_lower: str, max_dist: int) -> Iterable[str]:
        """Return candidate words from the index (or vocab if mutated directly)."""
        if len(self._index._words) == len(self.vocab):
            return self._index.candidates(word_lower, max_dist)
        return (c for c in self.vocab if abs(len(word_lower) - len(c)) <= max_dist)

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

        # Guard 2: Word is protected (slang output whitelist) — skip correction
        # This prevents words like "mahal" or "kasih" (produced by slang
        # normalization) from being mis-corrected to a short user vocab word
        # (e.g. "nasi" or "goreng") that happens to be close in edit distance.
        if word_lower in self._protected:
            return word

        # Guard 3: Word already in vocab — already correct
        if word_lower in self.vocab:
            return word

        # Guard 4: Word too short — correction is too risky
        # e.g. "di", "ya", "ok" have many neighbours at distance 1–2
        if len(word_lower) < self.min_word_length:
            return word

        # Guard 5: Return cached result if available
        if word_lower in self._cache:
            self._cache_hits += 1
            return self._cache[word_lower]

        self._cache_misses += 1

        # ── Indexed candidate lookup with deterministic tie-breaking ─────────
        best_match: str | None = None
        min_dist = max_dist + 1

        for candidate in self._find_candidates(word_lower, max_dist):
            dist = _bounded_levenshtein(word_lower, candidate, max_dist)
            if dist <= max_dist and (
                dist < min_dist
                or (dist == min_dist and (best_match is None or candidate < best_match))
            ):
                min_dist = dist
                best_match = candidate

        # ── Confidence filter ────────────────────────────────────────────────
        # confidence = fraction of characters that are "correct".
        # e.g. "mkan" (len 4) corrected to "makan" (dist 1):
        #   confidence = 1 - 1/4 = 0.75  →  accepted if min_confidence ≤ 0.75
        result = word
        if best_match is not None:
            confidence = 1.0 - (min_dist / max(len(word_lower), 1))
            if confidence >= self.min_confidence:
                result = best_match

        # Store result in cache before returning
        self._cache[word_lower] = result
        return result

    def correct_text(self, text: str, max_dist: int = 2) -> str:
        """
        Correct all tokens in a text string.

        Splits on whitespace and corrects alphabetic tokens while skipping
        URLs, domains, emails, social handles, hashtags, digits, and pure
        punctuation. Leading/trailing punctuation around alphabetic words is
        preserved.

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

        corrected: list[str] = []
        for token in text.split():
            if _SKIP_TOKEN_RE.match(token):
                corrected.append(token)
                continue
            match = _EDGE_PUNCT_RE.match(token)
            if match is None:
                corrected.append(token)
                continue
            prefix, core, suffix = match.groups()
            corrected.append(f"{prefix}{self.correct(core, max_dist)}{suffix}")
        return " ".join(corrected)

    def suggest(self, word: str, max_dist: int = 2, top_k: int = 3) -> list[str]:
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

        candidates: list[tuple[int, str]] = []
        for candidate in self._find_candidates(word_lower, max_dist):
            dist = _bounded_levenshtein(word_lower, candidate, max_dist)
            if dist <= max_dist:
                candidates.append((dist, candidate))

        candidates.sort(key=lambda x: (x[0], x[1]))
        return [c[1] for c in candidates[:top_k]]

    # ─── Diagnostics ─────────────────────────────────────────────────────────

    def cache_info(self) -> dict[str, int]:
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
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "size": len(self._cache),
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
