# URL Migration and Promotion Guide

## Overview
This document explains the lifecycle of URLs in the system, focusing on two critical processes:
1. Migration from DumpUrls to DeltaUrls
2. Promotion from DeltaUrls to CuratedUrls

## Core Concepts

### URL States
- **DumpUrls**: Raw data from initial scraping/indexing
- **DeltaUrls**: Work-in-progress changes and modifications
- **CuratedUrls**: Production-ready, approved content

### Fields That Transfer
All fields transfer between states, including:
- URL
- Scraped Title
- Generated Title
- Document Type
- Division
- Excluded Status
- Scraped Text
- Any additional metadata

## Pattern Application

### When Patterns Are Applied
Patterns are applied in two scenarios:
1. During migration from Dump to Delta
2. When a new pattern is created/updated

Patterns are NOT applied during promotion. The effects of patterns (modified titles, document types, etc.) are carried through to CuratedUrls during promotion, but the patterns themselves don't reapply.

### Pattern Effects
- Patterns modify DeltaUrls when they are created or when DeltaUrls are created through migration
- Pattern-modified fields (titles, document types, etc.) become part of the DeltaUrl's data
- These modifications persist through promotion to CuratedUrls
- Pattern relationships (which patterns affect which URLs) are maintained for tracking purposes

## Migration Process (Dump → Delta)

### Overview
Migration converts DumpUrls to DeltaUrls, preserving all fields and applying patterns. This process happens when:
- New content is scraped
- Content is reindexed
- Collection is being prepared for curation

### Steps
1. Clear existing DeltaUrls
2. Process each DumpUrl:
   - If matching CuratedUrl exists: Create Delta with all fields
   - If no matching CuratedUrl: Create Delta as new URL
3. Process missing CuratedUrls:
   - Create deletion Deltas for any not in Dump
4. Apply all patterns to new Deltas
5. Clear DumpUrls

### Examples

#### Example 1: Migration with Pattern Application
```python
# Starting State
dump_url = DumpUrl(
    url="example.com/data/file.pdf",
    scraped_title="Data File",
    document_type=None
)

document_type_pattern = DocumentTypePattern(
    match_pattern="*.pdf",
    document_type=DocumentTypes.DATA
)

# After Migration and Pattern Application
delta_url = DeltaUrl(
    url="example.com/data/file.pdf",
    scraped_title="Data File",
    document_type=DocumentTypes.DATA,  # Set by pattern
    to_delete=False
)
```

## Promotion Process (Delta → Curated)

### Overview
Promotion moves DeltaUrls to CuratedUrls, carrying forward all changes including pattern-applied modifications. This occurs when:
- A curator marks a collection as Curated

### Steps
1. Process each DeltaUrl:
   - If marked for deletion: Remove matching CuratedUrl
   - Otherwise: Update/create CuratedUrl with ALL fields
2. Clear all DeltaUrls
3. Update pattern relationship tracking

### Examples

#### Example 1: Basic Promotion
```python
# Starting State
delta_url = DeltaUrl(
    url="example.com/doc",
    scraped_title="New Title",
    document_type=DocumentTypes.DOCUMENTATION,
    to_delete=False
)

# After Promotion
curated_url = CuratedUrl(
    url="example.com/doc",
    scraped_title="New Title",
    document_type=DocumentTypes.DOCUMENTATION
)
```

#### Example 2: Promotion with NULL Override
```python
# Starting State
delta_url = DeltaUrl(
    url="example.com/doc",
    scraped_title="Title",
    document_type=None,  # Explicitly set to None by pattern
    to_delete=False
)

curated_url = CuratedUrl(
    url="example.com/doc",
    scraped_title="Title",
    document_type=DocumentTypes.DOCUMENTATION
)

# After Promotion
curated_url = CuratedUrl(
    url="example.com/doc",
    scraped_title="Title",
    document_type=None  # NULL value preserved
)
```

#### Example 3: Deletion During Promotion
```python
# Starting State
delta_url = DeltaUrl(
    url="example.com/old-doc",
    scraped_title="Old Title",
    to_delete=True
)

curated_url = CuratedUrl(
    url="example.com/old-doc",
    scraped_title="Old Title"
)

# After Promotion
# CuratedUrl is deleted
# DeltaUrl is cleared
```

## Important Notes


### Field Handling
- ALL fields are copied during migration and promotion
- NULL values in DeltaUrls are treated as explicit values
- Pattern-set values take precedence over original values

### Pattern Behavior
- Patterns only apply during migration or when patterns themselves are created/updated
- Pattern effects are preserved during promotion as regular field values
- Patterns are NOT re-applied during promotion. This means you can't add a DeltaUrl outside of the migration process and expect patterns to apply. In this case, you would need to either add it as a DumpUrl and migrate it correctly, or add it as a DeltaUrl manually apply the pattern.
