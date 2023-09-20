import importlib

import numpy as np
import pandas as pd
import torch

from Document_Classifier_inference.encoder import Encoder
from Document_Classifier_inference.model import ModelBert
from Document_Classifier_inference.preprocessing import Preprocessor


class TestPredictor:
    """
    Class created for sample predictions
    """

    def __init__(self, config):
        model = ModelBert.from_dict(config)
        self.loaded_model = model.load_model()
        self.device = torch.device("cpu")
        self.dataframe = pd.DataFrame()  # columns=['text','class']
        self.config = config
        self.classes = self.config["classes"]
        transformers = importlib.import_module(
            self.config["model_parameters"]["module_name"]
        )
        tokenizer_class = getattr(
            transformers, self.config["model_parameters"]["model"]
        )
        # Load the tokenizer and model
        self.tokenizer = tokenizer_class.from_pretrained(
            self.config["model_parameters"]["model_type"]
        )
        self.pdf_lists = []

    @classmethod
    def from_dict(cls, cfg: dict):
        """
        Creates an Encoder object from a dictionary and data.

        Args:
            cfg (dict): A dictionary containing configuration parameters for the encoder.

        Returns:
            Encoder: An instance of the Encoder class.

        """
        return cls(cfg)

    def convert_labels_to_class(self, value):
        """
        Converts a label value to its corresponding class/category.

        Parameters:
            value (int): The label value to be converted.

        Returns:
            str: The corresponding class/category for the given label value.

        """
        for category, val in self.classes.items():
            if val == value:
                return category

    def process_test_data(self, urls):
        """
        Processes the test data by retrieving content from the provided URL and encoding it.

        Parameters:
            url (str): The URL of the test data.

        Returns:
            Union[str, DataFrame]: If the content type is an image, returns "Image".
                                Otherwise, returns the encoded test data as a DataFrame.

        """
        self.dataframe["links"] = urls
        self.dataframe["class"] = [3 for i in urls]  # any random class
        processor = Preprocessor.from_dict(self.config, self.dataframe)
        processor.remove_header_footer()
        (
            self.dataframe,
            self.pdf_lists,
            self.image_lists,
        ) = processor.preprocessed_features()
        self.dataframe["text"] = self.dataframe["soup"]
        encoder = Encoder.from_dict(self.config, self.dataframe)
        encoded_data = encoder.encoder()
        return encoded_data, self.pdf_lists, self.image_lists

    def tokenize_test_data(self, encoded_data):
        """
        Tokenizes the encoded test data using the tokenizer specified in the configuration.

        Parameters:
            encoded_data (DataFrame): The encoded test data.

        Returns:
            Tuple[Tensor, Tensor]: The input IDs and attention masks of the tokenized test data.

        """
        sentence, labels, links = [], [], []
        for _, row in encoded_data.iterrows():
            sentence.append(row["text"])
            labels.append(row["class"])
            links.append(row["links"])
        module_name = self.config["model_parameters"]["module_name"]
        transformers = importlib.import_module(module_name)
        # Dynamically get the model class from transformers module
        tokenizer_class = getattr(
            transformers, self.config["model_parameters"]["tokenizer"]
        )
        tokenizer = tokenizer_class.from_pretrained(
            self.config["model_parameters"]["model_type"]
        )
        input_ids, attention_masks = [], []
        for sent in sentence:
            encoded_dict = tokenizer.encode_plus(
                text=sent,
                add_special_tokens=True,
                truncation=True,
                max_length=500,
                padding="max_length",
                return_attention_mask=True,
                return_tensors="pt",
            )
            input_ids.append(encoded_dict["input_ids"])
            attention_masks.append(encoded_dict["attention_mask"])
        input_ids = torch.cat(input_ids, dim=0)
        attention_masks = torch.cat(attention_masks, dim=0)
        return input_ids, attention_masks, links

    def predict_test_data(self, input_ids, attention_masks):
        """
        Predicts the category of test data given its input IDs and attention masks.

        Parameters:
            input_ids (list): The list of tensor of input IDs of the test data.
            attention_masks (list): The list of tensor of attention masks of the test data.

        Returns:
            categories (list): The list of predicted category of the test data.

        """
        self.loaded_model.eval()
        with torch.no_grad():
            outputs = self.loaded_model(
                input_ids,
                token_type_ids=None,
                attention_mask=attention_masks,
                return_dict=True,
            )
        preds = outputs.logits
        preds = torch.sigmoid(preds)
        preds = preds.detach().cpu().numpy()
        # To get predictions for all urls
        preds_position = [np.argmax(arr).tolist() for arr in preds]
        # Respective categories for all the urls
        categories = [
            self.convert_labels_to_class(position) for position in preds_position
        ]
        return categories
