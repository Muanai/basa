"""
Tests for basa.normalize and basa.quick.

Each test function covers a clear and isolated scenario.
The global singleton state ``typo`` is managed via a fixture so that tests
do not interfere with each other.
"""

import pytest
from basa import normalize, quick, typo


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_typo_vocab():
    """
    Clear the typo singleton vocabulary before and after each test.

    This prevents the vocabulary state from one test leaking into another,
    because ``typo`` is a module-level singleton shared across all tests.
    """
    typo.clear_vocab()
    yield
    typo.clear_vocab()


# ─────────────────────────────────────────────────────────────────────────────
# SLANG NORMALIZATION
# ─────────────────────────────────────────────────────────────────────────────

class TestSlangNormalization:
    def test_pronoun_gw(self):
        assert normalize("gw gk ngerti") == "saya tidak mengerti"

    def test_pronoun_lu(self):
        assert normalize("lu udh makan") == "kamu sudah makan"

    def test_negation_variants(self):
        assert normalize("ga mau") == "tidak mau"
        assert normalize("gak mau") == "tidak mau"
        assert normalize("nggak mau") == "tidak mau"

    def test_compound_negation(self):
        # "gamau" should → "tidak mau" (compound slang, not two tokens)
        assert normalize("gw gamau pergi") == "saya tidak mau pergi"

    def test_apply_slang_false_skips_normalization(self):
        # If apply_slang=False, slang MUST NOT be changed at all
        assert normalize("gw gk ngerti", apply_slang=False) == "gw gk ngerti"

    def test_slang_with_mixed_real_words(self):
        # Standard words among slang should not be corrupted
        assert normalize("gw pergi ke pasar") == "saya pergi ke pasar"


# ─────────────────────────────────────────────────────────────────────────────
# REPEATED CHARACTER REDUCTION
# ─────────────────────────────────────────────────────────────────────────────

class TestRepeatCharReduction:
    def test_repeated_vowel_in_slang(self):
        assert normalize("bangeeeettt") == "banget"

    def test_repeated_chars_before_slang_lookup(self):
        # "gwwww" → "gw" (reduce) → "saya" (slang)
        assert normalize("gwwww gkkkk ngertiii") == "saya tidak mengerti"

    def test_double_consonant_kk_in_slang(self):
        # "kk" is in the slang dictionary → "kakak", not reduced to "k"
        # Validates that double-consonant representing a valid abbreviation
        # is treated as a slang lookup, rather than undergoing character removal.
        assert normalize("kk") == "kakak"


# ─────────────────────────────────────────────────────────────────────────────
# TWO-PASS NORMALIZATION PIPELINE (regression tests for fixed bugs)
# ─────────────────────────────────────────────────────────────────────────────

class TestTwoPassNormalizationPipeline:
    """
    Regression tests for the two-pass lookup pipeline introduced to fix a bug
    where global vowel reduction ran *before* dictionary lookup, destroying
    valid double-vowel sequences in slang abbreviations.

    Root cause: "krjaan" → (global 2+ vowel reduction) → "krjan"
                (not in dict) → stays as "krjan" instead of "pekerjaan".

    Fix: dictionary lookup now happens *before* per-token char reduction
    (Pass A), and again *after* (Pass B). Global strict reduction (3+ vowels
    only) runs as a fallback for out-of-vocab words.
    """

    def test_double_vowel_in_slang_abbreviation_preserved(self):
        # Regression: "krjaan" has a valid double-a that must NOT be reduced
        # before the slang lookup. "krjaan" → "pekerjaan" (not "pekerjan").
        assert normalize("krjaan byk bgt") == "pekerjaan banyak banget"

    def test_double_vowel_in_full_sentence_preserved(self):
        # Original bug report: "krjaan" inside a longer sentence.
        assert normalize("kzl bgt hr ini krjaan byk bgt") == "kesal banget hari ini pekerjaan banyak banget"

    def test_valid_double_vowel_in_replacement_not_corrupted(self):
        # Replacement outputs from the dict (e.g., "pekerjaan", "maaf") must
        # NOT have their legitimate double vowels collapsed by the global pass.
        result = normalize("krjaan")
        assert "aa" in result, f"Expected 'aa' in output, got: {result!r}"

    def test_elongated_slang_reduced_then_looked_up(self):
        # Pass B: elongated form not in dict → reduce first → lookup.
        # "gwwww" is not in dict; reduce → "gw" → "saya".
        assert normalize("gwwww") == "saya"

    def test_elongated_vowel_slang_reduced_then_looked_up(self):
        # "gkkkk" not in dict; reduce → "gk" → "tidak".
        assert normalize("gkkkk") == "tidak"

    def test_elongated_out_of_vocab_word_still_reduced(self):
        # Out-of-vocab elongated word: no dict entry, just apply fallback reduction.
        # "manaaaa" (4 a's) → strict pass collapses to "mana" (standard word).
        result = normalize("manaaaa")
        assert result == "mana"

    def test_valid_double_vowel_in_dict_output_not_corrupted(self):
        # The strict global reduction pass only collapses 3+ consecutive identical
        # vowels. Dictionary replacement outputs that contain legitimate double
        # vowels (e.g. "pekerjaan" has "aa") must NOT be collapsed.
        # "krjaan" -> "pekerjaan" (dict lookup). The global pass that follows
        # must not then collapse "aa" → "a" because it only triggers on 3+.
        result = normalize("krjaan")
        assert result == "pekerjaan", f"Expected 'pekerjaan', got: {result!r}"

    def test_batch_preserves_double_vowel(self):
        # Batch mode must exhibit the same correct behavior.
        inputs = ["krjaan byk bgt", "kzl bgt hr ini krjaan byk bgt"]
        results = normalize(inputs)
        assert "pekerjaan" in results[0]
        assert "pekerjaan" in results[1]
        assert "pekerjan" not in results[0]
        assert "pekerjan" not in results[1]


# ─────────────────────────────────────────────────────────────────────────────
# AMBIGUOUS MAPPING REMOVAL (kasih → berikan)
# ─────────────────────────────────────────────────────────────────────────────

class TestKasihMappingRemoved:
    """
    Regression tests for the removal of the ambiguous "kasih" → "berikan"
    mapping, which was corrupting multi-word phrases like "terima kasih".
    """

    def test_kasih_not_mapped_to_berikan(self):
        # "kasih" alone must NOT be replaced with "berikan" anymore.
        assert normalize("kasih") == "kasih"

    def test_terima_kasih_not_corrupted(self):
        # Key regression: "terima kasih" must stay as-is (or be normalized
        # via the greetings dict), never become "terima berikan".
        result = normalize("terima kasih")
        assert "berikan" not in result

    def test_makasih_still_maps_to_terima_kasih(self):
        # The shorthand "makasih" must still work via the greetings dictionary.
        assert normalize("makasih") == "terima kasih"

    def test_tq_still_maps_to_terima_kasih(self):
        # Other thanks shorthands unaffected.
        assert normalize("tq") == "terima kasih"

    def test_ksih_not_mapped_to_berikan(self):
        # "ksih" (the compressed variant) was also removed.
        assert normalize("ksih") == "ksih"


# ─────────────────────────────────────────────────────────────────────────────
# NEW DICTIONARY ENTRIES
# ─────────────────────────────────────────────────────────────────────────────

class TestNewDictionaryEntries:
    """Tests for slang words newly added to the dictionary."""

    def test_pegi_maps_to_pergi(self):
        assert normalize("pegi") == "pergi"

    def test_pegi_in_sentence(self):
        assert normalize("gw mau pegi dlu ya") == "saya mau pergi dulu ya"

    def test_nyesel_maps_to_menyesal(self):
        assert normalize("nyesel") == "menyesal"

    def test_nyesel_in_sentence(self):
        assert normalize("gw nyesel bgt") == "saya menyesal banget"

    def test_sgini_maps_to_sebanyak_ini(self):
        assert normalize("sgini") == "sebanyak ini"

    def test_segini_maps_to_sebanyak_ini(self):
        assert normalize("segini") == "sebanyak ini"

    def test_sgitu_maps_to_sebanyak_itu(self):
        assert normalize("sgitu") == "sebanyak itu"

    def test_segitu_maps_to_sebanyak_itu(self):
        assert normalize("segitu") == "sebanyak itu"

    def test_sgini_in_sentence(self):
        assert normalize("kok mahal sgini sih") == "kok mahal sebanyak ini sih"

    def test_sgitu_in_sentence(self):
        assert normalize("ga nyangka sgitu banyaknya") == "tidak nyangka sebanyak itu banyaknya"


# ─────────────────────────────────────────────────────────────────────────────
# PUNCTUATION REDUCTION
# ─────────────────────────────────────────────────────────────────────────────

class TestPunctuationReduction:
    def test_exclamation_mark(self):
        assert normalize("serius bgt!!!!!") == "serius banget!"

    def test_question_mark(self):
        assert normalize("harga naik terus????") == "harga naik terus?"

    def test_ellipsis_collapse(self):
        assert normalize("hmm.....") == "hmm."

    def test_single_punctuation_unchanged(self):
        # Single punctuation marks must not be changed
        assert normalize("serius!") == "serius!"
        assert normalize("makan?") == "makan?"

    def test_normalize_punctuation_false(self):
        # normalize_punctuation=False must preserve ALL repeated punctuation marks.
        # The slang engine's consonant reducer now excludes punctuation chars so
        # "!!!!!" is NOT collapsed internally — it is only collapsed by stage 4
        # which is disabled here.
        result = normalize("serius!!!!!", normalize_punctuation=False)
        assert result == "serius!!!!!"

    def test_mixed_punctuation_types(self):
        # Each type of punctuation is reduced independently
        assert normalize("wow!!! kok bisa???") == "wow! kok bisa?"


# ─────────────────────────────────────────────────────────────────────────────
# LOWERCASE
# ─────────────────────────────────────────────────────────────────────────────

class TestLowercase:
    def test_uppercase_input_lowercased_by_default(self):
        assert normalize("GW GK NGERTI") == "saya tidak mengerti"

    def test_lowercase_false_preserves_case(self):
        # Entity names (NER) must not be lowercased
        result = normalize("Jokowi pergi ke Jakarta", lowercase=False)
        assert result == "Jokowi pergi ke Jakarta"

    def test_lowercase_false_slang_engine_mirrors_case(self):
        # When lowercase=False, the slang engine still matches tokens
        # case-insensitively, but mirrors the matched token's casing onto
        # the replacement: ALL-CAPS → upper, Title → capitalize, lower → as-is.
        assert normalize("GW", lowercase=False) == "SAYA"
        assert normalize("Gw", lowercase=False) == "Saya"
        assert normalize("gw", lowercase=False) == "saya"

    def test_mixed_case_normalized(self):
        # "GwW" → (lowercase stage 1) "gww" → slang lookup
        # "gww" is not in the slang dictionary because char reduce in the slang engine
        # operates at the 3+ level for consonants ("www"→"w" but "gww" is not a slang token)
        # Only letters repeated 3+ times are reduced, so "gww" → remains "gww"
        # "gK" → "gk" → "tidak"
        result = normalize("GwW gK")
        assert "tidak" in result  # "gK" → "tidak" succeeds


# ─────────────────────────────────────────────────────────────────────────────
# WHITESPACE
# ─────────────────────────────────────────────────────────────────────────────

class TestWhitespace:
    def test_leading_trailing_stripped(self):
        assert normalize("  gw gk ngerti  ") == "saya tidak mengerti"

    def test_multiple_internal_spaces_collapsed(self):
        assert normalize("gw    gk   ngerti") == "saya tidak mengerti"

    def test_normalize_whitespace_false(self):
        result = normalize("gw    gk   ngerti", normalize_whitespace=False)
        # Spaces are not compressed, but slang is still replaced
        assert "    " in result or "   " in result

    def test_tabs_and_newlines_collapsed(self):
        assert normalize("gw\tgk\nngerti") == "saya tidak mengerti"


# ─────────────────────────────────────────────────────────────────────────────
# TYPO CORRECTION
# ─────────────────────────────────────────────────────────────────────────────

class TestTypoCorrection:
    def test_typo_disabled_by_default(self):
        # Even without a vocab, the default apply_typo=False must not cause an error.
        # Use "mkaan" (a misspelling of "makan") — not in the slang dict, no repeated chars.
        assert normalize("saya mkaan") == "saya mkaan"

    def test_typo_opt_in_corrects_word(self):
        typo.add_to_vocab({"makan", "minum"})
        assert normalize("saya mkaan", apply_typo=True) == "saya makan"

    def test_typo_safeguard_empty_vocab(self):
        # apply_typo=True with empty vocab → no error, does not modify text
        assert normalize("saya mkaan", apply_typo=True) == "saya mkaan"

    def test_typo_does_not_corrupt_in_vocab_word(self):
        typo.add_to_vocab({"makan", "minum"})
        # "makan" is already correct, must not be changed
        assert normalize("saya makan", apply_typo=True) == "saya makan"

    def test_typo_runs_after_slang(self):
        # Slang first: "gw" → "saya", then typo correction.
        # "mkaan" is a genuine typo of "makan", not in slang dict.
        typo.add_to_vocab({"makan", "saya"})
        result = normalize("gw mkaan", apply_typo=True)
        assert result == "saya makan"


# ─────────────────────────────────────────────────────────────────────────────
# BATCH PROCESSING
# ─────────────────────────────────────────────────────────────────────────────

class TestBatchProcessing:
    def test_list_of_strings(self):
        inputs = ["gw gk ngerti", "lu udh makan??"]
        expected = ["saya tidak mengerti", "kamu sudah makan?"]
        assert normalize(inputs) == expected

    def test_empty_list(self):
        assert normalize([]) == []

    def test_list_preserves_order(self):
        inputs = ["gw", "lu", "dia"]
        result = normalize(inputs)
        assert result[0] == "saya"
        assert result[1] == "kamu"

    def test_quick_batch(self):
        result = quick(["gw makan", "lu minum"])
        assert result == ["saya makan", "kamu minum"]


# ─────────────────────────────────────────────────────────────────────────────
# QUICK API
# ─────────────────────────────────────────────────────────────────────────────

class TestQuickApi:
    def test_quick_basic(self):
        assert quick("gw gk ngerti bngt sihhhh!!!") == "saya tidak mengerti banget sih!"

    def test_quick_is_equivalent_to_normalize_defaults(self):
        text = "gwww gkkkk ngertiiii bngtttt!!!!!"
        assert quick(text) == normalize(text)

    def test_quick_uppercase(self):
        # quick() should lowercase by default
        assert quick("GW GK NGERTI") == "saya tidak mengerti"


# ─────────────────────────────────────────────────────────────────────────────
# EDGE CASES
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_string(self):
        assert normalize("") == ""

    def test_whitespace_only_string(self):
        assert normalize("   ") == ""

    def test_already_normalized_text(self):
        # Standard text must not be changed by normalize
        assert normalize("saya pergi ke pasar") == "saya pergi ke pasar"

    def test_non_string_passthrough(self):
        # None and non-str are returned as-is, no error
        assert normalize(None) is None

    def test_numbers_unchanged(self):
        assert normalize("harga 50000") == "harga 50000"

    def test_url_like_string_unchanged(self):
        # URLs must not be corrupted by normalization
        result = normalize("cek di tokopedia.com")
        assert "tokopedia.com" in result


    def test_all_flags_false(self):
        # All stages turned off → text is returned as-is (pass-through only)
        raw = "GW GK NGERTI BNT!!!!!"
        result = normalize(
            raw,
            apply_slang=False,
            apply_typo=False,
            lowercase=False,
            normalize_punctuation=False,
            normalize_whitespace=False,
        )
        assert result == raw


# ─────────────────────────────────────────────────────────────────────────────
# REGRESSION: lowercase=False and normalize_punctuation=False flags
# ─────────────────────────────────────────────────────────────────────────────

class TestFlagRegressions:
    """
    Regression tests for two bugs where the ``lowercase`` and
    ``normalize_punctuation`` flags were ignored.

    Root cause 1 (lowercase):
        The slang engine's ``_replace()`` always returned the lowercase dict
        value regardless of the caller's ``lowercase`` flag.
        Fix: ``_mirror_case()`` maps the original token's casing pattern onto
        the replacement (ALL-CAPS → upper, Title → capitalize, lower → as-is).

    Root cause 2 (punctuation):
        ``_CONSONANT_REPEAT`` matched ``([^aeiouAEIOU\\s\\d])\\1{2+}``, which
        included punctuation chars, so ``!!!`` was collapsed inside the slang
        engine before stage 4 (``normalize_punctuation``) was even reached.
        Fix: pattern changed to ``([^\\W\\s\\daeiouAEIOU])\\1{2+}`` (letter
        consonants only), so punctuation reduction is exclusively controlled
        by ``normalize_punctuation``.
    """

    # ── lowercase=False ───────────────────────────────────────────────────────

    def test_lowercase_false_all_caps_sentence(self):
        # "GW KESEL BGT" → each token uppercase → replacements mirrored to upper
        result = normalize("GW KESEL BGT", lowercase=False)
        assert result == "SAYA KESEL BANGET"

    def test_lowercase_false_title_case_slang(self):
        # "Gw" is title-case → replacement should be capitalized
        assert normalize("Gw pergi", lowercase=False) == "Saya pergi"

    def test_lowercase_false_lowercase_slang_unchanged(self):
        # "gw" is lowercase → replacement stays lowercase (no change)
        assert normalize("gw pergi", lowercase=False) == "saya pergi"

    def test_lowercase_false_preserves_non_slang_caps(self):
        # Non-slang words (e.g. named entities) must keep their original case
        result = normalize("GW ke Jakarta", lowercase=False)
        assert "Jakarta" in result

    def test_lowercase_false_mixed_caps_in_sentence(self):
        # Combination: ALL-CAPS slang + regular lowercase word + non-slang caps
        result = normalize("GW KESEL BGT", lowercase=False)
        assert result == "SAYA KESEL BANGET"

    def test_lowercase_false_does_not_uppercase_non_matched_words(self):
        # Words not in the slang dict must not have their casing changed
        result = normalize("GW ke Jakarta", lowercase=False)
        assert "ke" in result  # lowercase non-slang preserved

    # ── normalize_punctuation=False ───────────────────────────────────────────

    def test_normalize_punctuation_false_preserves_triple_exclamation(self):
        # "!!!" must survive unchanged when normalize_punctuation=False
        result = normalize("keren bgt!!!", normalize_punctuation=False)
        assert result == "keren banget!!!"

    def test_normalize_punctuation_false_preserves_many_exclamations(self):
        # Five or more marks must also be preserved
        result = normalize("mantap!!!!!", normalize_punctuation=False)
        assert result == "mantap!!!!!"

    def test_normalize_punctuation_false_preserves_question_marks(self):
        result = normalize("serius????", normalize_punctuation=False)
        assert result == "serius????"

    def test_normalize_punctuation_false_preserves_mixed_punct(self):
        # Different punctuation types, each run kept intact
        result = normalize("wow!!! kok bisa???", normalize_punctuation=False)
        assert result == "wow!!! kok bisa???"

    def test_normalize_punctuation_true_still_collapses(self):
        # Ensure the default behaviour (True) still works after the regex fix
        assert normalize("keren bgt!!!") == "keren banget!"
        assert normalize("serius?????") == "serius?"

    # ── combined scenario from the original bug report ────────────────────────

    def test_typo_correction_pipeline(self):
        # Full pipeline: slang off → typo correction → correct output
        typo.add_to_vocab({"saya", "makan", "nasi", "goreng"})
        result = normalize("sayy mkan nsai groeng", apply_typo=True)
        assert result == "saya makan nasi goreng"

    def test_lowercase_false_and_punctuation_false_combined(self):
        # Both flags disabled simultaneously
        result = normalize("GW KESEL BGT!!!", lowercase=False, normalize_punctuation=False)
        assert result == "SAYA KESEL BANGET!!!"


# ─────────────────────────────────────────────────────────────────────────────
# REGRESSION: slang output must not be corrupted by typo corrector
#
# Bug: after slang normalization produced correct Indonesian words (e.g.
# "mahal", "kasih", "saudara"), the typo corrector saw them as OOV and
# mis-corrected them to the nearest word in the user's small vocab (e.g.
# "nasi", "makan") via Levenshtein distance.
#
# Fix: all slang dictionary *values* are pre-loaded into `typo._protected`
# at import time.  Words in that whitelist bypass the distance scan entirely.
# ─────────────────────────────────────────────────────────────────────────────

class TestTypoSlangInteraction:
    """
    Regression tests for the slang-output corruption bug.

    The typo corrector must never mutate a word that was legitimately
    produced by slang normalization, even when the user's vocabulary happens
    to contain a Levenshtein-close word.
    """

    # ── individual slang outputs that were historically mis-corrected ─────────

    def test_mahal_not_corrupted_to_makan(self):
        # "mhl" → (slang) "mahal".  With vocab {"makan"}, typo must NOT
        # replace "mahal" → "makan" (edit distance 2, would pass the old guard).
        typo.add_to_vocab({"makan"})
        result = normalize("mhl", apply_typo=True)
        assert result == "mahal", f"Expected 'mahal', got '{result}'"

    def test_kasih_not_corrupted_to_nasi(self):
        # "thx" → (slang) "terima kasih".  With vocab {"nasi"}, "kasih" must
        # not be replaced with "nasi" (edit dist 2, was falsely accepted before).
        typo.add_to_vocab({"nasi"})
        result = normalize("thx", apply_typo=True)
        assert result == "terima kasih", f"Expected 'terima kasih', got '{result}'"

    def test_saudara_not_corrupted(self):
        # "gan" → (slang) "saudara".  With a small vocab, "saudara" must
        # survive typo correction unchanged.
        typo.add_to_vocab({"makan", "nasi", "goreng"})
        result = normalize("gan", apply_typo=True)
        assert result == "saudara", f"Expected 'saudara', got '{result}'"

    # ── exact notebook scenario that originally triggered the bug ─────────────

    def test_ecommerce_review_pipeline_no_nasi_corruption(self):
        # Reproduces the exact bug from the notebook (Section 3 vocab leaking
        # into Section 6).  None of the three cleaned sentences should contain
        # the word "nasi" or "makan" in a position that was not in the original.
        typo.add_to_vocab({"saya", "makan", "nasi", "goreng"})

        r1 = normalize("brgnya bgssss bgt gk nyesel bli dsni thx gan!!!", apply_typo=True)
        assert "nasi" not in r1, f"'nasi' should not appear in: {r1}"
        assert "terima kasih" in r1

        r2 = normalize("pdhl hrga mhl tp kwalitas jlek kcewa pokonya..", apply_typo=True)
        assert "mahal" in r2, f"'mahal' should survive; got: {r2}"
        # "makan" must NOT appear where "mahal" was
        words_r2 = r2.split()
        assert words_r2.count("makan") == 0, f"Unexpected 'makan' in: {r2}"

        r3 = normalize("lmyn lh buat hrga sgini", apply_typo=True)
        assert r3 == "lumayan lah buat harga sebanyak ini"

    # ── protected vocab does not block legitimate typo correction ─────────────

    def test_typo_correction_still_works_for_non_slang_words(self):
        # Regression guard: the whitelist must not prevent correction of
        # genuine typos in words that are not slang outputs.
        typo.add_to_vocab({"saya", "makan", "nasi", "goreng"})
        result = normalize("sayy mkan nsai groeng", apply_typo=True)
        assert result == "saya makan nasi goreng"

    def test_typo_correction_disabled_by_default(self):
        # With apply_typo=False (default), the small vocab must have zero
        # influence on the output — slang engine alone runs.
        typo.add_to_vocab({"nasi", "goreng"})
        result = normalize("thx gan")
        assert result == "terima kasih saudara"