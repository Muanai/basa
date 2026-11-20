# Frequently Asked Questions

## What is BASA?

BASA is an open-source NLP toolkit for Indonesian and regional languages.

The project currently focuses on text normalization, including slang normalization, repeated-character reduction, and conservative typo correction for Indonesian informal text.

---

## Who created BASA?

BASA was created and is maintained by Muanai Khalifah Revindo, an Informatics Engineering student at Universitas Sriwijaya with interests in AI, machine learning, and risk intelligence systems.

Learn more on the About page.

---

## Why is typo correction disabled by default?

Typo correction can unintentionally modify:

* Proper nouns
* Technical terms
* Acronyms
* Domain-specific vocabulary

To avoid destructive transformations, BASA uses conservative defaults and requires users to explicitly enable typo correction.

```python
from basa import normalize

normalize(
    text,
    apply_typo=True
)
```

---

## Does BASA support batch processing?

Yes.

BASA supports both individual strings and lists of strings.

```python
from basa import normalize

texts = [
    "gw gk ngerti",
    "udh makan blm?"
]

normalize(texts)
```

---

## Does BASA support Javanese?

Not yet.

Javanese support is planned for future releases, including translation utilities between Indonesian and Javanese.

---

## Does BASA support Sundanese?

Not yet.

Support for Sundanese translation and processing tools is part of the long-term roadmap.

---

## Is BASA production-ready?

Version 0.1 establishes the first stable public API.

The project prioritizes:

* Conservative defaults
* Automated testing
* Continuous integration
* Clear documentation
* Backward compatibility whenever possible

Users are encouraged to evaluate BASA within their own production requirements.

---

## Why build a separate Indonesian NLP toolkit?

Many existing NLP libraries primarily target English-language workflows.

BASA focuses on practical challenges specific to Indonesia, such as:

* Social media slang
* Informal text normalization
* Regional languages
* Indonesian evaluation pipelines
* Low-resource language development

---

## Is BASA free to use?

Yes.

BASA is released under the MIT License and can be used in personal, academic, and commercial projects.

---

## How can I contribute?

Contributions are welcome.

You can help by:

* Reporting bugs
* Suggesting new features
* Improving documentation
* Expanding slang dictionaries
* Adding tests
* Supporting regional language resources

Please open an issue or pull request on GitHub.
