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
