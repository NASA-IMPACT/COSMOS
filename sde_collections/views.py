from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from rest_framework import viewsets

from .models import CandidateURL, Collection, ExcludePattern, TitlePattern
from .serializers import (
    CandidateURLSerializer,
    ExcludePatternSerializer,
    TitlePatternSerializer,
)


class CollectionListView(ListView):
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


class CollectionDetailView(DetailView):
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


class CandidateURLsListView(ListView):
    """
    Display a list of collections in the system
    """

    model = CandidateURL
    template_name = "sde_collections/candidate_urls_list.html"
    context_object_name = "candidate_urls"

    def get_queryset(self):
        self.collection = Collection.objects.get(pk=self.kwargs["pk"])
        return (
            super()
            .get_queryset()
            .filter(collection=Collection.objects.get(pk=self.kwargs["pk"]))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = "candidate-url-list"
        context["title"] = self.collection
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
