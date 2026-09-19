from django import forms

from .models import Enterprise


class ApplicationForm(forms.ModelForm):
    consent = forms.BooleanField(
        label="I agree that Leema may store and use this information to assess my application.",
        required=True)

    class Meta:
        model = Enterprise
        fields = ["name", "trading_name", "registration_number", "sector", "province", "town",
                  "contact_name", "contact_email", "contact_phone", "description",
                  "employees_at_intake", "annual_turnover_at_intake",
                  "black_owned_pct", "women_owned_pct", "youth_owned_pct"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}
        labels = {"annual_turnover_at_intake": "Turnover in the last 12 months (R)",
                  "employees_at_intake": "People employed today"}


class StageForm(forms.Form):
    to_stage = forms.ChoiceField(label="Move to")
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False)

    def __init__(self, *args, enterprise, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["to_stage"].choices = [(s.value, s.label) for s in enterprise.allowed_transitions()]
