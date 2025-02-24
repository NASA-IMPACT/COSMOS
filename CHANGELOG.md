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

- 3227-bugfix-title-patterns-selecting-multi-url-pattern-does-nothing
  - Description: When selecting options from the match pattern type filter, the system does not filter the results as expected. Instead of displaying only the chosen variety of patterns, it continues to show all patterns.
  - Changes:
    - In `title_patterns_table` definition, corrected the column reference
    - Made `match_pattern_type` searchable
    - Corrected the column references and made code consistent on all the other tables, i.e., `exclude_patterns_table`, `include_patterns_table`, `division_patterns_table` and `document_type_patterns_table`

- 1001-tests-for-critical-functionalities
  - Description: Critical functionalities have been identified and listed, and critical areas lacking tests listed
  - Changes:
    - Integrated coverage.py as an indicative tool in the workflow for automated coverage reports on PRs, with separate display from test results.
    - Introduced docs/architecture-decisions/testing_strategy.md, which includes the coverage report, lists critical areas, and specifically identifies those critical areas that are untested or under-tested.
