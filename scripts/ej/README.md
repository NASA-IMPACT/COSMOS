# EJ Data Processing Pipeline

This pipeline processes NASA Common Metadata Repository (CMR) data and environmental justice (EJ) classifications to create standardized data dumps for the Science Discovery Engine (SDE).

## Overview

The pipeline consists of several components:
- CMR data processing
- Environmental justice classification processing
- Threshold-based filtering
- Data dump creation

## Setup

1. Clone the repository
2. Install dependencies
3. Configure settings in `scripts/ej/config.py`

## Input Files

You need two main input files:

1. **CMR Collections Data**: Generated using:
```bash
github.com/NASA-IMPACT/llm-app-EJ-classifier/blob/develop/scripts/data_processing/download_cmr.py
```

2. **Classification Predictions**: Provided by the classification model, contact Bishwas for access

## Configuration

Edit `scripts/ej/config.py` to customize:

- Classification thresholds
- Authorized classifications
- Input/output filenames
- Timestamp formats

Example configuration:
```python
# Adjust thresholds for different indicators
INDICATOR_THRESHOLDS = {
    "Climate Change": 1.0,
    "Disasters": 0.80,
    # ... other thresholds
}

# Change filenames
CMR_FILENAME = "your_cmr_file.json"
INFERENCE_FILENAME = "your_predictions.json"
```

## Usage

### Basic Usage

Run the pipeline on a local machine with the input files:
```bash
python create_ej_dump.py
```

## Output

The pipeline generates a JSON file named `ej_dump_YYYYMMDD_HHMMSS.json` containing:
- Processed CMR metadata
- Environmental justice classifications

## Server Deployment

To deploy the output to the server:
```bash
# Copy to server
scp ej_dump_YYYYMMDD_HHMMSS.json sde:/home/ec2-user/sde-indexing-helper/backups/

# Process on server using dm shell
dmshell

# add your file name to cmr_to_models.py
# paste and run the contents within the shell
```
