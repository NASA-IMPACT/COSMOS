# Pattern Resolution System

## Overview
The pattern system uses a "smallest set priority" strategy for resolving conflicts between overlapping patterns. This applies to title patterns, division patterns, and document type patterns. The pattern that matches the smallest set of URLs takes precedence.

## How It Works
When multiple patterns match a URL, the system:
1. Counts how many total URLs each pattern matches
2. Compares the counts
3. Applies the pattern that matches the fewest URLs

### Example Pattern Hierarchy
```
Pattern A: */docs/*          # Matches 100 URLs
Pattern B: */docs/api/*      # Matches 20 URLs
Pattern C: */docs/api/v2/*   # Matches 5 URLs

Example URLs and Which Patterns Apply:
1. https://example.com/docs/overview.html
   ✓ Matches Pattern A
   ✗ Doesn't match Pattern B or C
   Result: Pattern A applies (only match)

2. https://example.com/docs/api/endpoints.html
   ✓ Matches Pattern A
   ✓ Matches Pattern B
   ✗ Doesn't match Pattern C
   Result: Pattern B applies (20 < 100 URLs)

3. https://example.com/docs/api/v2/users.html
   ✓ Matches Pattern A
   ✓ Matches Pattern B
   ✓ Matches Pattern C
   Result: Pattern C applies (5 < 20 < 100 URLs)
```

## Pattern Types and Resolution

### Title Patterns
```
Patterns:
A: */docs/* → title="Documentation"           # Matches 100 URLs
B: */docs/api/* → title="API Reference"       # Matches 20 URLs
C: */docs/api/v2/* → title="V2 API Guide"     # Matches 5 URLs

Example URLs:
1. https://example.com/docs/getting-started.html
   • Matches: Pattern A
   • Result: title="Documentation"

2. https://example.com/docs/api/authentication.html
   • Matches: Patterns A, B
   • Result: title="API Reference"

3. https://example.com/docs/api/v2/oauth.html
   • Matches: Patterns A, B, C
   • Result: title="V2 API Guide"
```

### Division Patterns
```
Patterns:
A: *.pdf → division="GENERAL"                 # Matches 500 URLs
B: */specs/*.pdf → division="ENGINEERING"     # Matches 50 URLs
C: */specs/2024/*.pdf → division="RESEARCH"   # Matches 10 URLs

Example URLs:
1. https://example.com/docs/report.pdf
   • Matches: Pattern A
   • Result: division="GENERAL"

2. https://example.com/specs/architecture.pdf
   • Matches: Patterns A, B
   • Result: division="ENGINEERING"

3. https://example.com/specs/2024/roadmap.pdf
   • Matches: Patterns A, B, C
   • Result: division="RESEARCH"
```

### Document Type Patterns
```
Patterns:
A: */docs/* → type="DOCUMENTATION"            # Matches 200 URLs
B: */docs/data/* → type="DATA"                # Matches 30 URLs
C: */docs/data/schemas/* → type="SCHEMA"      # Matches 8 URLs

Example URLs:
1. https://example.com/docs/guide.html
   • Matches: Pattern A
   • Result: type="DOCUMENTATION"

2. https://example.com/docs/data/metrics.json
   • Matches: Patterns A, B
   • Result: type="DATA"

3. https://example.com/docs/data/schemas/user.json
   • Matches: Patterns A, B, C
   • Result: type="SCHEMA"
```

## Special Cases

### Mixed Pattern Types
```
When different pattern types overlap, each is resolved independently:

URL: https://example.com/docs/api/v2/schema.json
Matching Patterns:
1. */docs/* → title="Documentation", 100 matches
2. */docs/* → doc_type="DOCUMENTATION", 100 matches
3. */docs/api/* → title="API Reference", 50 matches
4. */docs/api/v2/* → division="ENGINEERING", 10 matches
5. */docs/api/v2/*.json → doc_type="DATA", 3 matches

Final Result:
• title="API Reference" (from pattern 3, most specific title pattern)
• division="ENGINEERING" (from pattern 4, only matching division pattern)
• doc_type="DATA" (from pattern 5, most specific doc_type pattern)
```
