# Leema Incubation Hub

Enterprise-support management for **Leema Township Incubator** (LEEMA Incubation NPC, Bodirelo Industrial
Park, Mogwase). It tracks enterprises from application to graduation and produces quarterly figures for
Seda/SEDFA reporting.

## What it does

- **Public application form** at `/apply/`, with consent capture. New applicants land in the pipeline.
- **Pipeline**: Applicant → Screening → Onboarded → Incubating → Graduated (or Declined/Exited). Stages can
  only move along allowed paths, and every move is written to an append-only history with who made it.
- **Enterprise record**: registration, ownership profile, intake baseline, cohort, Learnable enrolment.
- **Diagnostics**: 1–5 scores across finance, marketing, operations, compliance, people and digital.
- **Support delivered**: mentoring, training, BDS, market access, finance linkage, compliance, workspace,
  with hours and cost.
- **Milestones** with overdue tracking.
- **Quarterly performance**: turnover and jobs per enterprise per quarter (April–March financial year),
  a report page, and CSV export.
- **Overview**: enterprises in support, support hours and spend, jobs created, applications waiting,
  provincial spread, overdue milestones.
- **Records admin** at `/admin/` for data entry, built on Django's admin.

## Run it locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --require-hashes -r requirements.txt
export DJANGO_DEBUG=1
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo     # optional: fictional demo data, empty database only
python manage.py runserver
```

Open http://127.0.0.1:8000 and sign in.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Required in production. The app will not start without it. | none |
| `DJANGO_DEBUG` | `1` for local development only | `0` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names | `localhost,127.0.0.1` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | e.g. `https://hub.leemaincubation.co.za` | none |
| `HUB_ORG_NAME` | Name shown in the interface | `Leema Township Incubator` |
| `HUB_DB_PATH` | SQLite file location | `db.sqlite3` |

## Tests

```bash
DJANGO_DEBUG=1 python manage.py test incubator
```

The GitHub Actions workflow runs the tests, a missing-migrations check and Django's production security
audit on every push.

## Before production

- Choose hosting and a domain, then decide on `SECURE_HSTS_INCLUDE_SUBDOMAINS` and `SECURE_HSTS_PRELOAD`.
- Move to PostgreSQL for multi-user production use and set up backups, then test a restore.
- Complete a POPIA review: the form collects personal information; confirm the consent wording, retention
  period and Information Officer with the NPC.
- Confirm the quarterly CSV columns against the official SEDFA reporting template.
- Choose a licence for the repository.
