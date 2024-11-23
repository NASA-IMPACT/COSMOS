from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from .models import EnvironmentalJusticeRow
from .serializers import EnvironmentalJusticeRowSerializer


class EnvironmentalJusticeRowViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows environmental justice rows to be read.
    When combining spreadsheet and ml_production data, spreadsheet takes precedence
    for any matching dataset values.
    """

    queryset = EnvironmentalJusticeRow.objects.all()
    serializer_class = EnvironmentalJusticeRowSerializer
    http_method_names = ["get"]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["data_source"]

    def get_combined_queryset(self):
        """
        Returns combined data where:
        1. All spreadsheet data is included
        2. ML production data is included only if there's no spreadsheet data with matching dataset
        """
        # First, get all unique datasets that exist in spreadsheet
        spreadsheet_datasets = (
            EnvironmentalJusticeRow.objects.filter(data_source=EnvironmentalJusticeRow.DataSourceChoices.SPREADSHEET)
            .values_list("dataset", flat=True)
            .distinct()
        )

        # Build query to get:
        # 1. ALL spreadsheet records
        # 2. ML production records where dataset isn't in spreadsheet
        combined_query = Q(data_source=EnvironmentalJusticeRow.DataSourceChoices.SPREADSHEET) | Q(
            data_source=EnvironmentalJusticeRow.DataSourceChoices.ML_PRODUCTION, dataset__not_in=spreadsheet_datasets
        )

        return EnvironmentalJusticeRow.objects.filter(combined_query).order_by(
            "dataset"
        )  # Optional: orders results by dataset name

    def get_queryset(self):
        """
        Handle different data_source filter scenarios:
        - No filter: Return combined data (spreadsheet takes precedence)
        - 'combined': Same as no filter
        - specific source: Return data for that source only
        """
        data_source = self.request.query_params.get("data_source", "combined")

        # straightfoward case: return data for specific source
        if data_source in EnvironmentalJusticeRow.DataSourceChoices.values:
            return super().get_queryset().filter(data_source=data_source)

        # Handle 'combined' or no filter case
        return self.get_combined_queryset()
