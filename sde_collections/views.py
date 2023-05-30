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

from .forms import RequiredUrlForm
from .models import (
    CandidateURL,
    Collection,
    DocumentTypePattern,
    ExcludePattern,
    RequiredUrls,
    TitlePattern,
)
from .serializers import (
    CandidateURLBulkCreateSerializer,
    CandidateURLSerializer,
    CollectionSerializer,
    DocumentTypePatternSerializer,
    ExcludePatternSerializer,
    TitlePatternSerializer,
)

User = get_user_model()


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
            .annotate(num_candidate_urls=models.Count("candidate_urls"))
            .order_by("-num_candidate_urls")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = "collections"
        context["curators"] = User.objects.filter(groups__name="Curators")
        context["curation_status_choices"] = Collection.CurationStatusChoices

        return context


class CollectionDetailView(LoginRequiredMixin, DetailView):
    """
    Display a list of collections in the system
    """

    model = Collection
    template_name = "sde_collections/collection_detail.html"
    context_object_name = "collection"

    def post(self, request, *args, **kwargs):
        collection = self.get_object()
        form = RequiredUrlForm(request.POST)
        if "claim_button" in request.POST:
            user = self.request.user
            collection.curation_status = Collection.CurationStatusChoices.BEING_CURATED
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


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
