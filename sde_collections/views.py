from django.views.generic.list import ListView

from .models import Collection


class CollectionListView(ListView):
    """
    Display a list of collections in the system
    """

    model = Collection
    paginate_by = 100
    template_name = "sde_collections/collection_list.html"
    context_object_name = "collections"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
