from rest_framework import viewsets

from .models import EnvironmentalJusticeRow
from .serializers import EnvironmentalJusticeRowSerializer


class EnvironmentalJusticeRowViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows environmental justice rows to be read.
    """

    queryset = EnvironmentalJusticeRow.objects.all()
    serializer_class = EnvironmentalJusticeRowSerializer
    http_method_names = [
        "get",
    ]
