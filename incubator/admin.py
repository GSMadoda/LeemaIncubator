from django.contrib import admin

from .models import (Cohort, ComplianceCheck, Diagnostic, Enterprise, Intervention,
                     Linkage, Milestone, PerformanceReport, Programme, StageChange,
                     Workstream)

admin.site.site_header = "Leema Incubation Hub"
admin.site.site_title = "Leema Incubation Hub"
admin.site.index_title = "Records"


class StageChangeInline(admin.TabularInline):
    model = StageChange
    extra = 0
    can_delete = False
    readonly_fields = ["from_stage", "to_stage", "changed_at", "changed_by", "reason"]

    def has_add_permission(self, request, obj=None):
        return False


class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ["name", "funder", "fy_start_year", "budget"]


@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    list_display = ["name", "programme", "start_date", "end_date"]
    list_filter = ["programme"]


@admin.register(Enterprise)
class EnterpriseAdmin(admin.ModelAdmin):
    list_display = ["name", "relationship", "readiness_tier", "sector", "province", "stage", "cohort", "applied_on"]
    list_filter = ["relationship", "readiness_tier", "material_readiness", "stage", "province", "sector",
                   "cohort", "learnable_enrolled"]
    search_fields = ["name", "trading_name", "registration_number", "contact_name", "town"]
    readonly_fields = ["stage", "created_at"]
    inlines = [MilestoneInline, StageChangeInline]


@admin.register(StageChange)
class StageChangeAdmin(admin.ModelAdmin):
    list_display = ["enterprise", "from_stage", "to_stage", "changed_at", "changed_by"]
    list_filter = ["to_stage"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Diagnostic)
class DiagnosticAdmin(admin.ModelAdmin):
    list_display = ["enterprise", "assessed_on", "assessor", "overall"]
    autocomplete_fields = ["enterprise"]


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = ["enterprise", "kind", "delivered_on", "provider", "hours", "cost"]
    list_filter = ["kind", "delivered_on"]
    autocomplete_fields = ["enterprise"]
    date_hierarchy = "delivered_on"


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ["title", "enterprise", "due_on", "status"]
    list_filter = ["status"]
    autocomplete_fields = ["enterprise"]


@admin.register(PerformanceReport)
class PerformanceReportAdmin(admin.ModelAdmin):
    list_display = ["enterprise", "fy_start_year", "quarter", "turnover", "permanent_jobs", "new_jobs"]
    list_filter = ["fy_start_year", "quarter"]
    autocomplete_fields = ["enterprise"]


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ["enterprise", "kind", "status", "verified_on", "reference"]
    list_filter = ["status", "kind", "enterprise__readiness_tier"]
    list_editable = ["status", "verified_on"]
    search_fields = ["enterprise__name", "reference"]
    list_select_related = ["enterprise"]


@admin.register(Linkage)
class LinkageAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "opened_on"]
    list_filter = ["status"]
    filter_horizontal = ["providers", "recipients"]


@admin.register(Workstream)
class WorkstreamAdmin(admin.ModelAdmin):
    list_display = ["number", "title", "weeks", "status", "covers_whole_portfolio"]
    list_filter = ["status"]
    filter_horizontal = ["enterprises"]
