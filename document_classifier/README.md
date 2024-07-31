# Automated Document Tagging

# Project Description:

This purpose of this is to tag the content of a given url onto one of the six classes "Image","Documentation","Software and Tools",
"Mission and Instruments", "Training and Education", and "Data".

# Datasets:

Reference link for datasets: https://docs.google.com/spreadsheets/d/1rK7hvb_HRd-sqL3jrSYll5BiDvwnzQY2qVWDmpg6Bbk/edit#gid=1560325588

# To run the inference pipeline:

- location for saved model in drive: https://drive.google.com/drive/u/1/folders/1jkJSpN3ZuXhZIis4dSc-v0LkSV3pMrcs
- saved weight_name: model.pt
- prediction sample: `python3 main.py predicts --config_file config.json --url "url_link"`

For more details: contact rd0081@uah.edu
