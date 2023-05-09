from django.contrib.auth.mixins import LoginRequiredMixin
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

    def get_queryset(self):
        self.collection = Collection.objects.get(pk=self.kwargs["pk"])
        self.hide_excluded = self.request.GET.get("is_excluded")
        queryset = super().get_queryset().filter(collection=self.collection)
        if self.hide_excluded == "true":
            queryset = queryset.filter(appliedexclude__isnull=False)
        elif self.hide_excluded == "false":
            queryset = queryset.exclude(appliedexclude__isnull=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = "candidate-url-list"
        context["collection"] = self.collection
        return context


class CandidateURLViewSet(viewsets.ModelViewSet):
    queryset = CandidateURL.objects.all()
    serializer_class = CandidateURLSerializer


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
