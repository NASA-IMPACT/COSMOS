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
- 1030-resolve-0-value-document-type-in-nasa_science
  - Description: Around 2000 of the docs coming out of the COSMOS api for nasa_scince have a doc type vaule of 0.
  - Changes:
    - Added `obj.document_type != 0` as a condition in the `get_document_type` method within the `CuratedURLAPISerializer`
    - Added a changelog.md file
