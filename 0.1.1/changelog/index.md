# Changelog

All notable changes to BASA will be documented in this file.

The project follows Semantic Versioning (SemVer).

---

## [Unreleased]

---

## [0.1.1] - 2026-11-14

Patch release focusing on over-normalization (`ONER`) safety, dictionary integrity, and runtime hygiene.

### Fixed

* Protected URLs, `www.*` domains, email addresses, `@handles`, and `#hashtags` from character-repetition reduction and slang substitution (fixes `www.indonesia.go.id` $\rightarrow$ `saya.indonesia.go.id`).
* Isolated the two-pass slang normalization pipeline so Step 1 replacement outputs are never re-expanded in Step 3.
* Removed unprompted English loanword translations (`meeting`, `deadline`, `database`, `email`, `reject`, etc.) and false-positive standard Indonesian mutations (`lalu`, `parah`, `gila`, `nya`) to preserve code-switched and formal text.
* Deduplicated all 47 colliding keys across category dictionaries in `slang.py` (resolving conflicts on `dr`, `dah`, `lo`, `kpi`, and `nih`).
* Moved documentation dependencies (`mkdocs-ask-ai`, `pydantic`) out of core runtime dependencies (`dependencies = []`) and resolved strict `mypy` type annotations.

---

## [0.1.0] - 2026-07-02

First stable release.

### Added

* Added runtime version introspection via `basa.__version__`.
* Added `slang.supported_words()` and support for `len(slang)` to inspect supported slang mappings.

---

## [0.1.0rc1] - 2026-06-30

Release candidate.

### Added

* GitHub Actions CI workflow for automated testing and linting.
* Ruff configuration for linting and formatting.

### Fixed

* Preserve list length consistency during batch normalization.

---

## [0.1.0rc0] - 2026-06-30

First release candidate.

### Added

* Initial release candidate milestone.
* Stabilized public API for v0.1.0.

---

## [0.1.0b3] - 2026-06-29

### Added

* Material for MkDocs documentation setup.
* GitHub Pages deployment workflow.
* Additional slang dictionary entries for adjectives, verbs, and question forms.

### Changed

* Updated dictionary statistics in the README.

---

## [0.1.0b2] - 2026-06-28

### Added

* Regression tests for typo and slang interactions.

### Fixed

* Prevent slang normalization outputs from being incorrectly modified by the typo corrector.

---

## [0.1.0b1] - 2026-06-26

### Added

* Additional regression tests for the normalization pipeline.

### Fixed

* Respect `lowercase=False`.
* Respect `normalize_punctuation=False`.

---

## [0.1.0b0] - 2026-06-25

First beta release.

### Added

* Expanded normalization test coverage.

### Changed

* Improved slang normalization pipeline.
* Expanded slang dictionary coverage.

---

## [0.1.0a4] - 2026-06-24

### Added

* New slang entries across multiple categories.
* Expanded dictionary coverage to more than 1,600 entries.

### Changed

* Optimized slang dictionary implementation.

---

## [0.1.0a3] - 2026-06-24

### Added

* Additional slang categories and normalization rules.

---

## [0.1.0a2] - 2026-06-24

### Changed

* Internal improvements to normalization components.

---

## [0.1.0a1] - 2026-06-23

### Added

* Improved public API exports.
* Initial testing infrastructure.
* Comprehensive project README.

### Changed

* Refined package structure for the first alpha release.

---

## [0.1.0a0] - 2026-06-23

Initial alpha release.

### Added

* Project scaffolding and directory structure.
* Modern Python packaging using `pyproject.toml` and `uv`.
* Regex-based slang normalization engine.
* Character reduction pipeline.
* Typo correction module with suggestions and caching.
* Public normalization APIs:

  * `normalize()`
  * `quick()`
