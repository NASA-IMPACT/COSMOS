# docker-compose -f local.yml run --rm django pytest scripts/ej/test_cmr_processing.py
import json

import pytest
from cmr_processing import CmrDataset


# Helper function to load test data
def load_test_data(file_path="scripts/ej/cmr_example.json"):
    with open(file_path) as f:
        return json.load(f)[0]  # First dataset from the example


class TestCmrDatasetIntegration:
    """Integration tests using real CMR data example"""

    @pytest.fixture
    def cmr_dataset(self):
        return CmrDataset(load_test_data())

    def test_full_dataset_processing(self, cmr_dataset):
        """Test that all properties can be extracted from real data without errors"""
        # Test all property accessors
        assert cmr_dataset.dataset_name == "2000 Pilot Environmental Sustainability Index (ESI)"
        assert cmr_dataset.description.startswith("The 2000 Pilot Environmental Sustainability Index")
        assert cmr_dataset.limitations == "None"
        assert cmr_dataset.format == "PDF"
        assert cmr_dataset.temporal_extent == ""  # No SingleDateTimes in example
        assert cmr_dataset.intended_use == "Path A"  # ProcessingLevel is 4
        assert cmr_dataset.source_link == "https://doi.org/10.7927/H4NK3BZJ"
        assert "Long temporal extent" in cmr_dataset.strengths
        assert "No recent data available" in cmr_dataset.weaknesses
        assert cmr_dataset.latency == "Not Provided"
        assert cmr_dataset.geographic_coverage == ""
        assert (
            "https://sedac.ciesin.columbia.edu/downloads/maps/esi/esi-pilot-environmental-sustainability-index-2000/sedac-logo.jpg"  # noqa
            in cmr_dataset.data_visualization
        )
        assert cmr_dataset.temporal_resolution == ""
        assert cmr_dataset.spatial_resolution == ""
        assert "ESI" in cmr_dataset.projects


class TestTemporalProcessing:
    """Unit tests for temporal information processing"""

    def basic_temporal_data(self):
        return {
            "meta": {},
            "umm": {
                "TemporalExtents": [
                    {
                        "RangeDateTimes": [
                            {
                                "BeginningDateTime": "2020-01-01T00:00:00.000Z",
                                "EndingDateTime": "2020-12-31T23:59:59.999Z",
                            }
                        ],
                        "TemporalResolution": {"Unit": "Hour", "Value": 24},
                    }
                ]
            },
        }

    def test_parse_datetime_with_milliseconds(self):
        dataset = CmrDataset({})
        dt = dataset._parse_datetime("2020-01-01T00:00:00.123Z")
        assert dt.year == 2020
        assert dt.microsecond == 123000

    def test_parse_datetime_without_milliseconds(self):
        dataset = CmrDataset({})
        dt = dataset._parse_datetime("2020-01-01T00:00:00Z")
        assert dt.year == 2020
        assert dt.microsecond == 0

    def test_temporal_info_with_invalid_dates(self):
        data = {
            "umm": {
                "TemporalExtents": [
                    {"RangeDateTimes": [{"BeginningDateTime": "invalid", "EndingDateTime": "2020-12-31T23:59:59.999Z"}]}
                ]
            }
        }
        dataset = CmrDataset(data)
        assert dataset.temporal_info.total_duration == 0
        assert dataset.temporal_info.latest_end_date is None

    def test_temporal_resolution_parsing(self):
        dataset = CmrDataset(self.basic_temporal_data())
        assert dataset.temporal_resolution == "24 Hour"

    def test_temporal_duration_calculation(self):
        dataset = CmrDataset(self.basic_temporal_data())
        assert dataset.temporal_info.total_duration == 365  # Full year

    def test_multiple_time_ranges(self):
        data = {
            "meta": {},
            "umm": {
                "TemporalExtents": [
                    {
                        "RangeDateTimes": [
                            {
                                "BeginningDateTime": "2020-01-01T00:00:00.000Z",
                                "EndingDateTime": "2020-06-30T23:59:59.999Z",
                            },
                            {
                                "BeginningDateTime": "2020-07-01T00:00:00.000Z",
                                "EndingDateTime": "2021-01-01T00:00:00.000Z",
                            },
                        ]
                    }
                ]
            },
        }
        dataset = CmrDataset(data)
        assert dataset.temporal_info.total_duration == 365

    def test_single_date_times(self):
        data = {
            "meta": {},
            "umm": {"TemporalExtents": [{"SingleDateTimes": ["2020-01-01T00:00:00.000Z", "2020-06-01T00:00:00.000Z"]}]},
        }
        dataset = CmrDataset(data)
        assert len(dataset.temporal_info.single_date_times) == 2
        assert dataset.temporal_extent == "2020-01-01T00:00:00.000Z, 2020-06-01T00:00:00.000Z"

    def test_missing_temporal_data(self):
        dataset = CmrDataset({"meta": {}, "umm": {}})
        assert dataset.temporal_info.total_duration == 0
        assert dataset.temporal_info.latest_end_date is None
        assert dataset.temporal_resolution == ""


class TestSpatialProcessing:
    """Unit tests for spatial information processing"""

    def test_global_coverage_detection(self):
        data = {
            "umm": {
                "SpatialExtent": {
                    "HorizontalSpatialDomain": {
                        "Geometry": {
                            "BoundingRectangles": [
                                {
                                    "NorthBoundingCoordinate": 90,
                                    "SouthBoundingCoordinate": -90,
                                    "WestBoundingCoordinate": -180,
                                    "EastBoundingCoordinate": 180,
                                }
                            ]
                        }
                    }
                }
            }
        }
        dataset = CmrDataset(data)
        assert dataset.geographic_coverage == "Global"

    def test_non_global_coverage(self):
        data = {
            "umm": {
                "SpatialExtent": {
                    "HorizontalSpatialDomain": {
                        "Geometry": {
                            "BoundingRectangles": [
                                {
                                    "NorthBoundingCoordinate": 45,
                                    "SouthBoundingCoordinate": -45,
                                    "WestBoundingCoordinate": -90,
                                    "EastBoundingCoordinate": 90,
                                }
                            ]
                        }
                    }
                }
            }
        }
        dataset = CmrDataset(data)
        assert dataset.geographic_coverage == ""

    def test_spatial_resolution_varies(self):
        """Test spatial resolution when it varies."""
        data = {
            "umm": {
                "SpatialExtent": {
                    "HorizontalSpatialDomain": {
                        "ResolutionAndCoordinateSystem": {"HorizontalDataResolution": {"VariesResolution": "Varies"}}
                    }
                }
            }
        }
        dataset = CmrDataset(data)
        assert dataset.spatial_resolution == "Varies"

    def test_spatial_resolution_gridded_range(self):
        """Test spatial resolution with gridded range resolutions."""
        data = {
            "umm": {
                "SpatialExtent": {
                    "HorizontalSpatialDomain": {
                        "ResolutionAndCoordinateSystem": {
                            "HorizontalDataResolution": {
                                "GriddedRangeResolutions": [
                                    {
                                        "MinimumXDimension": 5.0,
                                        "MinimumYDimension": 5.0,
                                        "MaximumXDimension": 50.0,
                                        "MaximumYDimension": 40.0,
                                        "Unit": "Kilometers",
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
        dataset = CmrDataset(data)
        assert dataset.spatial_resolution == "50.0 kilometers"

    def test_spatial_resolution_gridded(self):
        """Test spatial resolution with gridded resolutions."""
        data = {
            "umm": {
                "SpatialExtent": {
                    "HorizontalSpatialDomain": {
                        "ResolutionAndCoordinateSystem": {
                            "HorizontalDataResolution": {
                                "GriddedResolutions": [{"XDimension": 30.0, "YDimension": 30.0, "Unit": "Meters"}]
                            }
                        }
                    }
                }
            }
        }
        dataset = CmrDataset(data)
        assert dataset.spatial_resolution == "30.0 meters"

    def test_spatial_resolution_generic(self):
        """Test spatial resolution with generic resolutions."""
        data = {
            "umm": {
                "SpatialExtent": {
                    "HorizontalSpatialDomain": {
                        "ResolutionAndCoordinateSystem": {
                            "HorizontalDataResolution": {
                                "GenericResolutions": [{"XDimension": 10.0, "YDimension": 10.0, "Unit": "Kilometers"}]
                            }
                        }
                    }
                }
            }
        }
        dataset = CmrDataset(data)
        assert dataset.spatial_resolution == "10.0 kilometers"

    def test_spatial_resolution_missing(self):
        """Test spatial resolution when resolution data is missing."""
        data = {"umm": {"SpatialExtent": {"HorizontalSpatialDomain": {"ResolutionAndCoordinateSystem": {}}}}}
        dataset = CmrDataset(data)
        assert dataset.spatial_resolution == ""

    def test_spatial_resolution_different_dimensions(self):
        """Test spatial resolution when X and Y dimensions differ."""
        data = {
            "umm": {
                "SpatialExtent": {
                    "HorizontalSpatialDomain": {
                        "ResolutionAndCoordinateSystem": {
                            "HorizontalDataResolution": {
                                "GriddedResolutions": [{"XDimension": 30.0, "YDimension": 40.0, "Unit": "Meters"}]
                            }
                        }
                    }
                }
            }
        }
        dataset = CmrDataset(data)
        assert dataset.spatial_resolution == "40.0 meters"

    def test_spatial_resolution_incomplete_data(self):
        """Test spatial resolution with incomplete resolution data."""
        data = {
            "umm": {
                "SpatialExtent": {
                    "HorizontalSpatialDomain": {
                        "ResolutionAndCoordinateSystem": {
                            "HorizontalDataResolution": {
                                "GriddedResolutions": [
                                    {
                                        "XDimension": 30.0,
                                        # Missing YDimension
                                        "Unit": "Meters",
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
        dataset = CmrDataset(data)
        assert dataset.spatial_resolution == ""


class TestDownloadProcessing:
    """Unit tests for download information processing"""

    def test_direct_download_detection(self):
        data = {
            "umm": {
                "RelatedUrls": [
                    {
                        "URLContentType": "DistributionURL",
                        "Type": "GET DATA",
                        "Subtype": "DIRECT DOWNLOAD",
                        "URL": "http://example.com/data",
                    }
                ]
            }
        }
        dataset = CmrDataset(data)
        assert "Direct data download available" in dataset.strengths

    def test_visualization_urls(self):
        data = {
            "umm": {
                "RelatedUrls": [
                    {"URLContentType": "VisualizationURL", "URL": "http://example.com/viz1"},
                    {"URLContentType": "VisualizationURL", "URL": "http://example.com/viz2"},
                ]
            }
        }
        dataset = CmrDataset(data)
        assert "http://example.com/viz1" in dataset.data_visualization
        assert "http://example.com/viz2" in dataset.data_visualization

    def test_format_extraction_single(self):
        data = {
            "umm": {
                "ArchiveAndDistributionInformation": {
                    "FileDistributionInformation": [{"Format": "GeoTIFF", "Fees": "0"}]
                }
            }
        }
        dataset = CmrDataset(data)
        assert dataset.format == "GeoTIFF"

    def test_format_extraction_multiple(self):
        data = {
            "umm": {
                "ArchiveAndDistributionInformation": {
                    "FileDistributionInformation": [
                        {"Format": "Excel", "Fees": "0"},
                        {"Format": "PDF", "Fees": "0"},
                        {"Format": "PNG", "Fees": "0"},
                    ]
                }
            }
        }
        dataset = CmrDataset(data)
        assert dataset.format == "Excel; PDF; PNG"

    def test_format_extraction_empty(self):
        data = {"umm": {"ArchiveAndDistributionInformation": {"FileDistributionInformation": []}}}
        dataset = CmrDataset(data)
        assert dataset.format == ""

    def test_format_extraction_missing_info(self):
        data = {"umm": {"ArchiveAndDistributionInformation": {}}}
        dataset = CmrDataset(data)
        assert dataset.format == ""

    def test_format_extraction_no_archive_info(self):
        data = {"umm": {}}
        dataset = CmrDataset(data)
        assert dataset.format == ""


class TestProcessingLevelInfo:
    """Unit tests for processing level information"""

    def test_intended_use_exploration(self):
        data = {"umm": {"ProcessingLevel": {"Id": "4"}, "CollectionDataType": "SCIENCE_QUALITY"}}
        dataset = CmrDataset(data)
        assert dataset.intended_use == "Path A"

    def test_intended_use_basic_analysis(self):
        data = {
            "umm": {
                "ProcessingLevel": {"Id": "2"},
                "CollectionDataType": "SCIENCE_QUALITY",
                "DataCenters": [{"ShortName": "SEDAC"}],
            }
        }
        dataset = CmrDataset(data)
        assert dataset.intended_use == "Path B"

    def test_intended_use_advanced_analysis(self):
        # Added this test to cover Path C case
        data = {
            "umm": {
                "ProcessingLevel": {"Id": "2"},
                "CollectionDataType": "SCIENCE_QUALITY",
                "DataCenters": [{"ShortName": "OTHER"}],
            }
        }
        dataset = CmrDataset(data)
        assert dataset.intended_use == "Path C"

    def test_latency_mapping(self):
        data = {"umm": {"CollectionDataType": "NEAR_REAL_TIME"}}
        dataset = CmrDataset(data)
        assert dataset.latency == "1-3 Hours"


class TestPropertiesGeneration:
    """Unit tests for strengths and weaknesses generation"""

    def test_empty_properties(self):
        dataset = CmrDataset({"meta": {}, "umm": {}})
        assert dataset.strengths == ""
        assert dataset.weaknesses == ""

    def test_multiple_strengths(self):
        data = {
            "umm": {
                "CollectionProgress": "ACTIVE",
                "CollectionDataType": "NEAR_REAL_TIME",
                "RelatedUrls": [
                    {"URLContentType": "DistributionURL", "Type": "GET DATA", "Subtype": "DIRECT DOWNLOAD"}
                ],
            }
        }
        dataset = CmrDataset(data)
        strengths = dataset.strengths.split("; ")
        assert len(strengths) == 3
        assert "Data collection is ongoing" in strengths
        assert "Near real-time data is available" in strengths
        assert "Direct data download available" in strengths


class TestUrlProcessing:
    """Unit tests for URL-related functionality"""

    def test_sde_link_generation(self):
        data = {"meta": {"concept-id": "C179001887-SEDAC"}}
        dataset = CmrDataset(data)
        assert "sciencediscoveryengine.nasa.gov" in dataset.sde_link
        assert "C179001887-SEDAC" in dataset.sde_link

    def test_source_link_generation(self):
        data = {"umm": {"DOI": {"Authority": "https://doi.org/", "DOI": "10.1234/test"}}}
        dataset = CmrDataset(data)
        assert dataset.source_link == "https://doi.org/10.1234/test"

    def test_missing_doi_info(self):
        dataset = CmrDataset({"umm": {"DOI": {}}})
        assert dataset.source_link == ""


class TestProjectProcessing:
    """Unit tests for project information processing"""

    def test_multiple_projects(self):
        data = {"umm": {"Projects": [{"ShortName": "Project1"}, {"ShortName": "Project2"}]}}
        dataset = CmrDataset(data)
        assert dataset.projects == "Project1; Project2"

    def test_missing_project_shortname(self):
        data = {"umm": {"Projects": [{"LongName": "Project1"}, {"ShortName": "Project2"}]}}
        dataset = CmrDataset(data)
        assert dataset.projects == "Project2"

    def test_no_projects(self):
        dataset = CmrDataset({"umm": {}})
        assert dataset.projects == ""


class TestStrengthsWeaknesses:
    """Unit tests for strengths and weaknesses generation"""

    def test_recent_data_strength(self):
        data = {
            "umm": {
                "TemporalExtents": [
                    {
                        "RangeDateTimes": [
                            {
                                "BeginningDateTime": "2023-01-01T00:00:00.000Z",
                                "EndingDateTime": "2024-01-01T00:00:00.000Z",
                            }
                        ]
                    }
                ]
            }
        }
        dataset = CmrDataset(data)
        assert "Recent data is available" in dataset.strengths

    def test_weaknesses_combination(self):
        data = {
            "umm": {
                "TemporalExtents": [
                    {
                        "RangeDateTimes": [
                            {
                                "BeginningDateTime": "2020-01-01T00:00:00.000Z",
                                "EndingDateTime": "2020-02-01T00:00:00.000Z",
                            }
                        ]
                    }
                ],
                "RelatedUrls": [{"URLContentType": "DistributionURL", "Type": "GET DATA"}],
            }
        }
        dataset = CmrDataset(data)
        weaknesses = dataset.weaknesses.split("; ")
        assert "Limited temporal extent" in weaknesses
        assert "Direct data download not available" in weaknesses


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_empty_dataset(self):
        dataset = CmrDataset({})
        assert dataset.dataset_name == ""
        assert dataset.description == ""
        assert dataset.limitations == ""
        assert dataset.strengths == ""
        assert dataset.weaknesses == ""

    def test_malformed_dates(self):
        data = {
            "umm": {
                "TemporalExtents": [
                    {
                        "RangeDateTimes": [
                            {"BeginningDateTime": "not-a-date", "EndingDateTime": "2020-01-01T00:00:00.000Z"}
                        ]
                    }
                ]
            }
        }
        dataset = CmrDataset(data)
        assert dataset.temporal_info.total_duration == 0


if __name__ == "__main__":
    pytest.main([__file__])
