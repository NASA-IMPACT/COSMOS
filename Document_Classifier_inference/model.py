import os
import importlib
import torch
from transformers import logging

logging.set_verbosity(40)

os.environ["TOKENIZERS_PARALLELISM"] = "false"


class ModelBert:
    """
    A class for predicting the correct long form for a given acronym
    in a context paragraph using a pre-trained BERT model and tokenizer.

    """

    def __init__(self, config, num_labels=5, device="cpu"):
        self.config = config["model_parameters"]
        self.num_labels = num_labels
        self.device = torch.device(device)
        self.model = None
        self.tokenizer = None
        self.state_dict = None

    @classmethod
    def from_dict(cls, cfg: dict):
        """
        Creates an ModelBert object from a dictionary.

        Args:
            cfg (dict): A dictionary containing configuration parameters for the encoder.
            data: The data to be encoded.

        Returns:
            ModelBert: An instance of the ModelBert class.

        """
        model_parameters = cfg.get("model_parameters")
        return cls(
            cfg,
            num_labels=model_parameters.get("num_labels"),
            device=model_parameters.get("device"),
        )

    def make_model(self):
        """
        Instantiates a pre-trained BERT model and tokenizer.
        Returns:
            A tuple containing the model and the tokenizer.
        """
        # Dynamicall import the transformers module
        module_name = self.config["module_name"]
        transformers = importlib.import_module(module_name)
        # Dynamically get the model class from transformers module
        model_class = getattr(transformers, self.config["model"])
        tokenizer_class = getattr(transformers, self.config["model"])
        # Load the tokenizer and model
        self.tokenizer = tokenizer_class.from_pretrained(self.config["model_type"])
        self.model = model_class.from_pretrained(
            self.config["model_type"], num_labels=self.config["num_labels"]
        ).to(self.device)
        return self.model, self.tokenizer

    def load_model(self):
        """This function loads the models and processes the data for evaluation"""
        self.state_dict = torch.load(
            self.config["saved_model_name"], map_location=self.device
        )
        model1, _ = self.make_model()
        model1.load_state_dict(self.state_dict)
        return model1
