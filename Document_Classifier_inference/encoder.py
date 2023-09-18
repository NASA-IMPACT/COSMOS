""" Encoding the url response """
import pandas as pd


class Encoder:
    def __init__(self, config, data):
        """
        Initializes an Encoder object.

        Args:
            data: The data to be encoded.
            config (dict): A dictionary containing configuration parameters for the encoder.
            - "encoder" (dict): A sub-dictionary containing encoder-related configuration.
                    - "image_keyword" (list): The list of keywords associated with image data.
                    - "software_keyword" (list): The list of keywords associated with software and tools data.
                    - "mission_keyword" (list): The list of keywords associated with mission and instruments data.
                    - "training_keyword" (list): The list of keywords associated with training and education data.

        """
        self.image_keyword = config["encoder"]["image_keyword"]
        self.software_keyword = config["encoder"]["software_keyword"]
        self.mission_keyword = config["encoder"]["mission_keyword"]
        self.training_keyword = config["encoder"]["training_keyword"]
        self.data = data
        self.encoded_data = pd.DataFrame()

    @classmethod
    def from_dict(cls, cfg: dict, data):
        """
        Creates an Encoder object from a dictionary and data.

        Args:
            cfg (dict): A dictionary containing configuration parameters for the encoder.
            data: The data to be encoded.

        Returns:
            Encoder: An instance of the Encoder class.

        """
        return cls(cfg, data)

    def generate_text_slice(self, word_positions, text_whole):
        """
        Generates a text slice based on the positions of specific words in the given text.

        Args:
            word_positions (dict): A dictionary containing the positions of
            specific words in the text.
            text_whole (str): The text which needs to be sliced
        Returns:
            str: The extracted text slice based on the positions of the words.

        """
        # Find the minimum position of the words
        min_position = min(min(positions) for positions in word_positions.values())
        # Calculate the start and end indices for the text slice
        start_index = max(min_position[0] - 50, 0)
        end_index = min(start_index + 1000, len(text_whole) - 1)
        # Extract the text slice based on the start and end indices
        text_slice = text_whole[start_index:end_index]
        return text_slice

    def extract_text(self, text):
        """
        Extracts a text slice based on the occurrence and positions of specific keywords.

        Args:
            text (str): The input text to extract the slice from.

        Returns:
            str: The extracted text slice based on the positions of the keywords.

        """

        keywords = (
            self.image_keyword
            + self.software_keyword
            + self.mission_keyword
            + self.training_keyword
        )
        software_count, mission_count, image_count, training_count = 0, 0, 0, 0
        word_positions = {}
        start = -1
        for word in text.split():
            start = text.find(word, start + 1)
            end = start + len(word)
            if word in keywords and word not in word_positions:
                word_positions[word] = []

            if word in self.image_keyword:
                image_count = image_count + 1
                word_positions[word].append((start, end))

            if word in self.software_keyword:
                software_count = software_count + 1
                word_positions[word].append((start, end))

            if word in self.mission_keyword:
                mission_count = mission_count + 1
                word_positions[word].append((start, end))

            if word in self.training_keyword:
                training_count = training_count + 1
                word_positions[word].append((start, end))

        if (
            software_count == 0
            and mission_count == 0
            and image_count == 0
            and training_count == 0
        ):
            mid = int(len(text) / 2)
            start_pos = mid - 512
            end_pos = mid + 512  # in terms of characters
            text_slice = text[start_pos:end_pos]
        else:
            text_slice = self.generate_text_slice(word_positions, text)
        return text_slice

    def encoder(self):
        """
        Encodes the data by processing the text, URLs, and classes.

        Returns:
            pandas.DataFrame: The encoded data with processed text, URLs, and classes.

        """
        text_list, urls_list, class_list = [], [], []
        for _, row in self.data.iterrows():
            text = row["text"]
            url = row["links"]
            classes = row["class"]
            counter = text.split()
            if len(counter) <= 400:
                text_list.append(text)
                urls_list.append(url)
                class_list.append(classes)
            elif len(counter) > 400:
                text = self.extract_text(text)
                text_list.append(text)
                urls_list.append(url)
                class_list.append(classes)
        self.encoded_data["text"] = text_list
        self.encoded_data["links"] = urls_list
        self.encoded_data["class"] = class_list
        return self.encoded_data
