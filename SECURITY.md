# Security Policy

## Supported Versions

Security fixes are released for the following versions of BASA:

| Version | Supported |
|---|---|
| `0.2.x` | Yes |
| `0.1.x` | Security fixes only (upgrade to `0.2.x` recommended) |
| `< 0.1.0` | No |

## Reporting a Vulnerability

Please **do not** report security vulnerabilities through public GitHub issues.

Instead, use one of the following private channels:

* **GitHub Private Vulnerability Reporting:** Submit an advisory at [https://github.com/Muanai/basa/security/advisories/new](https://github.com/Muanai/basa/security/advisories/new).
* **Email:** Send details to [muanaikhalifahr@gmail.com](mailto:muanaikhalifahr@gmail.com) with the subject line `[SECURITY] basa: <short summary>`.

Please include:

* Affected BASA version (`python -c "import basa; print(basa.__version__)"`)
* Reproduction steps or a minimal proof-of-concept input
* Potential impact (for example, catastrophic regex backtracking / ReDoS, unexpected memory exhaustion, or encoding issues)

### What to Expect

* You will receive an acknowledgment within **72 hours**.
* Once confirmed, we will work on a fix and coordinate disclosure before publishing a security advisory and patch release.
