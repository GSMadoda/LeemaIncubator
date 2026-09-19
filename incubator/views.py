import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ApplicationForm, StageForm
from .models import Enterprise, Intervention, PerformanceReport, fy_quarter

Stage = Enterprise.Stage


def apply(request):
    form = ApplicationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("incubator:applied")
    return render(request, "incubator/apply.html", {"form": form})


def applied(request):
    return render(request, "incubator/applied.html")


def _period(request):
    fy, q = fy_quarter(timezone.localdate())
    try:
        fy = int(request.GET.get("fy", fy))
        q = int(request.GET.get("q", q))
    except ValueError:
        pass
    return fy, max(1, min(4, q))


@login_required
def dashboard(request):
    fy, q = fy_quarter(timezone.localdate())
    active = Enterprise.objects.filter(stage__in=Enterprise.ACTIVE)
    fy_interventions = Intervention.objects.filter(
        delivered_on__gte=f"{fy}-04-01", delivered_on__lt=f"{fy + 1}-04-01")
    support = fy_interventions.aggregate(hours=Sum("hours"), cost=Sum("cost"), n=Count("id"))
    jobs = PerformanceReport.objects.filter(fy_start_year=fy).aggregate(new=Sum("new_jobs"))
    pipeline = {s: 0 for s in Stage}
    for row in Enterprise.objects.values("stage").annotate(n=Count("id")):
        pipeline[Stage(row["stage"])] = row["n"]
    context = {
        "fy": fy, "q": q,
        "active_count": active.count(),
        "pipeline": [(s.label, s.value, pipeline[s]) for s in Stage],
        "by_province": active.values("province").annotate(n=Count("id")).order_by("-n"),
        "by_tier": Enterprise.objects.exclude(readiness_tier=None)
                   .values("readiness_tier").annotate(n=Count("id")).order_by("readiness_tier"),
        "by_relationship": Enterprise.objects.values("relationship").annotate(n=Count("id")).order_by("-n"),
        "tier_labels": dict(Enterprise.Tier.choices),
        "relationship_labels": dict(Enterprise.Relationship.choices),
        "untiered": Enterprise.objects.filter(readiness_tier=None).count(),
        "support": support,
        "new_jobs": jobs["new"] or 0,
        "awaiting": Enterprise.objects.filter(stage__in=[Stage.APPLICANT, Stage.SCREENING]).order_by("applied_on")[:8],
        "overdue": [m for e in active.prefetch_related("milestones") for m in e.milestones.all() if m.overdue][:8],
        "province_labels": dict(Enterprise.Province.choices),
    }
    return render(request, "incubator/dashboard.html", context)


@login_required
def enterprise_list(request):
    qs = Enterprise.objects.select_related("cohort")
    stage, province, term = request.GET.get("stage"), request.GET.get("province"), request.GET.get("q", "").strip()
    tier, relationship = request.GET.get("tier"), request.GET.get("relationship")
    if stage:
        qs = qs.filter(stage=stage)
    if province:
        qs = qs.filter(province=province)
    if tier:
        qs = qs.filter(readiness_tier=tier)
    if relationship:
        qs = qs.filter(relationship=relationship)
    if term:
        qs = qs.filter(Q(name__icontains=term) | Q(trading_name__icontains=term) | Q(town__icontains=term))
    return render(request, "incubator/enterprise_list.html", {
        "enterprises": qs, "stages": Stage.choices, "provinces": Enterprise.Province.choices,
        "tiers": Enterprise.Tier.choices, "relationships": Enterprise.Relationship.choices,
        "sel": {"stage": stage, "province": province, "q": term,
                "tier": tier, "relationship": relationship}})


@login_required
def enterprise_detail(request, pk):
    e = get_object_or_404(Enterprise.objects.select_related("cohort"), pk=pk)
    return render(request, "incubator/enterprise_detail.html", {
        "e": e, "stage_form": StageForm(enterprise=e) if e.allowed_transitions() else None,
        "diagnostic": e.diagnostics.first(),
        "support_total": e.interventions.aggregate(hours=Sum("hours"), cost=Sum("cost")),
    })


@login_required
@require_POST
def change_stage(request, pk):
    e = get_object_or_404(Enterprise, pk=pk)
    form = StageForm(request.POST, enterprise=e)
    if form.is_valid():
        try:
            e.move_to(form.cleaned_data["to_stage"], user=request.user, reason=form.cleaned_data["reason"])
            messages.success(request, f"Moved to {e.get_stage_display()}.")
        except ValidationError as err:
            messages.error(request, err.messages[0])
    else:
        messages.error(request, "That stage change isn't allowed from the current stage.")
    return redirect(e)


def _report_rows(fy, q):
    reports = (PerformanceReport.objects.filter(fy_start_year=fy, quarter=q)
               .select_related("enterprise").order_by("enterprise__name"))
    return reports


@login_required
def quarterly_report(request):
    fy, q = _period(request)
    reports = _report_rows(fy, q)
    totals = reports.aggregate(turnover=Sum("turnover"), perm=Sum("permanent_jobs"),
                               temp=Sum("temporary_jobs"), new=Sum("new_jobs"))
    missing = Enterprise.objects.filter(stage__in=Enterprise.ACTIVE).exclude(
        reports__fy_start_year=fy, reports__quarter=q)
    return render(request, "incubator/report.html", {
        "fy": fy, "q": q, "reports": reports, "totals": totals, "missing": missing,
        "years": range(fy - 2, fy + 2)})


@login_required
def quarterly_report_csv(request):
    fy, q = _period(request)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="leema-kpi-FY{fy}-Q{q}.csv"'
    w = csv.writer(response)
    w.writerow(["Enterprise", "CIPC reg no", "Province", "Sector", "Stage", "Black-owned %",
                "Women-owned %", "Youth-owned %", "Period", "Turnover (R)", "Permanent jobs",
                "Temporary jobs", "New jobs"])
    for r in _report_rows(fy, q):
        e = r.enterprise
        w.writerow([e.name, e.registration_number, e.get_province_display(), e.get_sector_display(),
                    e.get_stage_display(), e.black_owned_pct, e.women_owned_pct, e.youth_owned_pct,
                    r.period, r.turnover, r.permanent_jobs, r.temporary_jobs, r.new_jobs])
    return response
