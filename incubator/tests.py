import csv
import io
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import (ComplianceCheck, Enterprise, Linkage, PerformanceReport,
                     StageChange, Workstream, fy_quarter)


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


class PortfolioSeedTests(TestCase):
    """The SEDFA portfolio as loaded, checked against the source report's own figures."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_portfolio", verbosity=0)

    def tally(self, field):
        result = {}
        for enterprise in Enterprise.objects.all():
            result[getattr(enterprise, field)] = result.get(getattr(enterprise, field), 0) + 1
        return result

    def test_sixteen_enterprises_in_two_cohorts(self):
        self.assertEqual(Enterprise.objects.count(), 16)
        self.assertEqual(Enterprise.objects.values("cohort").distinct().count(), 2)

    def test_readiness_tiers_match_the_report_summary(self):
        # Section 2 chart: Tier 1 five, Tier 2 seven, Tier 3 four. The only summary
        # figure in the report that agrees with its own enterprise table.
        self.assertEqual(self.tally("readiness_tier"), {1: 5, 2: 7, 3: 4})

    def test_relationships_follow_the_enterprise_table_not_the_summary_chart(self):
        # The report's chart says five resellers and five exploring; its enterprise
        # table gives four and six. The table is the primary record, so it wins.
        # docs/PORTFOLIO_DATA.md records the disagreement.
        self.assertEqual(
            self.tally("relationship"),
            {"incubatee": 4, "reseller": 4, "strategic": 1, "tech_applicant": 1, "exploring": 6})

    def test_provinces_follow_the_enterprise_table_not_the_summary_chart(self):
        # The report's chart says North West eight and Gauteng six, and its five
        # province figures sum to seventeen across sixteen enterprises.
        self.assertEqual(self.tally("province"), {"NW": 6, "GP": 7, "NC": 1, "MP": 1, "XX": 1})

    def test_no_personal_information_is_seeded(self):
        """This repository is public. A contact detail in seed data would be published."""
        for enterprise in Enterprise.objects.all():
            self.assertEqual(enterprise.contact_name, "", f"{enterprise} carries a contact name")
            self.assertEqual(enterprise.contact_email, "", f"{enterprise} carries a contact email")
            self.assertEqual(enterprise.contact_phone, "", f"{enterprise} carries a contact phone")

    def test_uncaptured_intake_measurements_are_absent_not_zero(self):
        # Section 6 note 5: the intake form captures neither employees nor turnover.
        # Storing zero would assert a measurement that was never taken.
        for enterprise in Enterprise.objects.all():
            self.assertIsNone(enterprise.employees_at_intake)
            self.assertIsNone(enterprise.annual_turnover_at_intake)

    def test_ownership_demographics_are_absent_not_zero(self):
        # Section 6 note 5 again: intake captures no ownership demographics.
        for enterprise in Enterprise.objects.all():
            self.assertFalse(enterprise.ownership_captured, f"{enterprise} asserts ownership percentages")

    def test_only_quantified_jobs_targets_are_recorded(self):
        targets = {e.name: e.jobs_target for e in Enterprise.objects.exclude(jobs_target=None)}
        self.assertEqual(targets, {
            "Reve P Catering": 10,
            "Far Out Excellent Trading and Projects": 5,
            "Oageng Creative Agency": 5,
        })

    def test_opening_stages_are_written_through_the_audit_log(self):
        incubatee = Enterprise.objects.get(name="Reve P Catering")
        self.assertEqual(incubatee.stage, Enterprise.Stage.INCUBATING)
        self.assertEqual(incubatee.stage_changes.count(), 3)
        exploring = Enterprise.objects.get(name="Sugar Bears")
        self.assertEqual(exploring.stage, Enterprise.Stage.APPLICANT)
        self.assertEqual(exploring.stage_changes.count(), 0)

    def test_refuses_to_run_twice(self):
        with self.assertRaises(Exception):
            call_command("seed_portfolio", verbosity=0)


class PortfolioFilterTests(TestCase):
    def setUp(self):
        call_command("seed_portfolio", verbosity=0)
        get_user_model().objects.create_user("staff", password="pw-for-tests-only")
        self.client.login(username="staff", password="pw-for-tests-only")

    def test_filters_by_readiness_tier(self):
        response = self.client.get(reverse("incubator:enterprises"), {"tier": "1"})
        self.assertEqual(len(response.context["enterprises"]), 5)

    def test_filters_by_relationship(self):
        response = self.client.get(reverse("incubator:enterprises"), {"relationship": "incubatee"})
        self.assertEqual(len(response.context["enterprises"]), 4)

    def test_detail_page_says_contacts_are_withheld(self):
        enterprise = Enterprise.objects.get(name="Sugar Bears")
        response = self.client.get(enterprise.get_absolute_url())
        self.assertContains(response, "POPIA")
        self.assertContains(response, "Tier 3")


class OperationsTests(TestCase):
    """The delivery side: the compliance register, the linkages and the 90-day plan."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_portfolio", verbosity=0)

    def setUp(self):
        get_user_model().objects.create_user("staff2", password="pw-for-tests-only")
        self.client.login(username="staff2", password="pw-for-tests-only")

    def test_every_enterprise_opens_a_full_compliance_register(self):
        kinds = len(ComplianceCheck.Kind)
        self.assertEqual(ComplianceCheck.objects.count(), 16 * kinds)
        for enterprise in Enterprise.objects.all():
            self.assertEqual(enterprise.compliance.count(), kinds)

    def test_nothing_starts_verified(self):
        """The register opens at the true position: nothing has been checked yet."""
        self.assertEqual(ComplianceCheck.objects.exclude(
            status=ComplianceCheck.Status.OUTSTANDING).count(), 0)

    def test_a_verified_check_must_carry_its_date(self):
        check = ComplianceCheck.objects.first()
        check.status = ComplianceCheck.Status.VERIFIED
        with self.assertRaises(ValidationError):
            check.full_clean()
        check.verified_on = date(2026, 10, 7)
        check.full_clean()

    def test_one_check_of_each_kind_per_enterprise(self):
        existing = ComplianceCheck.objects.first()
        with self.assertRaises(Exception):
            ComplianceCheck.objects.create(enterprise=existing.enterprise, kind=existing.kind)

    def test_register_counts_settled_work(self):
        check = ComplianceCheck.objects.first()
        check.status, check.verified_on = ComplianceCheck.Status.VERIFIED, date(2026, 10, 7)
        check.save()
        other = ComplianceCheck.objects.exclude(pk=check.pk).first()
        other.status = ComplianceCheck.Status.NOT_APPLICABLE
        other.save()
        response = self.client.get(reverse("incubator:compliance"))
        self.assertEqual(response.context["settled"], 2)
        self.assertEqual(response.context["total"], 16 * len(ComplianceCheck.Kind))

    def test_the_five_report_linkages_are_loaded_with_both_sides(self):
        self.assertEqual(Linkage.objects.count(), 5)
        ppe = Linkage.objects.get(title__startswith="Women's PPE")
        self.assertEqual([e.name for e in ppe.providers.all()], ["Kaborati Holdings"])
        self.assertEqual(ppe.recipients.count(), 3)
        self.assertEqual(ppe.status, Linkage.Status.PROPOSED)

    def test_the_eight_workstreams_are_loaded(self):
        self.assertEqual(Workstream.objects.count(), 8)
        audit = Workstream.objects.get(number=1)
        self.assertTrue(audit.covers_whole_portfolio)
        self.assertEqual(audit.weeks, "Weeks 1–4")
        self.assertEqual(Workstream.objects.get(number=8).weeks, "Week 12")

    def test_a_workstream_cannot_end_before_it_starts(self):
        workstream = Workstream(number=99, title="x", start_week=6, end_week=2, deliverable="x")
        with self.assertRaises(ValidationError):
            workstream.full_clean()

    def test_programme_page_lists_the_plan_and_the_linkages(self):
        response = self.client.get(reverse("incubator:programme"))
        self.assertEqual(len(response.context["workstreams"]), 8)
        self.assertEqual(len(response.context["linkages"]), 5)
        self.assertContains(response, "Verification and compliance audit")
        self.assertContains(response, "Catering and produce supply")

    def test_every_page_in_the_navigation_answers(self):
        for name in ["dashboard", "enterprises", "compliance", "programme", "report"]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(f"incubator:{name}")).status_code, 200)
