"""Domain model for the Leema Incubation Hub.

South African government financial year (April-March) is used for quarterly
reporting, matching Seda/SEDFA implementation-plan periods.
"""
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

PCT = [MinValueValidator(0), MaxValueValidator(100)]


def fy_quarter(d: date) -> tuple[int, int]:
    """Return (financial-year start year, quarter 1-4) for an April-March year."""
    start = d.year if d.month >= 4 else d.year - 1
    quarter = ((d.month - 4) % 12) // 3 + 1
    return start, quarter


class Programme(models.Model):
    name = models.CharField(max_length=160)
    funder = models.CharField(max_length=120, default="SEDFA")
    fy_start_year = models.PositiveIntegerField(help_text="2026 means FY 2026/27")
    budget = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))

    class Meta:
        ordering = ["-fy_start_year", "name"]

    def __str__(self):
        return f"{self.name} (FY {self.fy_start_year}/{str(self.fy_start_year + 1)[-2:]})"


class Cohort(models.Model):
    programme = models.ForeignKey(Programme, on_delete=models.PROTECT, related_name="cohorts")
    name = models.CharField(max_length=120)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["-start_date"]

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("End date must be on or after the start date.")

    def __str__(self):
        return self.name


class Enterprise(models.Model):
    class Stage(models.TextChoices):
        APPLICANT = "applicant", "Applicant"
        SCREENING = "screening", "Screening"
        ONBOARDED = "onboarded", "Onboarded"
        INCUBATING = "incubating", "Incubating"
        GRADUATED = "graduated", "Graduated"
        EXITED = "exited", "Exited"
        DECLINED = "declined", "Declined"

    TRANSITIONS = {
        Stage.APPLICANT: [Stage.SCREENING, Stage.DECLINED],
        Stage.SCREENING: [Stage.ONBOARDED, Stage.DECLINED],
        Stage.ONBOARDED: [Stage.INCUBATING, Stage.EXITED],
        Stage.INCUBATING: [Stage.GRADUATED, Stage.EXITED],
        Stage.GRADUATED: [],
        Stage.EXITED: [],
        Stage.DECLINED: [],
    }
    ACTIVE = [Stage.ONBOARDED, Stage.INCUBATING]

    class Province(models.TextChoices):
        NW = "NW", "North West"
        GP = "GP", "Gauteng"
        NC = "NC", "Northern Cape"
        MP = "MP", "Mpumalanga"
        OTHER = "OT", "Other"
        NOT_STATED = "XX", "Not stated"

    class Sector(models.TextChoices):
        MANUFACTURING = "manufacturing", "Manufacturing"
        ELECTRONICS = "electronics", "Electronics & devices"
        AGRO = "agro", "Agro-processing"
        CONSTRUCTION = "construction", "Construction"
        ICT = "ict", "ICT & digital"
        SERVICES = "services", "Services"
        RETAIL = "retail", "Retail & trade"
        ENERGY = "energy", "Energy & automotive"
        SUPPLY = "supply", "PPE & general supply"
        SECURITY = "security", "Security"
        HOSPITALITY = "hospitality", "Food & hospitality"
        ELECTRICAL = "electrical", "Electrical"
        OTHER = "other", "Other"

    class Relationship(models.TextChoices):
        """How the enterprise stands with LEEMA, as the SEDFA portfolio report classifies it."""
        INCUBATEE = "incubatee", "LEEMA Incubatee"
        RESELLER = "reseller", "LEEMA Reseller"
        STRATEGIC = "strategic", "LEEMA Strategic Partner"
        TECH_APPLICANT = "tech_applicant", "Technology Incubation applicant"
        EXPLORING = "exploring", "Exploring a relationship"

    class Tier(models.IntegerChoices):
        """Readiness for incubation interventions. Not creditworthiness, and revisited after verification."""
        GROWTH_READY = 1, "Tier 1 - Growth-ready"
        STRUCTURING = 2, "Tier 2 - Structuring"
        FOUNDATION = 3, "Tier 3 - Foundation"

    class Material(models.TextChoices):
        """State of the enterprise's own profile and supporting material at intake."""
        CURRENT = "current", "Current and complete"
        UPDATING = "updating", "Needs updating"
        IMPROVEMENT = "improvement", "Needs major improvement"
        REGISTRATION = "registration", "Registration documents only"
        NONE = "none", "None"
        NOT_CAPTURED = "not_captured", "Not captured"

    name = models.CharField("Registered name", max_length=200)
    trading_name = models.CharField(max_length=200, blank=True)
    registration_number = models.CharField("CIPC registration no.", max_length=20, blank=True)
    sector = models.CharField(max_length=20, choices=Sector.choices)
    province = models.CharField(max_length=2, choices=Province.choices)
    town = models.CharField("Town or township", max_length=120)
    # Personal information under POPIA. Left empty in any data committed to a public
    # repository; captured through the admin on a private deployment.
    contact_name = models.CharField(max_length=120, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    description = models.TextField("What the business does")
    relationship = models.CharField(
        max_length=16, choices=Relationship.choices, default=Relationship.EXPLORING,
        help_text="Standing with LEEMA, as reported to SEDFA.")
    readiness_tier = models.PositiveSmallIntegerField(
        choices=Tier.choices, null=True, blank=True,
        help_text="Desk-review readiness tier. Guides the type and sequence of support.")
    material_readiness = models.CharField(
        "Material at intake", max_length=14, choices=Material.choices,
        default=Material.NOT_CAPTURED)
    products_services = models.TextField(blank=True)
    customers_market = models.TextField("Customers and market", blank=True)
    competitive_edge = models.TextField(blank=True)
    goals_challenge = models.TextField("Goals and stated challenge", blank=True)
    target_1_3_years = models.TextField("One to three year target", blank=True)
    support_sought = models.TextField(blank=True)
    jobs_target = models.PositiveIntegerField(
        null=True, blank=True, help_text="Jobs the enterprise projects, where it quantified one. A projection, never counted as a job created.")
    bbbee_level = models.PositiveSmallIntegerField(
        "B-BBEE level", null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(8)])
    # Like the intake measurements: empty means not captured, which is not the same as zero.
    black_owned_pct = models.PositiveSmallIntegerField("Black-owned %", null=True, blank=True, validators=PCT)
    women_owned_pct = models.PositiveSmallIntegerField("Women-owned %", null=True, blank=True, validators=PCT)
    youth_owned_pct = models.PositiveSmallIntegerField("Youth-owned %", null=True, blank=True, validators=PCT)

    @property
    def ownership_captured(self):
        return any(p is not None for p in (self.black_owned_pct, self.women_owned_pct, self.youth_owned_pct))
    employees_at_intake = models.PositiveIntegerField(
        null=True, blank=True, help_text="Left empty where intake did not capture it. Empty is not zero.")
    annual_turnover_at_intake = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        help_text="Left empty where intake did not capture it. Empty is not zero.")
    learnable_enrolled = models.BooleanField("Enrolled on Learnable", default=False)
    stage = models.CharField(max_length=12, choices=Stage.choices, default=Stage.APPLICANT, editable=False)
    cohort = models.ForeignKey(Cohort, null=True, blank=True, on_delete=models.SET_NULL, related_name="enterprises")
    applied_on = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.trading_name or self.name

    def get_absolute_url(self):
        return reverse("incubator:enterprise", args=[self.pk])

    def allowed_transitions(self):
        return self.TRANSITIONS[self.Stage(self.stage)]

    @transaction.atomic
    def move_to(self, new_stage, user=None, reason=""):
        """The only sanctioned way to change stage; always writes the audit log."""
        new_stage = self.Stage(new_stage)
        if new_stage not in self.allowed_transitions():
            raise ValidationError(f"Cannot move from {self.get_stage_display()} to {new_stage.label}.")
        StageChange.objects.create(enterprise=self, from_stage=self.stage, to_stage=new_stage,
                                   changed_by=user, reason=reason)
        self.stage = new_stage
        self.save(update_fields=["stage"])

    def latest_report(self):
        return self.reports.order_by("-fy_start_year", "-quarter").first()


class StageChange(models.Model):
    """Append-only audit trail. Corrections are new entries, never edits."""
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="stage_changes")
    from_stage = models.CharField(max_length=12, choices=Enterprise.Stage.choices)
    to_stage = models.CharField(max_length=12, choices=Enterprise.Stage.choices)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-changed_at"]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Stage history is append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Stage history is append-only.")


class Diagnostic(models.Model):
    DIMENSIONS = ["finance", "marketing", "operations", "compliance", "people", "digital"]
    SCORE = [MinValueValidator(1), MaxValueValidator(5)]

    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="diagnostics")
    assessed_on = models.DateField(default=timezone.localdate)
    assessor = models.CharField(max_length=120)
    finance = models.PositiveSmallIntegerField(validators=SCORE)
    marketing = models.PositiveSmallIntegerField(validators=SCORE)
    operations = models.PositiveSmallIntegerField(validators=SCORE)
    compliance = models.PositiveSmallIntegerField(validators=SCORE)
    people = models.PositiveSmallIntegerField(validators=SCORE)
    digital = models.PositiveSmallIntegerField(validators=SCORE)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-assessed_on"]

    @property
    def overall(self):
        return round(sum(getattr(self, d) for d in self.DIMENSIONS) / len(self.DIMENSIONS), 1)

    def __str__(self):
        return f"{self.enterprise} diagnostic {self.assessed_on}"


class Intervention(models.Model):
    class Kind(models.TextChoices):
        MENTORING = "mentoring", "Mentoring"
        TRAINING = "training", "Training"
        BDS = "bds", "Business development service"
        MARKET = "market", "Market access"
        FINANCE = "finance", "Finance linkage"
        COMPLIANCE = "compliance", "Compliance support"
        FACILITY = "facility", "Equipment or workspace"

    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="interventions")
    kind = models.CharField(max_length=12, choices=Kind.choices)
    delivered_on = models.DateField(default=timezone.localdate)
    provider = models.CharField(max_length=160)
    hours = models.DecimalField(max_digits=6, decimal_places=1, default=Decimal("0"))
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    summary = models.TextField()

    class Meta:
        ordering = ["-delivered_on"]

    def __str__(self):
        return f"{self.get_kind_display()} for {self.enterprise} on {self.delivered_on}"


class Milestone(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"
        MISSED = "missed", "Missed"

    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="milestones")
    title = models.CharField(max_length=200)
    due_on = models.DateField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PLANNED)
    completed_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["due_on"]

    def clean(self):
        if self.status == self.Status.DONE and not self.completed_on:
            raise ValidationError("Add the completion date for a finished milestone.")

    @property
    def overdue(self):
        return self.status in (self.Status.PLANNED, self.Status.IN_PROGRESS) and self.due_on < timezone.localdate()

    def __str__(self):
        return self.title


class PerformanceReport(models.Model):
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="reports")
    fy_start_year = models.PositiveIntegerField(help_text="2026 means FY 2026/27")
    quarter = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)],
                                               help_text="Q1 = Apr-Jun")
    turnover = models.DecimalField("Turnover for the quarter", max_digits=14, decimal_places=2)
    permanent_jobs = models.PositiveIntegerField(default=0)
    temporary_jobs = models.PositiveIntegerField(default=0)
    new_jobs = models.PositiveIntegerField("Jobs created this quarter", default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-fy_start_year", "-quarter"]
        constraints = [models.UniqueConstraint(fields=["enterprise", "fy_start_year", "quarter"],
                                               name="one_report_per_enterprise_quarter")]

    @property
    def period(self):
        return f"FY{self.fy_start_year}/{str(self.fy_start_year + 1)[-2:]} Q{self.quarter}"

    def __str__(self):
        return f"{self.enterprise} {self.period}"


class ComplianceCheck(models.Model):
    """One verification item for one enterprise: the compliance register.

    Workstream 1 of the 90-day support plan verifies CIPC, SARS, CSD, B-BBEE, bank
    details, POPIA consent and baseline figures across the whole portfolio. Until a
    check is Verified, anything downstream of it -- a funding submission, a tender
    pack -- is resting on a self-reported claim.
    """

    class Kind(models.TextChoices):
        CIPC = "cipc", "CIPC registration"
        TAX = "tax", "SARS tax compliance"
        CSD = "csd", "Central Supplier Database"
        BBBEE = "bbbee", "B-BBEE credentials"
        BANK = "bank", "Bank confirmation"
        POPIA = "popia", "POPIA consent"
        BASELINE = "baseline", "Baseline jobs and turnover"

    class Status(models.TextChoices):
        OUTSTANDING = "outstanding", "Outstanding"
        REQUESTED = "requested", "Requested"
        VERIFIED = "verified", "Verified"
        FAILED = "failed", "Not compliant"
        NOT_APPLICABLE = "na", "Not applicable"

    #: Column heading for the register matrix, where the full label is too wide to repeat.
    SHORT = {Kind.CIPC: "CIPC", Kind.TAX: "SARS", Kind.CSD: "CSD", Kind.BBBEE: "B-BBEE",
             Kind.BANK: "Bank", Kind.POPIA: "POPIA", Kind.BASELINE: "Baseline"}

    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="compliance")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OUTSTANDING)
    verified_on = models.DateField(null=True, blank=True)
    reference = models.CharField(max_length=120, blank=True, help_text="Certificate or reference number.")
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["enterprise__name", "kind"]
        constraints = [models.UniqueConstraint(fields=["enterprise", "kind"], name="one_check_per_kind")]

    def clean(self):
        if self.status == self.Status.VERIFIED and not self.verified_on:
            raise ValidationError("A verified check must record the date it was verified.")

    @property
    def settled(self):
        """Nothing further is owed on this check."""
        return self.status in (self.Status.VERIFIED, self.Status.NOT_APPLICABLE)

    def __str__(self):
        return f"{self.enterprise} {self.get_kind_display()}"


class Linkage(models.Model):
    """A commercial introduction brokered between enterprises in the portfolio.

    The report commits these to SEDFA on arm's-length, market-related terms, so that
    resulting revenue can be tracked. A linkage is real when it is Agreed or Trading;
    Proposed means LEEMA intends it, nothing more.
    """

    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        INTRODUCED = "introduced", "Introduced"
        AGREED = "agreed", "Agreement signed"
        TRADING = "trading", "Trading"
        LAPSED = "lapsed", "Lapsed"

    title = models.CharField(max_length=160)
    providers = models.ManyToManyField(Enterprise, related_name="linkages_supplying", blank=True,
                                       help_text="Enterprises supplying into this linkage.")
    recipients = models.ManyToManyField(Enterprise, related_name="linkages_receiving", blank=True,
                                        help_text="Enterprises buying or receiving.")
    rationale = models.TextField()
    expected_output = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PROPOSED)
    opened_on = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Workstream(models.Model):
    """One workstream of the 90-day support plan, October to December 2026."""

    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        RUNNING = "running", "Running"
        DONE = "done", "Complete"
        BLOCKED = "blocked", "Blocked"

    number = models.PositiveSmallIntegerField(unique=True)
    title = models.CharField(max_length=160)
    detail = models.TextField(blank=True)
    enterprises = models.ManyToManyField(Enterprise, related_name="workstreams", blank=True)
    covers_whole_portfolio = models.BooleanField(
        default=False, help_text="Tick where the plan says 'all', rather than listing each enterprise.")
    start_week = models.PositiveSmallIntegerField()
    end_week = models.PositiveSmallIntegerField()
    deliverable = models.TextField("Deliverable or KPI")
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PLANNED)

    class Meta:
        ordering = ["number"]

    def clean(self):
        if self.end_week < self.start_week:
            raise ValidationError("A workstream cannot end before it starts.")

    @property
    def weeks(self):
        return f"Week {self.start_week}" if self.start_week == self.end_week \
            else f"Weeks {self.start_week}–{self.end_week}"

    def __str__(self):
        return f"{self.number}. {self.title}"
