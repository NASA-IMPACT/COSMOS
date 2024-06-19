

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
  "URL": "The web address of a specific webpage from a given source.",
  "Exclude": "The action of omitting a certain URL(s) from being included in the final list of candidate URLs. This can be based on URL patterns or URL content.",
  "Scraped Title": "The initial scraped title of the webpage generated from the webpage metadata.",
  "New Title" : "A modified or updated title for a webpage set by the curator either through a manual or pattern change. The new title often improves readability and clarity.",
  "Document Type": "The classification of the content found at the URL. This can be set as 'Documentation', 'Images', 'Software and Tools', 'Missions and Instruments', or 'Data'.",
  "Match Pattern" : "A pattern set by the curator for which to exclude URLs, change URL titles, or assign URL document types. A match pattern could be a portion of the URL (e.g. URL extension) or a pattern that includes wild cards.",
  "Match Pattern Type": "Indicates whether the Match Pattern applies to a single or multiple URLs.",
  "Reason": "Indicates why the curator has excluded single or multiple URLs.",
  "Affected URLs": "Indicates the number of URLs the given action, rule, or pattern has been applied to.",
  "Actions": "Gives the curator the ability to delete a set title, document type, or exclude pattern.",
  "Title Pattern": "A specific format given by the curator to make changes to original titles. This can include the use of xpaths or additions to the original title string."
};
