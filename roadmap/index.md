# Roadmap

BASA is building toward a modern NLP ecosystem for Indonesian and regional languages.

Our philosophy is to ship stable, well-tested features incrementally rather than pursuing rapid expansion without maintenance guarantees.

---

## v0.1 — Text Normalization Foundation

Status: Stable Foundation

Core features:

* `quick()` zero-configuration API
* `normalize()` configurable normalization pipeline
* Indonesian slang normalization
* Repeated-character reduction (`gkkkk → gk`)
* Conservative typo correction (opt-in)
* Batch processing support
* Full documentation with MkDocs
* Automated CI and testing pipeline

---

## v0.2 — Translation Utilities

Planned features:

* Javanese → Indonesian translation
* Indonesian → Javanese translation
* Sundanese → Indonesian translation
* Indonesian → Sundanese translation
* Regional language dictionaries
* Rule-based baseline translators

Goal:

Provide lightweight utilities for low-resource Indonesian regional language processing.

---

## v0.3 — Indonesian NLP Evaluation Tools

Planned features:

* Factual consistency evaluation for Indonesian summarization
* ROUGE utilities for Indonesian datasets
* BERTScore integration
* IndoBART evaluation helpers
* Explainable evaluation reports

Goal:

Make Indonesian NLP evaluation more accessible and reproducible.

---

## v0.4 — Dataset Utilities

Planned features:

* Dataset loaders
* Dataset validators
* Train/validation/test split helpers
* IndoBERT preprocessing utilities
* IndoBART preprocessing pipelines

Goal:

Reduce boilerplate for Indonesian NLP experiments and research projects.

---

## v0.5 — Low-Resource Language Support

Planned features:

* Synthetic data generation tools
* Augmentation pipelines
* Dictionary expansion utilities
* Data quality checks
* Support for additional Indonesian regional languages

Goal:

Lower the barrier to building NLP systems for underrepresented local languages.

---

## Long-Term Vision

BASA aims to become a practical NLP toolkit for:

* Indonesian text normalization
* Regional language processing
* Evaluation and benchmarking
* Dataset preparation
* Low-resource language development

The project prioritizes:

* Developer experience
* Conservative defaults
* Production-friendly APIs
* Strong documentation
* Incremental and maintainable growth
