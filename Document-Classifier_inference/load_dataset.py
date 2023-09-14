""" Module for loading dataset """
from torch.utils.data import TensorDataset
from torch.utils.data import DataLoader, RandomSampler, SequentialSampler


class DataLoad:
    def __init__(self, batch_size=8):
        """
        Initializes a new instance of the class.

        Args:
            config (dict): Configuration parameters for the class.
            batch_size (int): The batch size for data loading. Default is 8.

        Attributes:
            train_dataset: The training dataset.
            val_dataset: The validation dataset.
            test_dataset: The test dataset.
            batch_size (int): The batch size for data loading.
            test_links: Links associated with the test dataset.
            self.train_dataset=None
            self.val_dataset=None
            self.test_dataset=None
            self.batch_size=batch_size
            self.test_links=None
        """

        self.train_dataset = None
        self.val_dataset = None
        self.test_dataset = None
        self.batch_size = batch_size
        self.test_links = None

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

    # def dataset(
    #     self, input_ids, attention_masks, labels, train_idx, val_idx, test_idx, links
    # ):
    def dataset(self, token_results):
        """
        Split the samples into training, validation, and test datasets, and create
        TensorDatasets for each split.

        Args:
            token_results (dictionary): a dictonary containing information about input_ids, attention_masks,
            labels, links, and indices for training set, test set and validation set.
        Returns:
            None
        """
        input_ids, attention_masks = (
            token_results["input_ids"],
            token_results["attention_masks"],
        )
        labels, links = token_results["labels"], token_results["links"]
        train_idx = token_results["train_idx"]
        val_idx, test_idx = token_results["val_idx"], token_results["test_idx"]
        # Split the samples, and create TensorDatasets for each split.
        self.train_dataset = TensorDataset(
            input_ids[train_idx],
            attention_masks[train_idx],
            labels[train_idx],
        )
        self.val_dataset = TensorDataset(
            input_ids[val_idx],
            attention_masks[val_idx],
            labels[val_idx],
        )
        test_links = [links[idx] for idx in test_idx]
        self.test_dataset = TensorDataset(
            input_ids[test_idx],
            attention_masks[test_idx],
            labels[test_idx],
        )
        self.test_links = test_links

    def dataloader(self):
        """
        Create data loaders for training, validation, and prediction.

        Returns:
            train_dataloader (DataLoader): Data loader for the training samples.
            validation_dataloader (DataLoader): Data loader for the validation samples.
            prediction_dataloader (DataLoader): Data loader for the prediction samples.
            test_links (list): List of links associated with the test samples.
        """
        train_dataloader = DataLoader(
            self.train_dataset,  # The training samples.
            sampler=RandomSampler(self.train_dataset),  # Select batches randomly
            # shuffle=True,
            batch_size=self.batch_size,  # Trains with this batch size.
        )

        # For validation the order doesn't matter, so we'll just read them sequentially.
        validation_dataloader = DataLoader(
            self.val_dataset,  # The validation samples.
            sampler=SequentialSampler(
                self.val_dataset
            ),  # Pull out batches sequentially.
            batch_size=self.batch_size,  # Evaluate with this batch size.
        )

        prediction_sampler = SequentialSampler(self.test_dataset)
        prediction_dataloader = DataLoader(
            self.test_dataset, sampler=prediction_sampler, batch_size=self.batch_size
        )
        return (
            train_dataloader,
            validation_dataloader,
            prediction_dataloader,
            self.test_links,
        )
