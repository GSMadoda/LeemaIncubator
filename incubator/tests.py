import csv
import io
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Enterprise, PerformanceReport, StageChange, fy_quarter


def make(**kw):
    base = dict(name="Test Co", sector="services", province="NW", town="Mogwase", contact_name="A",
                contact_email="a@example.com", contact_phone="0", description="x")
    base.update(kw)
    return Enterprise.objects.create(**base)


class FinancialYearTests(TestCase):
    def test_april_to_march_quarters(self):
        self.assertEqual(fy_quarter(date(2026, 4, 1)), (2026, 1))
        self.assertEqual(fy_quarter(date(2026, 6, 30)), (2026, 1))
        self.assertEqual(fy_quarter(date(2026, 9, 19)), (2026, 2))
        self.assertEqual(fy_quarter(date(2026, 12, 31)), (2026, 3))
        self.assertEqual(fy_quarter(date(2027, 1, 1)), (2026, 4))
        self.assertEqual(fy_quarter(date(2027, 3, 31)), (2026, 4))


class StageTests(TestCase):
    def test_new_enterprise_is_applicant(self):
        self.assertEqual(make().stage, Enterprise.Stage.APPLICANT)

    def test_valid_path_writes_audit_log(self):
        e = make()
        for s in ["screening", "onboarded", "incubating", "graduated"]:
            e.move_to(s, reason="ok")
        self.assertEqual(e.stage, "graduated")
        self.assertEqual(StageChange.objects.filter(enterprise=e).count(), 4)

    def test_cannot_skip_stages(self):
        e = make()
        with self.assertRaises(ValidationError):
            e.move_to("incubating")
        self.assertEqual(Enterprise.objects.get(pk=e.pk).stage, "applicant")
        self.assertFalse(StageChange.objects.exists())

    def test_final_stages_are_final(self):
        e = make()
        e.move_to("declined")
        with self.assertRaises(ValidationError):
            e.move_to("screening")

    def test_audit_log_is_append_only(self):
        e = make()
        e.move_to("screening")
        entry = StageChange.objects.get()
        entry.reason = "tampered"
        with self.assertRaises(ValidationError):
            entry.save()
        with self.assertRaises(ValidationError):
            entry.delete()


class PublicApplicationTests(TestCase):
    def data(self, **kw):
        d = dict(name="New Co", sector="agro", province="NC", town="Galeshewe", contact_name="B",
                 contact_email="b@example.com", contact_phone="0123", description="Bakery",
                 employees_at_intake=2, annual_turnover_at_intake="100000", black_owned_pct=100,
                 women_owned_pct=100, youth_owned_pct=0, consent="on")
        d.update(kw)
        return d

    def test_application_creates_applicant(self):
        r = self.client.post(reverse("incubator:apply"), self.data())
        self.assertRedirects(r, reverse("incubator:applied"))
        self.assertEqual(Enterprise.objects.get().stage, "applicant")

    def test_applicant_cannot_set_own_stage(self):
        self.client.post(reverse("incubator:apply"), self.data(stage="graduated"))
        self.assertEqual(Enterprise.objects.get().stage, "applicant")

    def test_consent_required(self):
        d = self.data()
        d.pop("consent")
        self.client.post(reverse("incubator:apply"), d)
        self.assertFalse(Enterprise.objects.exists())

    def test_percentage_bounds(self):
        self.client.post(reverse("incubator:apply"), self.data(women_owned_pct=150))
        self.assertFalse(Enterprise.objects.exists())


class StaffViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("staff", password="a-long-test-password")

    def test_staff_pages_require_login(self):
        for name in ["dashboard", "enterprises", "report", "report_csv"]:
            r = self.client.get(reverse(f"incubator:{name}"))
            self.assertEqual(r.status_code, 302, name)
            self.assertIn(reverse("login"), r["Location"])

    def test_pages_render_with_demo_data(self):
        call_command("seed_demo", stdout=io.StringIO())
        self.client.force_login(self.user)
        e = Enterprise.objects.first()
        for url in [reverse("incubator:dashboard"), reverse("incubator:enterprises"),
                    reverse("incubator:enterprises") + "?stage=incubating&province=NW&q=demo",
                    reverse("incubator:report"), e.get_absolute_url(),
                    reverse("incubator:report_csv")]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_stage_change_view_records_user(self):
        self.client.force_login(self.user)
        e = make()
        self.client.post(reverse("incubator:change_stage", args=[e.pk]), {"to_stage": "screening"})
        self.assertEqual(StageChange.objects.get().changed_by, self.user)

    def test_stage_change_view_rejects_skips(self):
        self.client.force_login(self.user)
        e = make()
        self.client.post(reverse("incubator:change_stage", args=[e.pk]), {"to_stage": "graduated"})
        self.assertEqual(Enterprise.objects.get(pk=e.pk).stage, "applicant")

    def test_csv_totals_match_records(self):
        e1, e2 = make(name="A Co"), make(name="B Co")
        PerformanceReport.objects.create(enterprise=e1, fy_start_year=2026, quarter=2,
                                         turnover=Decimal("1000.50"), permanent_jobs=3, new_jobs=1)
        PerformanceReport.objects.create(enterprise=e2, fy_start_year=2026, quarter=2,
                                         turnover=Decimal("2000"), permanent_jobs=4, new_jobs=2)
        PerformanceReport.objects.create(enterprise=e2, fy_start_year=2026, quarter=1,
                                         turnover=Decimal("9999"), permanent_jobs=9, new_jobs=9)
        self.client.force_login(self.user)
        r = self.client.get(reverse("incubator:report_csv") + "?fy=2026&q=2")
        rows = list(csv.DictReader(io.StringIO(r.content.decode())))
        self.assertEqual([x["Enterprise"] for x in rows], ["A Co", "B Co"])
        self.assertEqual(sum(Decimal(x["Turnover (R)"]) for x in rows), Decimal("3000.50"))
        self.assertEqual(sum(int(x["New jobs"]) for x in rows), 3)

    def test_seed_refuses_non_empty_database(self):
        make()
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command("seed_demo", stdout=io.StringIO())


class LocaleFormatTests(TestCase):
    def test_dates_render_south_african_style(self):
        from django.template import Context, Template
        out = Template("{{ d }}").render(Context({"d": date(2026, 7, 31)}))
        self.assertEqual(out, "31 Jul 2026")
