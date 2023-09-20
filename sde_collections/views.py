import os
import re
import json
import subprocess


from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView
from django.views.generic.list import ListView
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse

from Document_Classifier_inference.main import batch_predicts

from .forms import CollectionGithubIssueForm, RequiredUrlForm
from .models.candidate_url import CandidateURL
from .models.collection import Collection, RequiredUrls
from .models.collection_choice_fields import CurationStatusChoices
from .models.pattern import DocumentTypePattern, ExcludePattern, TitlePattern
from .serializers import (
    CandidateURLBulkCreateSerializer,
    CandidateURLSerializer,
    CollectionSerializer,
    DocumentTypePatternSerializer,
    ExcludePatternSerializer,
    TitlePatternSerializer,
)
from .tasks import push_to_github_task

User = get_user_model()


def model_inference(request):
    if request.method == "POST":
        collection_id = request.POST.get("collection_id")
        candidate_urls = CandidateURL.objects.filter(
            collection_id=Collection.objects.get(pk=collection_id),
        ).exclude(document_type__in=[1, 2, 3, 4, 5, 6])
        print("Candidate_url",candidate_urls)
        document_type_list=[type(candidate_url.document_type) for candidate_url in candidate_urls]
        # These list of urls are to be inferred
        to_infer_url_list = [candidate_url.url for candidate_url in candidate_urls]
        if to_infer_url_list:
            collection_id = candidate_urls[0].collection_id
            prediction,pdf_lists = batch_predicts(
                "Document_Classifier_inference/config.json", to_infer_url_list
            )
            # Update document_type for corresponding URLs
            for candidate_url in candidate_urls:
                new_document_type = prediction.get(candidate_url.url)
                if new_document_type is not None:
                    candidate_url.document_type = new_document_type
                    candidate_url.inferenced_by = "model"
                    candidate_url.save() #Updating the changes in candidateurl table
                    # Create a new DocumentTypePattern entry for each URL and its document_type
                    DocumentTypePattern.objects.create(
                        collection_id=candidate_url.collection_id,
                        match_pattern=candidate_url.url.replace("https://",""),
                        match_pattern_type=DocumentTypePattern.MatchPatternTypeChoices.INDIVIDUAL_URL,
                        document_type=new_document_type,
                    )  #Adding the new record in documenttypepattern table
                if candidate_url.url in pdf_lists:  #flagging created for url with pdf response
                    candidate_url.is_pdf=True
                    candidate_url.save()
        return HttpResponse(status=204)


class CollectionListView(LoginRequiredMixin, ListView):
    """
    Display a list of collections in the system
    """

    model = Collection
    template_name = "sde_collections/collection_list.html"
    context_object_name = "collections"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(delete=False)
            .annotate(num_candidate_urls=models.Count("candidate_urls"))
            .order_by("-num_candidate_urls")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = "collections"
        context["curators"] = User.objects.filter(groups__name="Curators")
        context["curation_status_choices"] = CurationStatusChoices

        return context


class CollectionDetailView(LoginRequiredMixin, DetailView):
    """
    Display a list of collections in the system
    """

    model = Collection
    template_name = "sde_collections/collection_detail.html"
    context_object_name = "collection"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        collection = self.get_object()

        form = RequiredUrlForm(request.POST)
        github_form = CollectionGithubIssueForm(request.POST)

        if "github_issue_link" in request.POST and github_form.is_valid():
            github_issue_link = github_form.cleaned_data["github_issue_link"]
            issue_number = re.search(r"/issues/(\d+)/?$", github_issue_link)
            if issue_number:
                github_issue_number = int(issue_number.group(1))
                collection.github_issue_number = github_issue_number
                collection.save()
            else:
                github_form.add_error(
                    "github_issue_link", "Invalid GitHub issue link format"
                )
                return self.render_to_response(
                    self.get_context_data(form=form, github_form=github_form)
                )
            return redirect("sde_collections:detail", pk=collection.pk)

        else:
            if "claim_button" in request.POST:
                user = self.request.user
                collection.curation_status = CurationStatusChoices.BEING_CURATED
                collection.curated_by = user
                collection.curation_started = timezone.now()
                collection.save()
            elif form.is_valid():
                required_url = form.save(commit=False)
                required_url.collection = collection
                required_url.save()
            else:
                # If the form is not valid, render the detail view with the form and errors.
                return self.render_to_response(self.get_context_data(form=form))
            return redirect("sde_collections:detail", pk=collection.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "form" not in context:
            context["form"] = RequiredUrlForm()
            context["github_form"] = CollectionGithubIssueForm(
                initial={"github_issue_link": self.get_object().github_issue_link}
            )
        context["required_urls"] = RequiredUrls.objects.filter(
            collection=self.get_object()
        )
        context["segment"] = "collection-detail"
        return context


class RequiredUrlsDeleteView(LoginRequiredMixin, DeleteView):
    model = RequiredUrls

    def get_success_url(self, *args, **kwargs):
        return reverse(
            "sde_collections:detail", kwargs={"pk": self.object.collection.pk}
        )


class CandidateURLsListView(LoginRequiredMixin, ListView):
    """
    Display a list of collections in the system
    """

    model = CandidateURL
    template_name = "sde_collections/candidate_urls_list.html"
    context_object_name = "candidate_urls"
    # paginate_by = 1000

    def _filter_by_is_exluded(self, queryset, is_excluded):
        if is_excluded == "true":
            queryset = queryset.filter(appliedexclude__isnull=False)
        elif is_excluded == "false":
            queryset = queryset.exclude(appliedexclude__isnull=False)
        return queryset

    def get_queryset(self):
        self.collection = Collection.objects.get(pk=self.kwargs["pk"])
        queryset = super().get_queryset().filter(collection=self.collection)

        # Filter based on exclusion status
        is_excluded = self.request.GET.get("is_excluded")
        if is_excluded:
            queryset = self._filter_by_is_exluded(queryset, is_excluded)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = "candidate-url-list"
        context["collection"] = self.collection
        context["regex_exclude_patterns"] = self.collection.excludepattern.filter(
            match_pattern_type=2
        )  # 2=regex patterns
        context["title_patterns"] = self.collection.titlepattern.all()
        return context


class CollectionFilterMixin:
    def get_queryset(self):
        if not self.request.method == "GET":
            return super().get_queryset()

        try:
            collection_id = self.request.GET.get("collection_id")
            collection = Collection.objects.get(pk=collection_id)
        except Collection.DoesNotExist:
            # just return an empty list
            return super().get_queryset().filter(collection__isnull=True)
        return super().get_queryset().filter(collection=collection)


class CandidateURLViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = CandidateURL.objects.all()
    serializer_class = CandidateURLSerializer

    def _filter_by_is_excluded(self, queryset, is_excluded):
        if is_excluded == "false":
            queryset = queryset.filter(excluded=False)
        elif is_excluded == "true":
            queryset = queryset.exclude(excluded=False)
        return queryset

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.method == "GET":
            # Filter based on exclusion status
            is_excluded = self.request.GET.get("is_excluded")
            if is_excluded:
                queryset = self._filter_by_is_excluded(queryset, is_excluded)
        return queryset.order_by("url")


class CandidateURLBulkCreateView(generics.ListCreateAPIView):
    queryset = CandidateURL.objects.all()
    serializer_class = CandidateURLBulkCreateSerializer

    def perform_create(self, serializer, collection_id=None):
        for validated_data in serializer.validated_data:
            validated_data["collection_id"] = collection_id
        super().perform_create(serializer)

    def create(self, request, *args, **kwargs):
        config_folder = kwargs.get("config_folder")
        collection = Collection.objects.get(config_folder=config_folder)
        collection.candidate_urls.all().delete()

        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, collection_id=collection.pk)

        collection.apply_all_patterns()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ExcludePatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = ExcludePattern.objects.all()
    serializer_class = ExcludePatternSerializer

    def get_queryset(self):
        return super().get_queryset().order_by("match_pattern")

    def create(self, request, *args, **kwargs):
        match_pattern = request.POST.get("match_pattern")
        collection_id = request.POST.get("collection")
        try:
            ExcludePattern.objects.get(
                collection_id=Collection.objects.get(id=collection_id),
                match_pattern=match_pattern,
            ).delete()
            return Response(status=status.HTTP_200_OK)
        except ExcludePattern.DoesNotExist:
            return super().create(request, *args, **kwargs)


class TitlePatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = TitlePattern.objects.all()
    serializer_class = TitlePatternSerializer

    def get_queryset(self):
        return super().get_queryset().order_by("match_pattern")


class DocumentTypePatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = DocumentTypePattern.objects.all()
    serializer_class = DocumentTypePatternSerializer

    def get_queryset(self):
        return super().get_queryset().order_by("match_pattern")

    def create(self, request, *args, **kwargs):
        document_type = request.POST.get("document_type")
        inferencer = request.POST.get("inferencer")
        collection_id = request.POST.get("collection")
        match_pattern = request.POST.get("match_pattern")
        candidate_url = CandidateURL.objects.get(
            collection_id=Collection.objects.get(id=collection_id),
            url="https://" + match_pattern,
        )
        if not int(document_type) == 0:  # 0=none
            candidate_url.inferenced_by = inferencer
            candidate_url.save()
            return super().create(request, *args, **kwargs)
        try:
            DocumentTypePattern.objects.get(
                collection_id=Collection.objects.get(id=collection_id),
                match_pattern=match_pattern,
                match_pattern_type=DocumentTypePattern.MatchPatternTypeChoices.INDIVIDUAL_URL,
            ).delete()
            return super().create(request, *args, **kwargs)
        except DocumentTypePattern.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer


class PushToGithubView(APIView):
    def post(self, request):
        collection_ids = request.POST.getlist("collection_ids[]", [])
        if len(collection_ids) == 0:
            return Response(
                "collection_ids can't be empty.", status=status.HTTP_400_BAD_REQUEST
            )

        push_to_github_task.delay(collection_ids)

        return Response(
            {"Success": "Started pushing collections to github"},
            status=status.HTTP_200_OK,
        )
