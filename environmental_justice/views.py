from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from .models import EnvironmentalJusticeRow
from .serializers import EnvironmentalJusticeRowSerializer


class EnvironmentalJusticeRowViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows environmental justice rows to be read.
    """

    queryset = EnvironmentalJusticeRow.objects.all()
    serializer_class = EnvironmentalJusticeRowSerializer
    http_method_names = ["get"]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["destination_server"]

    def get_queryset(self):
        """
        if no destination_server is provided, default to PROD
        """
        queryset = super().get_queryset()
        if not self.request.query_params.get("destination_server"):
            queryset = queryset.filter(destination_server=EnvironmentalJusticeRow.DestinationServerChoices.PROD)
        return queryset
