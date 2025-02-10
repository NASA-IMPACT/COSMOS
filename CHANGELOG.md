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
