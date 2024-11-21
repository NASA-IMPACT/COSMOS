"""Configuration settings for EJ data processing."""

# Threshold values for different indicators
INDICATOR_THRESHOLDS = {
    "Not EJ": 0.80,
    "Climate Change": 1.0,
    "Disasters": 0.80,
    "Extreme Heat": 0.50,
    "Food Availability": 0.80,
    "Health & Air Quality": 0.90,
    "Human Dimensions": 0.80,
    "Urban Flooding": 0.50,
    "Water Availability": 0.80,
}

# List of authorized classifications
AUTHORIZED_CLASSIFICATIONS = [
    # "Climate Change",
    "Disasters",
    "Extreme Heat",
    "Food Availability",
    "Health & Air Quality",
    "Human Dimensions",
    "Urban Flooding",
    "Water Availability",
]

# File paths and names
CMR_FILENAME = "cmr_collections_umm_20240807_142146.json"
INFERENCE_FILENAME = "alpha-1.3-wise-vortex-42-predictions.json"

# Output format
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
OUTPUT_FILENAME_TEMPLATE = "ej_dump_{}.json"
