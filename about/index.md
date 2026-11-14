# About BASA

## What is BASA?

BASA is an open-source NLP toolkit for Indonesian and regional languages.

The project focuses on building practical, developer-friendly tools for Indonesian text processing, beginning with informal text normalization and gradually expanding toward regional language support, evaluation utilities, and dataset tooling.

The name **BASA** comes from the Indonesian and Javanese word *bahasa*, reflecting the project's long-term vision of supporting Indonesia's linguistic diversity.

---

## Creator

BASA was created by Muanai Khalifah Revindo, an Informatics Engineering student at Universitas Sriwijaya.

His work primarily focuses on:

* Artificial Intelligence
* Machine Learning
* Risk Intelligence Systems
* Operational Analytics
* Indonesian NLP
* Low-resource language technologies

BASA represents an effort to build practical open-source infrastructure for Indonesian and regional-language NLP ecosystems.

---

## Why BASA Exists

Many modern NLP tools are designed primarily around English-language workflows.

Indonesian developers often need to solve challenges such as:

* Social media slang normalization
* Repeated-character reduction
* Informal text preprocessing
* Regional language support
* Low-resource dataset preparation

BASA aims to address these problems through simple APIs, conservative defaults, and strong developer experience.

---

## Design Principles

BASA follows several core principles:

### Conservative by Default

Potentially destructive operations, such as typo correction, are opt-in rather than automatic.

### Indonesian First

The project prioritizes Indonesian NLP problems before expanding to broader multilingual use cases.

### Incremental Growth

Features are introduced gradually, with an emphasis on maintainability, testing, and documentation.

### Developer Experience

Most workflows should require only a few lines of code:

```python
from basa import quick

quick("gw gk ngerti bngtttt")
```

---

## Long-Term Vision

The long-term goal of BASA is to become a practical ecosystem for Indonesian and regional-language NLP, including:

* Text normalization
* Translation utilities
* Evaluation frameworks
* Dataset tooling
* Synthetic data generation
* Low-resource language support

The project values practical usability and sustainable open-source development over rapid feature expansion.

---

## Open Source

BASA is an open-source project released under the MIT License.

Community contributions, feedback, and collaboration are always welcome.
