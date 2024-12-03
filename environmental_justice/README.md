# Environmental Justice API

## Overview
This API provides access to Environmental Justice data from multiple sources. It supports retrieving data from individual sources or as a combined dataset with defined precedence rules.

## Endpoints

### GET /api/environmental-justice/

Retrieves environmental justice data based on specified data source.

#### Query Parameters

| Parameter    | Description | Default    | Options                                      |
|-------------|-------------|------------|----------------------------------------------|
| data_source | Data source filter | "combined" | "spreadsheet", "ml_production", "ml_testing", "combined" |

#### Data Source Behavior

1. **Single Source**
   - `?data_source=spreadsheet`: Returns only spreadsheet data
   - `?data_source=ml_production`: Returns only ML production data
   - `?data_source=ml_testing`: Returns only ML testing data

2. **Combined Data** (Default)
   - Access via `?data_source=combined` or no parameter
   - Merges data from 'spreadsheet' and 'ml_production' sources
   - Precedence rules:
     - If the same dataset exists in both sources, the spreadsheet version is used
     - Unique datasets from ml_production are included
     - ML testing data is not included in combined view

#### Example Requests

```bash
# Get combined data (default)
GET /api/environmental-justice/

# Get combined data (explicit)
GET /api/environmental-justice/?data_source=combined

# Get only spreadsheet data
GET /api/environmental-justice/?data_source=spreadsheet

# Get only ML production data
GET /api/environmental-justice/?data_source=ml_production

# Get only ML testing data
GET /api/environmental-justice/?data_source=ml_testing
```

#### Response Fields

Each record includes the following fields:
- dataset
- description
- description_simplified
- indicators
- intended_use
- latency
- limitations
- project
- source_link
- strengths
- format
- geographic_coverage
- data_visualization
- spatial_resolution
- temporal_extent
- temporal_resolution
- sde_link
- data_source

## Data Source Definitions

- **spreadsheet**: Primary source data from environmental justice spreadsheets
- **ml_production**: Production machine learning processed data
- **ml_testing**: Testing/staging machine learning processed data

## Precedence Rules
When retrieving combined data:
1. If a dataset exists in both spreadsheet and ml_production:
   - The spreadsheet version takes precedence
   - The ml_production version is excluded
2. Datasets unique to ml_production are included in the response
3. ML testing data is never included in combined results
