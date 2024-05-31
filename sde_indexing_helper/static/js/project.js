

/* Project specific Javascript goes here. */
 const tableHeaderDefinitions = {
    "Name": "The designated name of the collection.",
    "URL": "The primary URL of the collection from which the scraping process begins.",
    "Division": "The specific division to which the collection belongs. It can be one of: Astrophysics, Heliophysics, Biological and Physical Sciences, Earth Science, or Planetary Science.",
    "Candidate URLs" : "The URLs crawled from the base URL by Sinequa. These are curated and sent for indexing.",
    "Workflow Status": "The current stage of the collection within the workflow.",
    "Curator": "The individual responsible for curating this collection.",
    "Connector Type": "Indicates whether the connector is a web crawler or API-based."
}


const candidateTableHeaderDefinitons = {
  "URL": "A scraped URL.",
  "Exclude": "Whether or not this URL is excluded from the collection.",
  "Scraped Title": "Title scraped from the document.",
  "New Title" : "New title set by a user.",
  "Document Type": "{insert description here}",
  "Match Pattern" : "Pattern that is used to match against URLs in the collection.",
  "Match Pattern Type": "{Insert explanation here}",
  "Reason": "{Insert explanation here}",
  "Affected URLs": "The URLs that match the pattern.",
  "Actions": "Delete a pattern."
};
