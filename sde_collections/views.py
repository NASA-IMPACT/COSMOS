from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .models import CandidateURL, Collection


class CollectionListView(ListView):
    """
    Display a list of collections in the system
    """

    model = Collection
    template_name = "sde_collections/collection_list.html"
    context_object_name = "collections"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        return context


class CandidateURLsListView(ListView):
    """
    Display a list of collections in the system
    """

    model = CandidateURL
    template_name = "sde_collections/candidate_urls_list.html"
    context_object_name = "candidate_urls"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(collection=Collection.objects.get(pk=self.kwargs["pk"]))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
