# Leema Incubation Hub: guidance for Claude Code

## This repository holds two unrelated projects
- **The public website**: `index.html` plus `assets/`, one static page, no build step. Published to GitHub
  Pages from the repository root by `.github/workflows/pages.yml` on every push to main. Everything in this
  repository is publicly readable and publicly served, the Hub's source included.
- **The Incubation Hub** (below): `manage.py`, `hub/`, `incubator/`, `templates/`, `static/hub/`, `docs/`.

They share no code, no build and no data. A change to one is not a change to the other. `static/hub/` is the
Hub's stylesheet and has nothing to do with the site's `assets/`.

## Project
Django 5.2 LTS app for Leema Township Incubator (LEEMA Incubation NPC, Bodirelo Industrial Park, Mogwase).
Tracks enterprises from application to graduation and produces quarterly figures for Seda/SEDFA reporting.

- `incubator/models.py`: domain model. Stage changes go ONLY through `Enterprise.move_to()`, which enforces
  `Enterprise.TRANSITIONS` and writes the append-only `StageChange` log. Never bypass it or edit history.
- Financial year runs April-March (`fy_quarter()`); Q1 = Apr-Jun.
- Data entry uses Django admin (`incubator/admin.py`). Prefer extending admin over building new CRUD screens.
- UI: `templates/`, `static/hub/hub.css`. Board green `#1F4D3A`, marking yellow `#E8B820`, Barlow type.
  The pipeline "circuit trace" is the one signature element; keep everything else plain.
- South African formats live in `hub/formats/en_ZA/formats.py`.

## Commands
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --require-hashes -r requirements.txt
export DJANGO_DEBUG=1
python manage.py migrate
python manage.py test incubator                  # must pass before any commit
python manage.py makemigrations --check --dry-run
DJANGO_DEBUG=0 DJANGO_SECRET_KEY=x-long-random DJANGO_ALLOWED_HOSTS=h python manage.py check --deploy
pip install -r requirements-audit.txt                      # CI-only tooling, separate environment
pip-audit --require-hashes -r requirements.txt             # dependency vulnerability scan
python manage.py seed_demo                       # fictional data, empty database only
```

## N7 working rules (apply to every task)
1. Start each task with a short run contract: target, task, phase, acceptance criteria, exit condition,
   out of scope. One bounded phase per task; do not cross into deployment or production on your own.
2. Never fabricate evidence. Hashes, versions, test results and command output are reported only if
   they came from a command run in this session; otherwise say UNVERIFIED.
3. Label judgement calls as INFERENCE with evidence -> criterion -> conclusion.
4. Open-source first: reuse Django and mature libraries before writing new subsystems.
5. Dependencies: pin exact versions with SHA-256 hashes in `requirements.txt`, confirm each hash matches
   PyPI and record the licence in `docs/SUPPLY_CHAIN.md`. Prefer wheels (no install hooks). Any change to
   `requirements.txt` must be followed by a `pip-audit` run, and the record in `docs/SUPPLY_CHAIN.md`
   updated with what was actually observed.
6. Smallest coherent change; add or tighten a test for every behaviour you change or bug you fix.
   A weak test is not evidence.
7. Distinguish system defects from environment limitations (missing tool, no network).
8. Finish with: result (PASS / HOLD / UNVERIFIED), what was observed, inferences, what remains
   unverified, whether anything was mutated, and exactly one next action.

## Open items (not yet done)
- Hosting and domain; then decide HSTS include-subdomains and preload.
- PostgreSQL, backups and a tested restore.
- POPIA review of the application form, consent wording, retention and Information Officer.
- Match the quarterly CSV columns to the official SEDFA reporting template.
- Choose a repository licence.
