# Supply-chain evidence (v0.1.0)

All runtime dependencies are pinned by SHA-256 in `requirements.txt`; pip refuses any file that does not match.

| Package | Version | Wheel SHA-256 | Licence (from wheel metadata) | Matches PyPI digest |
|---|---|---|---|---|
| Django | 5.2.17 (LTS) | f04fb3b36ee119e1af4fa1d397d5fd6cf12700f49321e84d4f4c642c5b1973db | BSD-3-Clause | yes |
| asgiref | 3.12.1 | fe386d1c2bff7259ea95929266d12a8cf9a8b5a1c2598402967d8792e7a7c094 | BSD-3-Clause | yes |
| sqlparse | 0.6.0 | b861c0288ce2fa56209a9a6412d2e066ac664b3873b89c26c9d8415e8e32996f | BSD | yes |

Method: wheels downloaded with `pip download --only-binary=:all:` into a quarantine folder, hashed with
`sha256sum`, licence read from the wheel's METADATA without executing it, and each hash compared with the
digest published by the PyPI JSON API. Only wheels were used, so no third-party install hooks ran.

Not yet done: vulnerability scan (for example `pip-audit` or OSV-Scanner) and signed provenance.
