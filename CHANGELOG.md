## Overview
These are not the release notes, which can be found https://github.com/NASA-IMPACT/COSMOS/releases. Instead, this is a changelog that developers use to log key changes to the codebase with each pull request.

## What to Include
For each PR made, an entry should be added to this changelog. It should contain
- a brief description of the deliverable of the feature or bugfix
- exact listing of key changes such as:
  - API endpoint modified
  - frontend components added
  - model updates
  - deployment changes needed on the servers
  - etc.

## Changelog

- 1052-update-cosmos-to-create-jobs-for-scrapers-and-indexers
  - Description: The original automation set up to generate the scrapers and indexers automatically based on a collection workflow status change needed to be updated to more accurately reflect the curation workflow. It would also be good to generate the jobs during this process to streamline the same.
  - Changes:
    - Updated function nomenclature. Scrapers are Sinequa connector configurations that are used to scrape all the URLs prior to curation. Indexers are Sienqua connector configurations that are used to scrape the URLs post to curation, which would be used to index content on production. Jobs are used to trigger the connectors which are included as parts of joblists.
    - Parameterized the convert_template_to_job method to include the job_source to streamline the value added to the <Collection> tag in the job XML.
    - Updated the fields that are pertinenet to transfer from a scraper to an indexer. Also added a third level of XML processing to facilitate the same.
    - scraper_template.xml and indexer_template.xml now contains the templates used for the respective configuration generation.
    - Deleted the redundant webcrawler_initial_crawl.xml file.
    - Added and updated tests on workflow status triggers.
