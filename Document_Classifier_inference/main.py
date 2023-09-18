import argparse
import json
from Document_Classifier_inference.test_predictions import TestPredictor


def predicts(config_file, url):
    """
    Predicts the possible full_forms and their confidence_scores which exceed the
    confidence_threshold given context and full_forms as input
    Arg(s):
            config_file: json file for config
            url (str): The URL of the test data
    Returns:
        str: The predicted category of the test data.
    """
    with open(config_file, "rb") as files:
        config = json.load(files)
    predictor = TestPredictor.from_dict(config)
    encoded_data = predictor.process_test_data(url)
    if isinstance(encoded_data,str):
        return "Image"
    input_ids, attention_masks = predictor.tokenize_test_data(encoded_data)
    category, confidence_score = predictor.predict_test_data(input_ids, attention_masks)
    return category, confidence_score


def batch_predicts(config_file, urls):
    """
    Predicts the possible full_forms and their confidence_scores which exceed the
    confidence_threshold given context and full_forms as input in a batch of maximum 8 urls
    Arg(s):
            config_file: json file for config
            urls (list): The URL of the test data in the form of list
    Returns:
        list: The predicted category of the test data for each url in the form of list.
    """
    with open(config_file, "rb") as files:
        config = json.load(files)
    predictor = TestPredictor.from_dict(config)
    prediction = {}
    url_list = []
    count = 0
    for url in urls:
        count = count + 1
        encoded_data = predictor.process_test_data(url)
        if isinstance(encoded_data,str):
            prediction["url"] = {"category": "Image", "confidence score": 100}
        else:
            url_list.append(url)
            input_ids, attention_masks = predictor.tokenize_test_data(encoded_data)
            category, _ = predictor.predict_test_data(
                input_ids, attention_masks
            )
            prediction[url] = config.get("webapp").get(category)
    return prediction


