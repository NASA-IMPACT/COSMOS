from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

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
    filterset_fields = []

    def get_combined_queryset(self):
        """
        Returns combined data where:
        1. All spreadsheet data is included
        2. ML production data is included only if there's no spreadsheet data with matching dataset
        Records are sorted by dataset name and then data_source (ensuring spreadsheet comes before ml_production)
        """
        # Get spreadsheet data
        spreadsheet_data = EnvironmentalJusticeRow.objects.filter(
            data_source=EnvironmentalJusticeRow.DataSourceChoices.SPREADSHEET
        )

        # Get ML production data excluding datasets that exist in spreadsheet
        ml_production_data = EnvironmentalJusticeRow.objects.filter(
            data_source=EnvironmentalJusticeRow.DataSourceChoices.ML_PRODUCTION
        ).exclude(dataset__in=spreadsheet_data.values_list("dataset", flat=True))

        # Combine the querysets and sort
        return spreadsheet_data.union(ml_production_data).order_by("dataset", "data_source")

    def get_queryset(self):
        """
        Handle different data_source filter scenarios:
        - No filter: Return combined data (spreadsheet takes precedence)
        - 'combined': Same as no filter
        - specific source: Return data for that source only
        """
        data_source = self.request.query_params.get("data_source", "combined")

        # Handle the 'combined' case or no parameter case
        if not data_source or data_source == "combined":
            return self.get_combined_queryset()

        # Validate specific data source
        if data_source not in EnvironmentalJusticeRow.DataSourceChoices.values:
            valid_choices = list(EnvironmentalJusticeRow.DataSourceChoices.values) + ["combined"]
            raise ValidationError(f"Invalid data_source. Valid choices are: {', '.join(valid_choices)}")

        return super().get_queryset().filter(data_source=data_source).order_by("dataset")
