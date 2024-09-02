""" Module for loading dataset """

from torch.utils.data import DataLoader, SequentialSampler, TensorDataset


class DataLoad:
    def __init__(self, batch_size=8):
        """
        Initializes a new instance of the class.

        Args:
            config (dict): Configuration parameters for the class.
            batch_size (int): The batch size for data loading. Default is 8.

        Attributes:
            batch_size (int): The batch size for data loading.
            self.inference_dataset: The inferencing dataset
        """

        self.inference_dataset = None
        self.batch_size = batch_size

    @classmethod
    def from_dict(cls, cfg: dict):
        """
        Creates an DataLoad object from a dictionary

        Args:
            cfg (dict): A dictionary containing configuration parameters for the loader

        Returns:
            DataLoad: An instance of the DataLoad class.

        """
        return cls(batch_size=cfg.get("dataload", {}).get("batch_size"))

    def dataset(self, input_ids, attention_masks):
        """
        Converts the input_ids and attention_masks into tensor dataset

        Args:
            token_results (dictionary): a dictonary containing information about input_ids, attention_masks,
            links, and indices for training set, test set and validation set.
            input_ids (list): A list of tensors containing input_ids of inference dataset
            attention_masks (list): A list of tensors containing attention_masks of the inference dataset
        Returns:
            None
        """
        # Split the samples, and create TensorDatasets for each split.

        self.inference_dataset = TensorDataset(input_ids, attention_masks)

    def dataloader(self):
        """
        Create data loaders for inference

        Returns:
            inference_dataloader (DataLoader): Data loader for the inference samples.
        """

        inference_sampler = SequentialSampler(self.inference_dataset)
        inference_dataloader = DataLoader(
            self.inference_dataset,
            sampler=inference_sampler,
            batch_size=self.batch_size,
        )
        return inference_dataloader
