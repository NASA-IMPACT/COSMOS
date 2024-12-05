# URL Include and Exclude Patterns

## Overview

The pattern system allows you to control which URLs are included in or excluded from your collection using two types of patterns:
- **Exclude Patterns**: Mark URLs for exclusion from the collection
- **Include Patterns**: Explicitly include URLs, overriding any exclude patterns

## Pattern Types

### Individual URL Patterns
- Matches exact URLs
- Best for targeting specific pages
- No wildcards allowed
```python
# Matches only exactly this URL
match_pattern = "https://example.com/docs/specific-page.html"
```

### Multi-URL (Wildcard) Patterns
- Uses `*` as a wildcard to match multiple URLs
- Best for targeting entire directories or file types
- Can have wildcards anywhere in the pattern
```python
# Matches all files in the /docs directory
match_pattern = "https://example.com/docs/*"

# Matches all PDF files
match_pattern = "https://example.com/*.pdf"
```

## Pattern Precedence

1. Include patterns **always** take precedence over exclude patterns
2. More specific patterns take precedence over general patterns
3. If a URL matches both an include and exclude pattern, it will be included

## Common Examples

### Excluding a Directory But Including Specific Files

```python
# Exclude the internal docs directory
DeltaExcludePattern.objects.create(
    collection=collection,
    match_pattern="https://example.com/internal/*",
    match_pattern_type=2  # Multi-URL pattern
)

# But include specific approved pages
DeltaIncludePattern.objects.create(
    collection=collection,
    match_pattern="https://example.com/internal/public-roadmap.html",
    match_pattern_type=1  # Individual URL pattern
)
```

### Including Only Specific File Types

```python
# Exclude everything in docs directory
DeltaExcludePattern.objects.create(
    collection=collection,
    match_pattern="https://example.com/docs/*",
    match_pattern_type=2
)

# Include only PDF files
DeltaIncludePattern.objects.create(
    collection=collection,
    match_pattern="https://example.com/docs/*.pdf",
    match_pattern_type=2
)
```

### Folder-Based Access Control

```python
# Exclude all draft documents
DeltaExcludePattern.objects.create(
    collection=collection,
    match_pattern="https://example.com/docs/drafts/*",
    match_pattern_type=2
)

# Include the approved drafts subfolder
DeltaIncludePattern.objects.create(
    collection=collection,
    match_pattern="https://example.com/docs/drafts/approved/*",
    match_pattern_type=2
)
```

## Best Practices

1. **Start Specific**: Begin with specific patterns and broaden as needed
   ```python
   # Better
   match_pattern = "https://example.com/docs/api/v1/*"
   # Less precise
   match_pattern = "https://example.com/docs/*"
   ```

2. **Use Include for Exceptions**: When excluding a large section, use include patterns for exceptions
   ```python
   # Exclude staging environment
   exclude_pattern = "https://staging.example.com/*"
   # Include specific staging features that should be public
   include_pattern = "https://staging.example.com/features/released/*"
   ```

3. **Document Patterns**: Keep track of why each pattern was added
   ```python
   DeltaExcludePattern.objects.create(
       collection=collection,
       match_pattern="https://example.com/internal/*",
       reason="Internal documentation not ready for public release"
   )
   ```

4. **Regular Maintenance**: Review patterns periodically to ensure they're still needed and correct

## Common Gotchas

1. **Trailing Slashes**: URLs with and without trailing slashes are treated as different
   ```python
   # These are different patterns
   "https://example.com/docs"
   "https://example.com/docs/"
   ```

2. **Over-Inclusive Wildcards**: Be careful with patterns that might match too much
   ```python
   # Dangerous: Could match more than intended
   match_pattern = "https://example.com/*internal*"

   # Better: More specific
   match_pattern = "https://example.com/internal/*"
   ```

3. **Pattern Order**: Remember that include patterns always win, regardless of the order they're created
   ```python
   # This URL will be included despite the exclude pattern
   exclude_pattern = "https://example.com/docs/*"
   include_pattern = "https://example.com/docs/public.html"
   ```
