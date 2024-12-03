import factory
from factory.django import DjangoModelFactory

from environmental_justice.models import EnvironmentalJusticeRow


class EnvironmentalJusticeRowFactory(DjangoModelFactory):
    class Meta:
        model = EnvironmentalJusticeRow

    dataset = factory.Sequence(lambda n: f"dataset_{n}")
    description = factory.Faker("sentence")
    description_simplified = factory.Faker("sentence")
    indicators = factory.Faker("sentence")
    intended_use = factory.Faker("sentence")
    latency = factory.Faker("word")
    limitations = factory.Faker("sentence")
    project = factory.Faker("word")
    source_link = factory.Faker("url")
    strengths = factory.Faker("sentence")
    format = factory.Faker("file_extension")
    geographic_coverage = factory.Faker("country")
    data_visualization = factory.Faker("sentence")
    spatial_resolution = factory.Faker("word")
    temporal_extent = factory.Faker("date")
    temporal_resolution = factory.Faker("word")
    sde_link = factory.Faker("url")
    data_source = EnvironmentalJusticeRow.DataSourceChoices.SPREADSHEET
