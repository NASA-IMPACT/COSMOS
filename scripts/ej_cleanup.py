import json

import pandas as pd

FILENAME = "ej_emily_cleaned.xlsx"

sheet_dict = {
    "climate": "Climate (Climate Change) - CIP",
    "disasters": "Disasters (Disaster Recovery) -",
    "extreme_heat": "Extreme Heat - CIP",
    "food_availability": "Food Availability - Cleaned",
    "health_and_air_quality": "Health and Air Quality - CIP",
    "human_dimensions": "Human Dimensions - Cleaned",
    "urban_flooding": "Urban Flooding - Cleaned",
    "water_availability": "Water Availability - Cleaned",
}

dataframes = {
    sheet_id: pd.read_excel(FILENAME, sheet_name=sheet_name, header=1)
    for sheet_id, sheet_name in sheet_dict.items()
}

standard_columns = [
    "Dataset",
    "Indicators                     (Select from drop-down list)",
    "Description",
    "Description Simplified",
    "Geographic Coverage",
    "Format",
    "Spatial Resolution",
    "Temporal Resolution",
    "Temporal Extent",
    "Latency",
    "Source/Link",
    "Project",
    "Strengths",
    "Limitations",
    "Data Visualization",
    "Intended Use",
    "Spatial Resolution (Standard)",
]


def column_check():
    # check for standard columns
    for sheet_name, df in dataframes.items():
        print(sheet_name, set(standard_columns) - set(df.columns))

    for sheet_name, df in dataframes.items():
        print(sheet_name, set(df.columns) - set(standard_columns))


# remove non-standard columns
for sheet_name, df in dataframes.items():
    to_remove = set(df.columns) - set(standard_columns)
    for col in to_remove:
        df.drop(col, inplace=True, axis=1)

list_of_dfs = []
for sheet_name, dataframe in dataframes.items():
    list_of_dfs.append(dataframe)

combined = pd.concat(list_of_dfs)
combined["Dataset"] = combined["Dataset"].str.strip()

# remove duplicates using the column "Dataset"
combined = combined.drop_duplicates(subset=["Dataset"])

print(f"Final row count: {len(combined)}")

cols = {
    "Dataset": "dataset",
    "Indicators                     (Select from drop-down list)": "indicators",
    "Description": "description",
    "Description Simplified": "description_simplified",
    "Geographic Coverage": "geographic_coverage",
    "Format": "format",
    "Spatial Resolution (Standard)": "spatial_resolution",
    "Temporal Resolution": "temporal_resolution",
    "Temporal Extent": "temporal_extent",
    "Latency": "latency",
    "Source/Link": "source_link",
    "Project": "project",
    "Strengths": "strengths",
    "Limitations": "limitations",
    "Data Visualization": "data_visualization",
    "Intended Use": "intended_use",
}

combined.rename(columns=cols, inplace=True)
combined.drop("Spatial Resolution", axis=1, inplace=True)

COUNT = 0


def create_ej_row_json(row):
    global COUNT
    COUNT += 1
    return {
        "model": "environmental_justice.environmentaljusticerow",
        "pk": COUNT,
        "fields": {
            "dataset": row["dataset"],
            "description": row["description"],
            "description_simplified": row["description_simplified"],
            "indicators": row["indicators"],
            "intended_use": row["intended_use"],
            "latency": row["latency"],
            "limitations": row["limitations"],
            "project": row["project"],
            "source_link": row["source_link"],
            "strengths": row["strengths"],
            "format": row["format"],
            "geographic_coverage": row["geographic_coverage"],
            "data_visualization": row["data_visualization"],
            "spatial_resolution": row["spatial_resolution"],
            "temporal_extent": row["temporal_extent"],
            "temporal_resolution": row["temporal_resolution"],
        },
    }


combined.fillna("", inplace=True)
combined["temporal_extent"] = combined["temporal_extent"].astype("string")
combined["json"] = combined.apply(lambda row: create_ej_row_json(row), axis=1)


json.dump(
    combined["json"].tolist(),
    open(
        "/Users/aacharya/work/sde-indexing-helper/environmental_justice/fixtures/ej_row.json",
        "w",
    ),
)

print("Done")
