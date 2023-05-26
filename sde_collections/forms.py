from django import forms
from .models import RequiredUrls


class RequiredUrlForm(forms.ModelForm):
    class Meta:
        model = RequiredUrls
        fields = ["url"]
