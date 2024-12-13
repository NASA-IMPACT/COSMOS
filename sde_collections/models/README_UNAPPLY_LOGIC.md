# Pattern System Unapply Logic

## Core Principles
1. When patterns are removed, we need to handle deltas based on their relationship to curated URLs
2. Deltas should only exist if they differ from their curated counterparts, or if no curated URL exists
3. Multiple patterns can affect the same URL
4. Manual changes to deltas should be preserved

## Cases to Handle

### Case 1: Delta Only (New URL)
**Scenario:**
- No curated URL exists for this URL
- Delta URL exists with pattern effect
- Pattern is removed
```
Curated: None exists
Delta: url=new.com, division=None
```
`[Pattern: division=BIOLOGY], created`
```
Curated: None exists
Delta: url=new.com, division=BIOLOGY
```
`[Pattern: division=BIOLOGY], deleted`
```
Curated: None exists
Delta: url=new.com, division=None
```

### Case 2: Delta Created to Apply Pattern
**Scenario:**
- A Curated with no division already exists
- A pattern is created
- A delta is created to  to apply a pattern
- Pattern is removed
- Delta should be deleted
```
Curated: division=None
```
`[Pattern: division=BIOLOGY], created`
```
Curated: division=None
Delta: division=BIOLOGY (from pattern)
```
`[Pattern: division=BIOLOGY], deleted`
```
Curated: division=None
```

### Case 3: Pre-existing Delta
- A Curated with no division already exists
- A Delta with an updated scraped_title exists
- A pattern is created to set division
- A delta is created to apply a pattern
- Pattern is removed
- Delta should be maintained because of scraped_title

```
Curated: division=None
Delta: scraped_title="Modified", division=None
```
`[Pattern: division=BIOLOGY], created`
```
Curated: division=None
Delta: scraped_title="Modified", division=BIOLOGY (from pattern)
```
`[Pattern: division=BIOLOGY], deleted`
```
Curated: division=None
Delta: scraped_title="Modified", division=None
```

### Case 4: Multiple Pattern Effects
**Scenario:**
- Delta has changes from multiple patterns
- One pattern is removed
```
Delta: division=BIOLOGY, doc_type=DATA (from two patterns)
Pattern: division=BIOLOGY
Pattern: doc_type=DATA
```
`[Pattern: division=BIOLOGY], deleted`
```
Delta: division=None, doc_type=DATA
Pattern: doc_type=DATA
```

### Case 5: Overlapping Patterns, Specific Deleted
```
Curated: division=ASTROPHYSICS (because of specific pattern)
Specific Pattern: division=ASTROPHYSICS
General Pattern: division=BIOLOGY
```
`[Specific Pattern: division=ASTROPHYSICS], deleted`

```
Curated: division=BIOLOGY (because of general pattern)
General Pattern: division=BIOLOGY
```


### Case 6: Overlapping Patterns, General Deleted
```
Curated: division=ASTROPHYSICS (because of specific pattern)
Specific Pattern: division=ASTROPHYSICS
General Pattern: division=BIOLOGY
```
`[General Pattern: division=BIOLOGY], deleted`

```
Curated: division=ASTROPHYSICS (because of specific pattern)
Specific Pattern: division=ASTROPHYSICS
```


## Implementation Steps

1. **Get Affected URLs**
   - Get all deltas and curated URLs that match pattern
   - For each URL determine what exists (delta only, both, or curated only)

2. **For Each Delta URL Found**
   - If no matching curated exists:
     - Set pattern's field to null
   - If matching curated exists:
     - Set pattern's field to curated value
     - If delta now matches curated exactly, delete delta

3. **For Each Curated URL without Delta**
   - Create new delta with pattern's field set to null

4. **Cleanup**
   - Clear pattern's relationships with URLs
   - Remove pattern from database

## Edge Cases to Handle

1. **Field Comparison**
   - When comparing delta to curated, ignore id and to_delete fields
   - All other fields must match exactly for delta deletion

2. **Manual Changes**
   - Preserve any delta fields not modified by this pattern
   - Only delete delta if ALL fields match curated

3. **Multiple Collections**
   - Only affect URLs in pattern's collection

4. **Invalid States**
   - Handle missing URLs gracefully
   - Skip URLs that no longer exist
