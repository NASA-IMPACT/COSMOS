# URL Migration, Classification, and Promotion Guide

## Overview
This document explains the lifecycle of URLs in the system, focusing on these critical processes:
1. Migration from DumpUrls to DeltaUrls
2. Classification of URLs for metadata enrichment
3. Promotion from DeltaUrls to CuratedUrls

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
- TDAMM Tags
- Any additional metadata

## Classification Process

### Overview
The classification process analyzes content to automatically add metadata, including:
- TDAMM tags for Astrophysics content
- Division classification for General content

Classification is optional and is gated on the `INFERENCE_ENABLED` setting, which
defaults to `False`. The inference pipeline is currently dormant, so in the default
configuration no classification stage runs at all.

### When Classification Happens
Classification, when enabled, occurs after DumpUrls are created but before they are migrated to DeltaUrls:
1. DumpUrls are created from scraped content
2. `Collection.queue_necessary_classifications()` is called
3. If `INFERENCE_ENABLED` is `False`, migration is queued immediately and steps 4–6 are skipped
4. Classification models analyze DumpUrl content
5. Classification results are applied to DumpUrls
6. DumpUrls (with enhanced metadata) are migrated to DeltaUrls

### Classification Types
- **TDAMM Classification**: Applied to Astrophysics collections to tag content related to multi-messenger astronomy
- **Division Classification**: Applied to General collections to suggest appropriate divisions

### Classification Flow
1. If `INFERENCE_ENABLED` is `False`, immediately queue `migrate_dump_to_delta_and_handle_status_transistions` and stop
2. Check if collection needs classification based on its configuration
3. Queue appropriate classification jobs; collections needing none go straight to migration
4. Process classifications asynchronously
5. Apply classification results to DumpUrls
6. Initiate migration to DeltaUrls once all classifications complete

## Pattern Application

### When Patterns Are Applied
Patterns are applied in two scenarios:
1. During migration from Dump to Delta (after classifications are complete, if any ran)
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
- New content is scraped (and classified, if `INFERENCE_ENABLED` is on)
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

#### Example 1: Basic Migration with Classification
A DumpUrl is created, classified, and then migrated to a DeltaUrl.
```python
# Starting State
dump_url = DumpUrl(
    url="example.com/doc",
    scraped_title="Original Title",
    document_type=DocumentTypes.DOCUMENTATION,
    tdamm_tag=None
)

# After Classification
dump_url = DumpUrl(
    url="example.com/doc",
    scraped_title="Original Title",
    document_type=DocumentTypes.DOCUMENTATION,
    tdamm_tag=["MMA_O_BH", "MMA_O_BH_AGN"]  # Applied by classification
)

# After Migration
delta_url = DeltaUrl(
    url="example.com/doc",
    scraped_title="Original Title",
    document_type=DocumentTypes.DOCUMENTATION,
    tdamm_tag=["MMA_O_BH", "MMA_O_BH_AGN"],  # Preserved from classification
    to_delete=False
)
```

#### Example 2: Migration with Existing Curated
If a CuratedUrl exists and the classified DumpUrl has changes, a DeltaUrl will be created.
```python
# Starting State
dump_url = DumpUrl(
    url="example.com/doc",
    scraped_title="New Title",
    document_type=DocumentTypes.ASTROPHYSICS,
    tdamm_tag=None
)

# After Classification
dump_url = DumpUrl(
    url="example.com/doc",
    scraped_title="New Title",
    document_type=DocumentTypes.ASTROPHYSICS,
    tdamm_tag=["MMA_O_BH"]  # Applied by classification
)

curated_url = CuratedUrl(
    url="example.com/doc",
    scraped_title="Old Title",
    document_type=DocumentTypes.ASTROPHYSICS,
    tdamm_tag=None
)

# After Migration
delta_url = DeltaUrl(
    url="example.com/doc",
    scraped_title="New Title",  # Different from curated
    document_type=DocumentTypes.ASTROPHYSICS,
    tdamm_tag=["MMA_O_BH"],  # Different from curated (null)
    to_delete=False
)

curated_url = CuratedUrl(
    url="example.com/doc",
    scraped_title="Old Title",
    document_type=DocumentTypes.ASTROPHYSICS,
    tdamm_tag=None
)
```

#### Example 3: Migration with Pattern Application
If a pattern exists that modifies the document type of a DumpUrl, that pattern will be applied and the DeltaUrl will reflect the pattern's changes.
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
Promotion moves DeltaUrls to CuratedUrls, carrying forward all changes including pattern-applied modifications and classification results. This occurs when:
- A curator marks a collection as Curated

### Steps
1. Process each DeltaUrl:
   - If marked for deletion: Remove matching CuratedUrl
   - Otherwise: Update/create CuratedUrl with ALL fields
2. Clear all DeltaUrls
3. Update pattern relationship tracking

### Examples

#### Example 1: Basic Promotion
If there ae no CuratedUrls for the URL, the DeltaUrl will be promoted to a new CuratedUrl.
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
It's important to notice that the None value in the DeltaUrl is preserved in the CuratedUrl.
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
If there is no DumpUrl for an existing CuratedUrl, this signifies the url has been removed from the collection. A DeltaUrl with `to_delete=True` will be created, and on promotion the CuratedUrl will be deleted.
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
- Classification-set values are preserved through the entire lifecycle
- Pattern-set values take precedence over original values

### Classification Behavior
- Classifications only run when `INFERENCE_ENABLED` is on; with the flag off (the default) migration runs immediately after the DumpUrls are created
- Classifications only run on DumpUrls before migration to DeltaUrls
- Classification results become regular field values and persist through promotion
- When classifications are queued, migration to DeltaUrls waits for all of them to complete

### Pattern Behavior
- Patterns only apply during migration or when patterns themselves are created/updated
- Pattern effects are preserved during promotion as regular field values
- Patterns are NOT re-applied during promotion. This means you can't add a DeltaUrl outside of the migration process and expect patterns to apply. In this case, you would need to either add it as a DumpUrl and migrate it correctly, or add it as a DeltaUrl manually apply the pattern.
