
## Classifying Collections

We need the latest fulltext.
Therefore, classifications happen at the level of the DumpUrl.

## Curated vs Delta

### First times
Classification Value
- ml = blank
- manual = blank

After Curation
- ml = black holes
- manual = x-rays

### Second Time
Classification Value
- ml = black holes
- manual = x-rays
This will evaluate as equivalent, and no delta will be generated.

### Third Time
Classification Value

- ml = x-rays
- manual = x-rays

Technically ml has changed, but does that mean we want a delta? No, because the manual classification is authoritative.
Therefore, we should send this dump url directly to CuratedUrls.

## Requirements
- we must actually have full texts in order to run the classifier
- changed ML values with no curator override should register as deltas
- changed ML values WITH curator override should NOT register as deltas, UNLESS the full text has changed.
- probably ML titles should not be registered as deltas? Since every time they will be different?
  - nevermind. i'm being dumb. it will only be regenerated if the full text has changed.

## Implementation Possibilities
### DumpUrl
Pros
- By using the DumpUrl and the associated promotion code, we can piggy back on the DeltaUrl determination processes to handle delta generation

Cons
- You have to re-pull from dev in order to classify
- Promotion has to wait on inference server processing (this is also a pro, as Emily will never see until the processing is done)

### Dedicated Process
Pros

Cons
- Needs to be able to run on curated + deltas and merge the results
- Separate process for delta generation, or a refactor that can pull in the modularized version of the existing code
- Needs to enforce existence of fulltexts for the specified collection


## How are things classified
- if the division is general, then it is automatically marked as needing division classification
- if it is astrophysics, then it is automatically marked as needing TDAMM classification
  - consider running this on a url basis?
- auto bad title identifier,  every single collection has this run on it? or does emily pick collections?
- auto bad title fixer
  - as long as it only fixes bad titles, it should run on every collection
- auto excludes?
