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
Curated: None
Delta: division=BIOLOGY (from pattern)
[Pattern removed]
Result: Delta remains with division=None
```

### Case 2: Delta and Curated Exist
**Scenario:**
- Both curated and delta URLs exist
- Pattern is removed
```
Curated: division=GENERAL
Delta: division=BIOLOGY (from pattern)
[Pattern removed]
Result: Delta reverts to curated value (division=GENERAL)
If delta now matches curated exactly, delta is deleted
```

### Case 3: Curated Only
**Scenario:**
- Only curated URL exists
- Pattern is removed
```
Curated: division=GENERAL
Delta: None
[Pattern removed]
Result: New delta created with division=None
```

### Case 4: Multiple Pattern Effects
**Scenario:**
- Delta has changes from multiple patterns
- One pattern is removed
```
Curated: division=GENERAL, doc_type=DOCUMENTATION
Delta: division=BIOLOGY, doc_type=DATA (from two patterns)
[Division pattern removed]
Result: Delta remains with division=GENERAL, doc_type=DATA preserved
```

### Case 5: Pattern Removal with Manual Changes
**Scenario:**
- Delta has both pattern effect and manual changes
- Pattern is removed
```
Curated: division=GENERAL, title="Original"
Delta: division=BIOLOGY, title="Modified" (pattern + manual)
[Pattern removed]
Result: Delta remains with division=GENERAL, title="Modified" preserved
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
