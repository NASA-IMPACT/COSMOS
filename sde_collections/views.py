from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CandidateURL, Collection, ExcludePattern, TitlePattern
from .serializers import (
    CandidateURLSerializer,
    ExcludePatternSerializer,
    TitlePatternSerializer,
)


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
        return context


class CollectionDetailView(LoginRequiredMixin, DetailView):
    """
    Display a list of collections in the system
    """

    model = Collection
    template_name = "sde_collections/collection_detail.html"
    context_object_name = "collection"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = "collection-detail"
        return context


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
        context["regex_exclude_patterns"] = self.collection.exclude_patterns.filter(
            pattern_type=2
        )  # 2=regex patterns
        context["title_patterns"] = self.collection.title_patterns.all()
        return context


class CandidateURLViewSet(viewsets.ModelViewSet):
    queryset = CandidateURL.objects.all()
    serializer_class = CandidateURLSerializer

    def get_queryset(self):
        if not self.request.method == "GET":
            return super().get_queryset()

        try:
            collection_id = self.request.GET.get("collection_id")
            collection = Collection.objects.get(pk=collection_id)
        except Collection.DoesNotExist:
            # just return an empty list
            return super().get_queryset().filter(collection__isnull=True)
        return super().get_queryset().filter(collection=collection).order_by("url")


class ExcludePatternViewSet(viewsets.ModelViewSet):
    queryset = ExcludePattern.objects.all()
    serializer_class = ExcludePatternSerializer


class TitlePatternViewSet(viewsets.ModelViewSet):
    queryset = TitlePattern.objects.all()
    serializer_class = TitlePatternSerializer


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()

    @action(detail=True)
    def candidate_urls(self, request, pk=None):
        collection = self.get_object()
        queryset = collection.candidate_urls.all()

        # Filter based on exclusion status
        exclude = request.query_params.get("is_excluded", None)
        if exclude:
            if exclude.lower() == "true":
                queryset = queryset.filter(appliedexclude__isnull=False)
            elif exclude.lower() == "false":
                queryset = queryset.exclude(appliedexclude__isnull=False)

        serializer = CandidateURLSerializer(queryset, many=True)
        return Response(serializer.data)
