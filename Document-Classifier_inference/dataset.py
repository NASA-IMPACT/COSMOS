import pandas as pd


def convert_dataset_to_csv(config):
    """
    Converts an Excel dataset to a CSV file.

    Parameters:
        config (dict): A dictionary containing configuration parameters.
            - 'preprocess' (dict): A dictionary containing preprocessing settings.
                - 'raw_data' (str): The file path of the raw Excel dataset.
                - 'processed_data' (str): The file path where the converted csv is saved.

    Returns:
        None
    """
    loaded_file = pd.ExcelFile(config["preprocess"]["raw_data"])
    sheet_names = loaded_file.sheet_names
    data = pd.DataFrame(columns=["links", "class"])
    for i, sheet_name in enumerate(sheet_names):
        dataframe = pd.read_excel(
            loaded_file, sheet_name=sheet_name, header=None, names=["links"]
        )
        dataframe["class"] = i
        data = pd.concat([data, dataframe], axis=0)
    data.to_csv(config["preprocess"]["processed_data"], index=False)
