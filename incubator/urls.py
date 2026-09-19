from django.urls import path

from . import views

app_name = "incubator"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("apply/", views.apply, name="apply"),
    path("apply/received/", views.applied, name="applied"),
    path("enterprises/", views.enterprise_list, name="enterprises"),
    path("enterprises/<int:pk>/", views.enterprise_detail, name="enterprise"),
    path("enterprises/<int:pk>/stage/", views.change_stage, name="change_stage"),
    path("compliance/", views.compliance_register, name="compliance"),
    path("programme/", views.programme, name="programme"),
    path("reports/", views.quarterly_report, name="report"),
    path("reports/export.csv", views.quarterly_report_csv, name="report_csv"),
]
