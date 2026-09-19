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

## Vulnerability scan

`pip-audit` is run against the hash-locked runtime set. CI runs it on every push and pull request
(`audit` job in `.github/workflows/ci.yml`), in its own step so the tool never enters the application
environment. A known advisory fails the job.

```bash
pip install -r requirements-audit.txt
pip-audit --progress-spinner=off --require-hashes -r requirements.txt
```

Last scan recorded here: 2026-09-19, pip-audit 2.10.1
(wheel `pip_audit-2.10.1-py3-none-any.whl`, SHA-256
`99ef3f600a317c1945f1e89e227ef26e1c2d618429b8bd3fa6f4f7c440c4611a`), Python 3.11.15.

| Package | Version | Known vulnerabilities |
|---|---|---|
| Django | 5.2.17 | none |
| asgiref | 3.12.1 | none |
| sqlparse | 0.6.0 | none |

Result: **no known vulnerabilities in the runtime dependencies.**

Scope and limits of that result:

- The scan covers the three packages in `requirements.txt`. It does not cover `pip`, `setuptools` or
  `wheel`, which a virtual environment bootstraps and which the application does not import at runtime.
  A separate scan of the whole environment on the same date reported PYSEC-2026-3447 against the
  bootstrapped `setuptools` 79.0.1; that advisory concerns `MANIFEST.in` matching when building a source
  distribution on macOS APFS/HFS+, which this project does not do. Upgrade `setuptools` to 83.0.0 or
  later in any environment that does build sdists.
- The recorded run used the PyPI advisory database (`-s pypi`). The OSV service, which `pip-audit` uses by
  default and which CI uses, was unreachable from the machine that produced this record, so OSV coverage
  for these versions is UNVERIFIED here and is established by the CI job instead.
- `requirements-audit.txt` pins `pip-audit` by version rather than by SHA-256. It is CI-only tooling, and
  its transitive wheel set varies by Python version and platform, so a hash lock resolved on one
  interpreter would break the job on another. The runtime set it checks stays fully hash-locked.

A clean scan is evidence about *known, published* advisories on the scan date. It is not evidence that the
dependencies are free of defects, and it goes stale: re-read the CI result rather than this table.

Not yet done: signed provenance.
