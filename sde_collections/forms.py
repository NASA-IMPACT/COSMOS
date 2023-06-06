from django import forms

from .models import Collection, RequiredUrls


class RequiredUrlForm(forms.ModelForm):
    class Meta:
        model = RequiredUrls
        fields = ["url"]


class CollectionGithubIssueForm(forms.ModelForm):
    github_issue_link = forms.URLField()

    class Meta:
        model = Collection
        fields = [
            "github_issue_link",
        ]
