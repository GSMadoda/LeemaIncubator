# Portfolio data: source, scope and known disagreements

## Source

**Full Portfolio Report — Combined SMME cohort: profiles, readiness assessment and support plan.**
Leema Township Incubation NPC to the Small Enterprise Development Finance Agency (SEDFA),
under the SEDFA 2026/27 FY Implementation Plan approved 17 April 2026.
Report date 16 September 2026, as at 15 September 2026.
Cohorts: 27 August – 2 September 2026 (9 enterprises) and 9 – 15 September 2026 (7 enterprises).

`incubator/management/commands/seed_portfolio.py` loads it. Run it on an empty database:

```bash
python manage.py seed_portfolio
```

The report's own data basis: *"Self-reported intake submissions; desk review by LEEMA;
verification pending."* No site visits, document checks or financial reviews had been carried
out. Everything loaded here inherits that standing — it is what enterprises said about
themselves, not what anyone has verified.

## What is deliberately not loaded

The report is classified **"Confidential – contains personal information (POPIA)"**. This
repository is public, so anything committed to it is published and cannot be recalled. Two
categories are therefore absent:

- **Contact person, telephone number and email address** for all 16 enterprises. The model
  keeps the fields; the seed leaves them empty. Capture them through the admin on a private
  deployment. `PortfolioSeedTests.test_no_personal_information_is_seeded` fails if any
  reappear in seed data.
- **The per-enterprise "Gaps and risks" assessment.** Publishing "cash flow is the core
  operating constraint" beside a named business can cost it the contract it is trying to win.
  This follows the rule the public website already applies to the same cohort.

**Employees and turnover at intake are empty, not zero.** Section 6 note 5 of the report
records that the intake form captures neither. Empty means not captured; zero would assert a
measurement nobody took.

## The scheme

The report assesses on two axes, which the Hub keeps separate from its own pipeline stage.

| Axis | Field | Values |
|---|---|---|
| Standing with LEEMA | `relationship` | Incubatee · Reseller · Strategic Partner · Technology Incubation applicant · Exploring |
| Readiness for intervention | `readiness_tier` | Tier 1 Growth-ready · Tier 2 Structuring · Tier 3 Foundation |
| Material at intake | `material_readiness` | Current and complete · Needs updating · Needs major improvement · Registration only · None · Not captured |

Tiers describe readiness for incubation interventions, **not creditworthiness**, and the
report states they will be revisited after verification.

**Pipeline stage is inferred, not reported.** The report does not state a pipeline stage. The
seed opens each enterprise at: incubatee → Incubating; reseller and strategic partner →
Onboarded; technology applicant and exploring → Applicant. Stages are set through
`Enterprise.move_to()`, so the audit log records how each one got there and says the opening
stage came from this report.

## Known disagreements in the source

The report's summary charts disagree with its own enterprise table in three places. **The
per-enterprise table and profiles are treated as the primary record; the summary charts are
not followed.** These are recorded rather than corrected, and are for LEEMA to reconcile — the
same treatment the public website gives the earlier cohort's summary.

| Dimension | Summary chart says | Enterprise table gives | Loaded |
|---|---|---|---|
| Province | North West 8, Gauteng 6, Northern Cape 1, Mpumalanga 1, not stated 1 — **17 across 16 enterprises** | North West 6, Gauteng 7, Northern Cape 1, Mpumalanga 1, not stated 1 | The table |
| Relationship | Reseller 5, Exploring 5 | Reseller 4, Exploring 6 | The table |
| Material readiness | Current 5, updating 3, major improvement 3, registration only 3, none 1, not captured 1 | Current 6, updating 4, registration only 2, major improvement 2, none 1, not captured 1 | The profiles |

On the third row: the summary names its five current-material enterprises (Lomatlhola, MIDC,
Thakaramo, Lokissa, Oageng) but Kaborati's own profile also lists a current company profile,
catalogue and brochure, so the profiles give six.

Readiness tiers are the one summary figure that agrees with the table: 5 / 7 / 4.

`PortfolioSeedTests` asserts each of these tallies, so a future edit that quietly switches to
the summary figures fails the suite.

## Data-integrity items from the report (Section 6)

Carried here because they qualify what the data means, not as defects of this loader.

1. **Sector misclassification.** Kaborati selected ICT but manufactures PPE; Olacis selected
   Construction and Food but supplies consumables. Loaded under the business described, with
   the intake selection noted in the description.
2. **Incomplete location.** Rata Batho gave none — province `Not stated`. Kaborati gave a
   province only.
3. **Regulatory exposure.** Rata Batho's subscription TV-box model needs content licences and
   device type-approval evidence before any funding recommendation.
4. **Contact name differs from email name** for Sugar Bears. Not loaded here in any case.
5. **Intake form gaps.** No CIPC number, years trading, employees, turnover, tax/CSD/B-BBEE
   status or ownership demographics for any enterprise. These are the first items the 90-day
   plan verifies.

Two enterprise pairs also share contact details in the source (TM Leasure Homes with Moela
Energies; Level 98 with Kaborati). Not loaded, but relevant to verification.
