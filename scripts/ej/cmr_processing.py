import urllib.parse
from datetime import datetime
from typing import NamedTuple


class TemporalInfo(NamedTuple):
    """Container for processed temporal information."""

    latest_end_date: datetime | None
    total_duration: int
    resolution: str
    resolution_unit: str
    single_date_times: list[str]


class SpatialInfo(NamedTuple):
    """Container for processed spatial information."""

    is_global: bool
    resolution: str
    bounding_rectangles: list[dict]


class DownloadInfo(NamedTuple):
    """Container for processed download information."""

    has_distribution: bool
    has_direct_download: bool
    visualization_urls: list[str]
    format: str


class ProcessingInfo(NamedTuple):
    """Container for processing level information."""

    level: str
    collection_type: str
    data_centers: list[str]


class CmrDataset:
    """Comprehensive processor for CMR dataset information."""

    def __init__(self, dataset: dict):
        self.dataset = dataset
        self.meta = dataset.get("meta", {})
        self.umm = dataset.get("umm", {})
        self.today = datetime.now()

        # Process all information once during initialization
        self.temporal_info = self._process_temporal_extents()
        self.spatial_info = self._process_spatial_info()
        self.download_info = self._process_download_info()
        self.processing_info = self._process_processing_info()

    @staticmethod
    def _parse_datetime(date_str: str) -> datetime:
        """Parse CMR datetime string to datetime object."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            # Some dates might not have milliseconds
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

    def _check_temporal_range(self, range_datetime: dict) -> tuple[datetime, datetime]:
        """Extract begin and end dates from a range datetime entry."""
        begin_date = self._parse_datetime(range_datetime["BeginningDateTime"])
        end_date = self._parse_datetime(range_datetime["EndingDateTime"])
        return begin_date, end_date

    def _process_temporal_extents(self) -> TemporalInfo:
        """Process all temporal information."""
        temporal_extents = self.umm.get("TemporalExtents", [])
        latest_end_date = None
        total_duration = 0
        single_date_times = []

        for extent in temporal_extents:
            single_date_times.extend(extent.get("SingleDateTimes", []))
            range_datetimes = extent.get("RangeDateTimes", [])

            for range_dt in range_datetimes:
                try:
                    begin_date, end_date = self._check_temporal_range(range_dt)
                    if latest_end_date is None or end_date > latest_end_date:
                        latest_end_date = end_date
                    total_duration += (end_date - begin_date).days
                except (KeyError, ValueError):
                    continue

        # Fix: Extract Value and Unit correctly from the TemporalResolution dictionary
        temporal_resolution_dict = temporal_extents[0].get("TemporalResolution", {}) if temporal_extents else {}
        resolution_value = temporal_resolution_dict.get("Value", "")
        resolution_unit = temporal_resolution_dict.get("Unit", "")

        return TemporalInfo(
            latest_end_date=latest_end_date,
            total_duration=total_duration,
            resolution=str(resolution_value),  # Convert to string in case it's a number
            resolution_unit=resolution_unit,
            single_date_times=single_date_times,
        )

    def _process_spatial_info(self) -> SpatialInfo:
        """Process all spatial information."""
        spatial_extent = self.umm.get("SpatialExtent", {})
        horizontal_domain = spatial_extent.get("HorizontalSpatialDomain", {})
        geometry = horizontal_domain.get("Geometry", {})
        rectangles = geometry.get("BoundingRectangles", [])

        is_global = any(
            abs(rect.get("NorthBoundingCoordinate", 0)) >= 85
            and abs(rect.get("SouthBoundingCoordinate", 0)) >= 85
            and abs(rect.get("WestBoundingCoordinate", 0)) >= 175
            and abs(rect.get("EastBoundingCoordinate", 0)) >= 175
            for rect in rectangles
        )

        resolution = self._extract_spatial_resolution(horizontal_domain)

        return SpatialInfo(is_global, resolution, rectangles)

    def _extract_spatial_resolution(self, horizontal_domain: dict) -> str:
        """
        Extract and format spatial resolution from horizontal domain data.

        Args:
            horizontal_domain: Dictionary containing resolution information

        Returns:
            Formatted resolution string or empty string if not available
        """
        resolution_system = horizontal_domain.get("ResolutionAndCoordinateSystem", {})
        resolution_data = resolution_system.get("HorizontalDataResolution", {})

        if not resolution_data:
            return ""

        # Check for Varies resolution
        if resolution_data.get("VariesResolution") == "Varies":
            return "Varies"

        # Check for GriddedRangeResolutions (use maximum values)
        gridded_range = resolution_data.get("GriddedRangeResolutions", [])
        if gridded_range:
            # I spot checked 200 datasets, and never saw more than one entry
            # so I'm just going to use the first one for now for simplicity
            range_data = gridded_range[0]
            # in a gridded range, MinimumXDimension is also available,
            # however I have chosen to use the less impressive MaximumXDimension
            max_x = range_data.get("MaximumXDimension")
            max_y = range_data.get("MaximumYDimension")
            unit = range_data.get("Unit", "").lower()
            if max_x and max_y and unit:
                # Use the larger of the two dimensions
                max_dim = max(max_x, max_y)
                return f"{max_dim} {unit}"
            return ""

        # Check for GriddedResolutions
        gridded = resolution_data.get("GriddedResolutions", [])
        if gridded:
            grid_data = gridded[0]
            x_dim = grid_data.get("XDimension")
            y_dim = grid_data.get("YDimension")
            unit = grid_data.get("Unit", "").lower()
            if x_dim and y_dim and unit:
                # If dimensions differ, use the larger one
                max_dim = max(x_dim, y_dim)
                return f"{max_dim} {unit}"
            return ""

        # Check for GenericResolutions
        generic = resolution_data.get("GenericResolutions", [])
        if generic:
            generic_data = generic[0]
            x_dim = generic_data.get("XDimension")
            y_dim = generic_data.get("YDimension")
            unit = generic_data.get("Unit", "").lower()
            if x_dim and y_dim and unit:
                # If dimensions differ, use the larger one
                max_dim = max(x_dim, y_dim)
                return f"{max_dim} {unit}"
            return ""

        return ""

    def _process_download_info(self) -> DownloadInfo:
        """Process all download and visualization information."""
        has_distribution = False
        has_direct_download = False
        visualization_urls = []

        related_urls = self.umm.get("RelatedUrls", [])
        for url in related_urls:
            if url.get("URLContentType") == "DistributionURL" and url.get("Type") == "GET DATA":
                has_distribution = True
                if url.get("Subtype") == "DIRECT DOWNLOAD":
                    has_direct_download = True
            elif url.get("URLContentType") == "VisualizationURL":
                visualization_urls.append(url.get("URL", ""))

        return DownloadInfo(
            has_distribution=has_distribution,
            has_direct_download=has_direct_download,
            visualization_urls=visualization_urls,
            format=self.meta.get("format", ""),
        )

    def _process_processing_info(self) -> ProcessingInfo:
        """Process all processing level information."""
        processing_level = self.umm.get("ProcessingLevel", {}).get("Id", "")
        collection_type = self.umm.get("CollectionDataType", "")
        # Get all data center short names
        data_centers = [
            center.get("ShortName", "") for center in self.umm.get("DataCenters", []) if center.get("ShortName")
        ]

        return ProcessingInfo(processing_level, collection_type, data_centers)

    def get_properties(self) -> tuple[str, str]:
        """
        Get dataset strengths and weaknesses together.
        Returns tuple of (strengths_string, weaknesses_string).
        """
        strengths = set()
        weaknesses = set()

        # Collection activity
        if self.umm.get("CollectionProgress") == "ACTIVE":
            strengths.add("Data collection is ongoing")

        # Data type
        if self.processing_info.collection_type == "NEAR_REAL_TIME":
            strengths.add("Near real-time data is available")

        # Temporal characteristics
        if self.temporal_info.latest_end_date:
            age_in_days = (self.today - self.temporal_info.latest_end_date).days
            if age_in_days <= (3 * 365):
                strengths.add("Recent data is available")
            else:
                weaknesses.add("No recent data available")

        if self.temporal_info.total_duration:
            if self.temporal_info.total_duration >= (5 * 365):
                strengths.add("Long temporal extent")
            elif self.temporal_info.total_duration < 365:
                weaknesses.add("Limited temporal extent")

        # Download availability
        if self.download_info.has_direct_download:
            strengths.add("Direct data download available")
        elif self.download_info.has_distribution:
            weaknesses.add("Direct data download not available")

        return (
            "; ".join(sorted(strengths)) if strengths else "",
            "; ".join(sorted(weaknesses)) if weaknesses else "",
        )

    @property
    def strengths(self) -> str:
        """Get dataset strengths."""
        strengths, _ = self.get_properties()
        return strengths

    @property
    def weaknesses(self) -> str:
        """Get dataset weaknesses."""
        _, weaknesses = self.get_properties()
        return weaknesses

    @property
    def latency(self) -> str:
        """Get dataset latency."""
        latency_mapping = {
            "NEAR_REAL_TIME": "1-3 Hours",
            "LOW_LATENCY": "3 Hours to 1 Day",
            "EXPEDITED": "1-4 Days",
            "SCIENCE_QUALITY": "Not Provided",
        }
        return latency_mapping.get(self.processing_info.collection_type, "Not Provided")

    @property
    def intended_use(self) -> str:
        """Get dataset intended use path."""
        level = self.processing_info.level
        collection_type = self.processing_info.collection_type
        data_centers = self.processing_info.data_centers

        if level == "4" and collection_type == "SCIENCE_QUALITY":
            return "Path A"  # maps to "exploration"

        if (
            (level in ["2", "2a", "2b"] and "SEDAC" in data_centers and collection_type == "SCIENCE_QUALITY")
            or (level in ["3", "3a"] and collection_type == "SCIENCE_QUALITY")
            or (level == "4" and collection_type != "SCIENCE_QUALITY")
        ):
            return "Path B"  # maps to "basic analysis"

        return "Path C"  # maps to "advanced analysis"

    @property
    def geographic_coverage(self) -> str:
        """Get dataset geographic coverage."""
        return "Global" if self.spatial_info.is_global else ""

    @property
    def data_visualization(self) -> str:
        """Get dataset visualization URLs."""
        return "; ".join(self.download_info.visualization_urls)

    @property
    def temporal_resolution(self) -> str:
        """Get dataset temporal resolution."""
        if self.temporal_info.resolution and self.temporal_info.resolution_unit:
            return f"{self.temporal_info.resolution} {self.temporal_info.resolution_unit}"
        return ""

    @property
    def spatial_resolution(self) -> str:
        """Get dataset spatial resolution."""
        return self.spatial_info.resolution

    @property
    def projects(self) -> str:
        """Get dataset projects."""
        projects = self.umm.get("Projects", [])
        return "; ".join(project.get("ShortName", "") for project in projects if project.get("ShortName"))

    @property
    def dataset_name(self) -> str:
        """Get dataset short name."""
        return self.umm.get("ShortName", "")

    @property
    def description(self) -> str:
        """Get dataset abstract."""
        return self.umm.get("Abstract", "")

    @property
    def limitations(self) -> str:
        """Get dataset access constraints."""
        return self.umm.get("AccessConstraints", {}).get("Description", "")

    @property
    def format(self) -> str:
        """Get dataset format."""
        return self.download_info.format

    @property
    def temporal_extent(self) -> str:
        """Get dataset temporal extent."""
        return ", ".join(self.temporal_info.single_date_times)

    @property
    def source_link(self) -> str:
        """Generate source link from DOI information."""
        doi_field = self.umm.get("DOI", {})
        authority = doi_field.get("Authority")
        doi = doi_field.get("DOI")
        if authority and doi:
            return urllib.parse.urljoin(authority, doi)
        return ""

    @property
    def sde_link(self) -> str:
        """Generate SDE link from concept ID."""
        concept_id = self.meta.get("concept-id", "")
        if not concept_id:
            return ""

        base_url = "https://sciencediscoveryengine.nasa.gov/app/nasa-sba-smd/#/preview"
        query = '{"name":"query-smd-primary","scope":"All","text":""}'
        sinequa_id = f"/SDE/CMR_API/|{concept_id}"

        encoded_id = urllib.parse.quote(sinequa_id, safe="")
        encoded_query = urllib.parse.quote(query, safe="")

        return f"{base_url}?id={encoded_id}&query={encoded_query}"

    def to_dict(self) -> dict:
        """Convert CmrDataset to a dictionary with all final ej fields."""
        return {
            "concept_id": self.meta.get("concept-id", ""),
            "dataset": self.dataset_name,
            "description": self.description,
            "limitations": self.limitations,
            "format": self.format,
            "temporal_extent": self.temporal_extent,
            "intended_use": self.intended_use,
            "source_link": self.source_link,
            "sde_link": self.sde_link,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "latency": self.latency,
            "geographic_coverage": self.geographic_coverage,
            "data_visualization": self.data_visualization,
            "temporal_resolution": self.temporal_resolution,
            "spatial_resolution": self.spatial_resolution,
            "projects": self.projects,
        }
