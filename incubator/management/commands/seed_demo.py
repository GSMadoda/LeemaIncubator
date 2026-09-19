"""Load clearly fictional demo data. Never run against a live database."""
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from incubator.models import (Cohort, Diagnostic, Enterprise, Intervention, Milestone,
                              PerformanceReport, Programme, fy_quarter)

DEMO = [
    ("Demo Mogwase Metalworks", "manufacturing", "NW", "Mogwase", "incubating"),
    ("Demo Tlhabane Solar Installers", "energy", "NW", "Tlhabane", "incubating"),
    ("Demo Soshanguve Electronics Repair", "electronics", "GP", "Soshanguve", "onboarded"),
    ("Demo Galeshewe Bakery", "agro", "NC", "Galeshewe", "incubating"),
    ("Demo Ledig Brick Works", "construction", "NW", "Ledig", "screening"),
    ("Demo Boitekong Web Studio", "ict", "NW", "Boitekong", "applicant"),
]
PATH = {"applicant": [], "screening": ["screening"], "onboarded": ["screening", "onboarded"],
        "incubating": ["screening", "onboarded", "incubating"]}


class Command(BaseCommand):
    help = "Load fictional demo data (all names start with 'Demo')."

    def handle(self, *args, **opts):
        if Enterprise.objects.exists():
            raise CommandError("Database already has enterprises; demo data is only for an empty database.")
        today = date.today()
        fy, q = fy_quarter(today)
        prog = Programme.objects.create(name="Township Incubation Programme", fy_start_year=fy,
                                        budget=Decimal("1400000"))
        cohort = Cohort.objects.create(programme=prog, name=f"Cohort {fy}A", start_date=date(fy, 4, 1),
                                       end_date=date(fy + 1, 3, 31))
        for i, (name, sector, prov, town, stage) in enumerate(DEMO):
            e = Enterprise.objects.create(
                name=name, sector=sector, province=prov, town=town, contact_name="Demo Contact",
                contact_email=f"demo{i}@example.com", contact_phone="0000000000",
                description="Fictional enterprise for demonstration.", black_owned_pct=100,
                women_owned_pct=[0, 51, 100][i % 3], youth_owned_pct=[100, 0, 50][i % 3],
                employees_at_intake=2 + i, annual_turnover_at_intake=Decimal(150000 * (i + 1)),
                cohort=cohort if stage in ("onboarded", "incubating") else None,
                applied_on=today - timedelta(days=90 - i * 10))
            for s in PATH[stage]:
                e.move_to(s, reason="Demo data")
            if stage in ("onboarded", "incubating"):
                Diagnostic.objects.create(enterprise=e, assessor="Demo Assessor", finance=2 + i % 3,
                                          marketing=2, operations=3, compliance=1 + i % 4, people=3, digital=2)
                Intervention.objects.create(enterprise=e, kind="mentoring", provider="Demo Mentor",
                                            hours=Decimal("6"), cost=Decimal("4500"),
                                            summary="Cash-flow planning sessions.")
                Intervention.objects.create(enterprise=e, kind="training", provider="Learnable",
                                            hours=Decimal("12"), cost=Decimal("2000"),
                                            summary="Business basics course.")
                Milestone.objects.create(enterprise=e, title="Tax clearance obtained",
                                         due_on=today + timedelta(days=30 - i * 20))
            if stage == "incubating":
                PerformanceReport.objects.create(enterprise=e, fy_start_year=fy, quarter=q,
                                                 turnover=Decimal(60000 * (i + 1)), permanent_jobs=3 + i,
                                                 temporary_jobs=1, new_jobs=1)
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(DEMO)} fictional enterprises."))
