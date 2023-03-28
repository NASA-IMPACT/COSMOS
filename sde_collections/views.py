from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .models import Collection


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
        context["candidate_url_tree"] = self.object.candidate_url_tree()
        return context
