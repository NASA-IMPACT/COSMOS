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
