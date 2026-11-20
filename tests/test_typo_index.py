"""Tests for SymSpell-style _DeleteIndex, deterministic ranking, and default vocab."""

from __future__ import annotations

import time

import pytest

from basa.core.typo import (
    TypoCorrector,
    _bounded_levenshtein,
    _DeleteIndex,
    levenshtein_distance,
    typo,
)
from basa.core.vocab import DEFAULT_VOCAB


@pytest.fixture(autouse=True)
def _reset_singleton_typo():
    """Keep the module-level typo singleton isolated across tests."""
    typo.clear_vocab()
    yield
    typo.clear_vocab()


class TestBoundedLevenshtein:
    def test_matches_full_levenshtein_within_bound(self):
        pairs = [
            ("makan", "makan"),
            ("mkan", "makan"),
            ("mnder", "mander"),
            ("komptuer", "komputer"),
            ("tehknik", "teknik"),
            ("abc", "def"),
            ("", "ab"),
        ]
        for s1, s2 in pairs:
            full = levenshtein_distance(s1, s2)
            for max_dist in (0, 1, 2, 3):
                bounded = _bounded_levenshtein(s1, s2, max_dist)
                if full <= max_dist:
                    assert bounded == full
                else:
                    assert bounded > max_dist

    def test_length_difference_short_circuits(self):
        assert _bounded_levenshtein("a", "abcdef", 2) > 2


class TestDeleteIndex:
    def test_exact_equivalence_with_brute_force(self):
        vocab = {
            "makan",
            "minum",
            "masak",
            "mander",
            "teknik",
            "komputer",
            "indonesia",
            "kebersihan",
            "informasi",
            "aplikasi",
            "program",
            "data",
            "baru",
            "hari",
            "ini",
            "itu",
            "ada",
            "ab",
        }
        index = _DeleteIndex(max_edit_distance=2)
        for word in vocab:
            index.add(word)

        queries = [
            "mkan",
            "mnm",
            "tehknik",
            "komptuer",
            "indonsia",
            "kebrsihan",
            "infomasi",
            "apliksai",
            "proram",
            "dtaa",
            "brau",
            "hrai",
            "ac",
            "xyz",
            "komputerisasi",
        ]
        for max_dist in (1, 2):
            for query in queries:
                brute = {w for w in vocab if levenshtein_distance(query, w) <= max_dist}
                candidates = index.candidates(query, max_dist)
                verified = {
                    w
                    for w in candidates
                    if _bounded_levenshtein(query, w, max_dist) <= max_dist
                }
                assert verified == brute, (
                    f"Mismatch for query={query!r}, max_dist={max_dist}: "
                    f"index={verified} vs brute={brute}"
                )

    def test_incremental_add_remove_clear(self):
        index = _DeleteIndex(max_edit_distance=2)
        index.add("makan")
        index.add("minum")
        assert "makan" in index.candidates("mkan", 1)

        index.remove("makan")
        assert "makan" not in index.candidates("mkan", 1)
        assert "minum" in index.candidates("minm", 1)

        index.clear()
        assert index.candidates("minm", 1) == set()


class TestDeterministicRankingAndFallback:
    def test_deterministic_tie_breaking_across_insertion_orders(self):
        # Both "makan" and "makin" are distance 1 from "makun"
        order_a = ["makan", "makin", "makon"]
        order_b = ["makon", "makin", "makan"]

        c1 = TypoCorrector(min_word_length=4)
        for w in order_a:
            c1.add_to_vocab({w})

        c2 = TypoCorrector(min_word_length=4)
        for w in order_b:
            c2.add_to_vocab({w})

        assert c1.correct("makun", max_dist=1) == "makan"
        assert c2.correct("makun", max_dist=1) == "makan"
        assert c1.suggest("makun", max_dist=1, top_k=3) == ["makan", "makin", "makon"]
        assert c2.suggest("makun", max_dist=1, top_k=3) == ["makan", "makin", "makon"]

    def test_max_dist_above_2_fallback(self):
        corrector = TypoCorrector(
            vocab={"indonesia", "internasional"},
            min_word_length=4,
            min_confidence=0.4,
        )
        # Distance from "indonezxa" -> "indonesia" is 2, "indnxsa" -> 3
        assert corrector.correct("indnxsa", max_dist=3) == "indonesia"
        assert "indonesia" in corrector.suggest("indnxsa", max_dist=3, top_k=2)

    def test_remove_and_clear_vocab_update_index(self):
        corrector = TypoCorrector(vocab={"makan", "minum"}, min_word_length=4)
        assert corrector.correct("mkan") == "makan"

        corrector.remove_from_vocab({"makan"})
        assert corrector.correct("mkan") == "mkan"
        assert corrector.correct("minm") == "minum"

        corrector.clear_vocab()
        assert corrector.correct("minm") == "minm"


class TestCorrectTextGuards:
    def test_skips_urls_domains_digits_and_preserves_punctuation(self):
        corrector = TypoCorrector(
            vocab={"teknik", "komputer", "indonesia", "kebersihan"},
            min_word_length=4,
        )
        text = (
            "tehknik komptuer, https://www.indonesia.go.id/tes "
            "www.komptuer.id user@indonsia.id @kebrsihan #tehknik 12345 v2 ..."
        )
        result = corrector.correct_text(text)
        assert result == (
            "teknik komputer, https://www.indonesia.go.id/tes "
            "www.komptuer.id user@indonsia.id @kebrsihan #tehknik 12345 v2 ..."
        )


class TestDefaultVocab:
    def test_load_default_vocab_populates_and_corrects(self):
        assert len(DEFAULT_VOCAB) > 100
        typo.load_default_vocab()
        assert len(typo) == len(DEFAULT_VOCAB)

        assert typo.correct("tehknik") == "teknik"
        assert typo.correct("komptuer") == "komputer"
        assert typo.correct("indonsia") == "indonesia"
        assert typo.correct("kebrsihan") == "kebersihan"


@pytest.mark.slow
def test_50k_vocab_scaling_and_latency():
    words = {f"kata{i:05d}indo" for i in range(50_000)}
    corrector = TypoCorrector(vocab=words, min_word_length=4)

    queries = [f"ktaa{i:05d}indo" for i in range(0, 50_000, 500)]
    latencies_ms: list[float] = []
    for q in queries:
        t0 = time.perf_counter()
        res = corrector.correct(q, max_dist=2)
        latencies_ms.append((time.perf_counter() - t0) * 1000.0)
        assert res.startswith("kata")

    latencies_ms.sort()
    p50 = latencies_ms[len(latencies_ms) // 2]
    assert p50 < 5.0, f"Expected p50 < 5.0 ms at 50k vocab, got {p50:.3f} ms"
