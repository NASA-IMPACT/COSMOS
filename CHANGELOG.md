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

- 1209-bug-fix-document-type-creator-form
  - Description: The dropdown on the pattern creation form needs to be set as multi as the default option since this is why the doc type creator form is used for the majority of multi-URL pattern creations. This should be applied to doc types, division types, and titles as well.
  - Changes:
    - Set the default value for `match_pattern_type` in `BaseMatchPattern` class is set to `2`
    - Changed `test_create_simple_exclude_pattern` test within `TestDeltaExcludePatternBasics`
    - Changed `test_create_division_pattern` and `test_create_document_type_pattern_single` within `TestFieldModifierPatternBasics`

- 1052-update-cosmos-to-create-jobs-for-scrapers-and-indexers
  - Description: The original automation set up to generate the scrapers and indexers automatically based on a collection workflow status change needed to be updated to more accurately reflect the curation workflow. It would also be good to generate the jobs during this process to streamline the same.
  - Changes:
    - Updated function nomenclature. Scrapers are Sinequa connector configurations that are used to scrape all the URLs prior to curation. Indexers are Sienqua connector configurations that are used to scrape the URLs post to curation, which would be used to index content on production. Jobs are used to trigger the connectors which are included as parts of joblists.
    - Parameterized the convert_template_to_job method to include the job_source to streamline the value added to the `<Collection>` tag in the job XML.
    - Updated the fields that are pertinenet to transfer from a scraper to an indexer. Also added a third level of XML processing to facilitate the same.
    - scraper_template.xml and indexer_template.xml now contains the templates used for the respective configuration generation.
    - Deleted the redundant webcrawler_initial_crawl.xml file.
    - Added and updated tests on workflow status triggers.

- 2889-serialize-the-tdamm-tags
  - Description: Have TDAMM serialzed in a specific way and exposed via the Curated URLs API to be consumed into SDE Test/Prod
  - Changes:
    - Changed `get_tdamm_tag` method in the `CuratedURLAPISerializer` to process the TDAMM tags and pass them to the API endpoint

- 960-notifications-add-a-dropdown-with-options-on-the-feedback-form
  - Description: Generate an API endpoint and publish all the dropdown options necessary as a list for LRM to consume it.
  - Changes:
    - Created a new model `FeedbackFormDropdown`
    - Added the migration file
    - Added the `dropdown_option` field to the `Feedback` model
    - Updated the slack notification structure by adding the dropdown option text
    - Created a new serializer called `FeedbackFormDropdownSerializer`
    - Added a new API endpoint `feedback-form-dropdown-options-api/` where the list is going to be accesible
    - Added a list view called `FeedbackFormDropdownListView`
    - Added tests

- 1217-add-data-validation-to-the-feedback-form-api-to-restrict-html-content
  - Description: The feedback form API does not currently have any form of data validation on the backend which makes it easy for the user with the endpoint to send in data with html tags. We need to have a validation scheme on the backend to protect this from happening.
  - Changes:
    - Defined a class `HTMLFreeCharField` which inherits `serializers.CharField`
    - Used regex to catch any HTML content comming in as an input to form fields
    - Called this class within the serializer for necessary fields

- 1030-resolve-0-value-document-type-in-nasa_science
  - Description: Around 2000 of the docs coming out of the COSMOS api for nasa_science have a doc type value of 0.
  - Changes:
    - Added `obj.document_type != 0` as a condition in the `get_document_type` method within the `CuratedURLAPISerializer`

- 1014-add-logs-when-importing-urls-so-we-know-how-many-were-expected-how-many-succeeded-and-how-many-failed
  - Description: When URLs of a given collection are imported into COSMOS, a Slack notification is sent. This notification includes the name of the collection imported,count of the existing curated URLs, total URLs count as per the server, URLs successfully imported from the server, delta URLs identified and delta URLs marked for deletion.
  - Changes:
    - The get_full_texts() function in sde_collections/sinequa_api.py is updated to yeild total_count along with rows.
    - fetch_and_replace_full_text() function in sde_collections/tasks.py captures the total_server_count and triggers send_detailed_import_notification().
    - Added a function send_detailed_import_notification() in sde_collections/utils/slack_utils.py to structure the notification to be sent.
    - Updated the associated tests effected due to inclusion of this functionality.

- 3228-bugfix-preserve-scroll-position--document-type-selection-behavior-on-individual-urls
  - Description: Upon selecting a document type on any individual URL, the page refreshes and returns to the top. This is not necessarily a bug but an inconvenience, especially when working at the bottom of the page. Fix the JS code.
  - Changes:
    - Added a constant `scrollPosition` within `postDocumentTypePatterns` to store the y coordinate postion on the page
    - Modified the ajax relaod to navigate to this position upon posting/saving the document type changes.

- 3227-bugfix-title-patterns-selecting-multi-url-pattern-does-nothing
  - Description: When selecting options from the match pattern type filter, the system does not filter the results as expected. Instead of displaying only the chosen variety of patterns, it continues to show all patterns.
  - Changes:
    - In `title_patterns_table` definition, corrected the column reference
    - Made `match_pattern_type` searchable
    - Corrected the column references and made code consistent on all the other tables, i.e., `exclude_patterns_table`, `include_patterns_table`, `division_patterns_table` and `document_type_patterns_table`

- 1190-add-tests-for-job-generation-pipeline
  - Description: Tests have been added to enhance coverage for the config and job creation pipeline, alongside comprehensive tests for XML processing.
  - Changes:
    - Added config_generation/tests/test_config_generation_pipeline.py which tests the config and job generation pipeline, ensuring all components interact correctly
    - config_generation/tests/test_db_to_xml.py is updated to include comprehensive tests for XML Processing

- 1001-tests-for-critical-functionalities
  - Description: Critical functionalities have been identified and listed, and critical areas lacking tests listed
  - Changes:
    - Integrated coverage.py as an indicative tool in the workflow for automated coverage reports on PRs, with separate display from test results.
    - Introduced docs/architecture-decisions/testing_strategy.md, which includes the coverage report, lists critical areas, and specifically identifies those critical areas that are untested or under-tested.

- 1192-finalize-the-infrastructure-for-frontend-testing
  - Description: Set up comprehensive frontend testing infrastructure using Selenium WebDriver with Chrome, establishing a foundation for automated UI testing.
  - Changes:
    - Added Selenium testing dependency to `requirements/local.txt`
    - Updated Dockerfile to support Chrome and ChromeDriver
    - Created BaseTestCase and AuthenticationMixin for reusable test components
    - Implemented core authentication test suite

- 1195-implement-unit-test-for-forms-on-the-frontend
  - Description: Implemented comprehensive frontend test suite covering authentication, collection management, search functionality, and pattern application forms.
  - Changes:
    - Added tests for authentication flows
    - Implemented collection display and data table tests
    - Added universal search functionality tests
    - Created search pane filter tests
    - Added pattern application form tests with validation checks

- 1101-bug-fix-quotes-not-escaped-in-titles
  - Description: Title rules that include single quotes show up correctly in the sinequa frontend (and the COSMOS api) but not in the delta urls page.
  - Changes:
    - Added `escapeHtml` function in the `delta_url_list.js` file to handle special character escaping correctly.
    - Called this function while retrieving the titles in `getGeneratedTitleColumn()` and `getCuratedGeneratedTitleColumn()` functions.

- 1240-fix-code-scanning-alert-inclusion-of-functionality-from-an-untrusted-source
  - Description: Ensured all external resources load securely by switching to HTTPS and adding Subresource Integrity (SRI) checks.
  - Changes:
    - Replaced protocol‑relative URLs with HTTPS.
    - Added SRI (integrity) and crossorigin attributes to external script tags.

- 1196-arrange-the-show-100-csv-customize-columns-boxes-to-be-in-one-line-on-the-delta-urls-page
  changelog-update-Issue-1001
  - Description: Formatting the buttons - 'Show 100','CSV' and 'Customize Columns' to be on a single line for an optimal use of space.
  - Changes:
    - Updated delta_url_list.css and delta_url_list.js files with necessary modifications

- 1246-minor-enhancement-document-type-pattern-form-require-document-type-or-show-appropriate-error
  - Description: In the Document Type Pattern Form, if the user does not select a Document Type while filling out the form, an appropriate error message is displayed.
  - Changes:
    - Added a JavaScript validation check on form submission to ensure the document type (stored in a hidden input) is not empty.
    - Display an error message and prevent form submission if the field is empty.

- 1249-add-https-link-to-cors_allowed_origins-for-sde-lrm
  - Description: The feedback form API was throwing CORS errors and to rectify that, we need to add the apt https link for sde-lrm.
  - Changes:
    - Added `https://sde-lrm.nasa-impact.net` to `CORS_ALLOWED_ORIGINS` in the base settings.
