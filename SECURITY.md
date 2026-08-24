# Security Policy

## Supported Versions

Zenith AI is actively maintained. Security patches and dependency updates are applied to the latest `main` branch.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Architecture & Privacy Model

Zenith AI is built on a **Zero Cloud Egress / 100% On-Device Privacy Architecture**:
* Neural SLM inference (`phi-4-mini`) and dense embeddings (`qwen3-embedding`) execute strictly on local hardware via the Microsoft Foundry Local SDK.
* No telemetry, prompt tokens, ingested documents, or chat histories are transmitted to third-party cloud endpoints or external APIs.
* File uploads and vector indices are persisted locally in SQLite (`data/zenith.db`).

## Reporting a Vulnerability

If you discover a security vulnerability within Zenith AI, please report it responsibly:
1. **GitHub Private Vulnerability Reporting:** Use the [Report a Vulnerability](https://github.com/Cagrik34/microsoft-foundry-local-rag-assistant/security/advisories/new) button in the Security tab.
2. **Direct Contact:** Alternatively, reach out directly to the maintainer via GitHub issues or email.

Please include:
* Description of the vulnerability.
* Steps to reproduce the issue.
* Potential impact.

We take security seriously and will investigate and patch verified vulnerabilities promptly.