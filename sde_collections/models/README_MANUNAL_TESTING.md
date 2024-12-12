# COSMOS Curation System Testing Guide

## Resources
There are 14 collections which have been reindexed on dev and can have their statuses changed to `REINDEXING_FINISHED` to test url importing. The collections and their counts can be seen [here](https://docs.google.com/spreadsheets/d/1mJFqZXdIyAN8LTuVQMLRDuNgzm7GIMlYb_cPUtLKSCM/edit?gid=1316450061#gid=1316450061 ).

## Test Flow 1: Basic URL Collection Lifecycle

### Objective
Verify the complete lifecycle of a URL collection from initial creation through curation to production.

### Prerequisites
- Access to dev environment
- Test collection created
- Sample URLs ready for testing

### Test Cases

#### 1.1 Collection Status Progression
1. Create new collection in `RESEARCH_IN_PROGRESS` status
2. Verify initial scraper and indexer configs are created when moved to `READY_FOR_ENGINEERING`
3. Progress through `ENGINEERING_IN_PROGRESS` to `INDEXING_FINISHED_ON_DEV`
4. Confirm full text fetch triggers automatically
5. Verify status updates to `READY_FOR_CURATION`
6. Check plugin config creation
7. Move through `CURATION_IN_PROGRESS` to `CURATED`
8. Verify DeltaUrls promotion to CuratedUrls
9. Test quality check status changes (`QUALITY_CHECK_PERFECT/MINOR`)
10. Confirm collection appears in public query after PR merge

#### 1.2 Data State Transitions
1. Verify DumpUrls are created during indexing
2. Test migration from DumpUrls to DeltaUrls
3. Confirm field preservation during transitions
4. Check promotion from DeltaUrls to CuratedUrls
5. Verify all metadata transfers correctly

Expected Results:
- Each status transition triggers appropriate automated actions
- Data integrity maintained through all transitions
- Correct config generation at each stage
- Proper public visibility after final approval

## Test Flow 2: Pattern System Functionality

### Objective
Test the creation, application, and interaction of different pattern types.

### Prerequisites
- Collection with sample URLs
- Mix of different URL types and structures

### Test Cases

#### 2.1 Include/Exclude Patterns
1. Create exclude pattern for specific directory
   ```python
   pattern = "https://example.com/internal/*"
   ```
2. Create include pattern for specific file within excluded directory
   ```python
   pattern = "https://example.com/internal/public-doc.html"
   ```
3. Verify include pattern overrides exclude pattern
4. Test wildcard pattern matching
5. Check pattern precedence rules

#### 2.2 Modification Patterns
1. Create overlapping title patterns:
   ```python
   pattern1 = "*/docs/* → title='Documentation'"
   pattern2 = "*/docs/api/* → title='API Reference'"
   ```
2. Create division patterns with different specificity
3. Test document type patterns with wildcards
4. Verify "smallest set priority" resolution
5. Check pattern application during migrations

#### 2.3 Pattern Removal Scenarios
1. Test removing pattern affecting only Delta URLs
2. Remove pattern affecting Curated URLs
3. Verify handling of multiple pattern effects
4. Test manual change preservation
5. Check cleanup procedures

Expected Results:
- Pattern precedence rules correctly applied
- Proper handling of overlapping patterns
- Manual changes preserved during pattern operations
- Correct reversal of pattern effects on removal

## Test Flow 3: Reindexing Workflow

### Objective
Verify the reindexing process and status management.

### Prerequisites
- Existing collection in production
- Access to both dev and prod environments

### Test Cases

#### 3.1 Reindexing Status Progression
1. Change status from `REINDEXING_NOT_NEEDED` to `REINDEXING_NEEDED_ON_DEV`
2. Complete reindexing and update to `REINDEXING_FINISHED_ON_DEV`
3. Verify automatic full text fetch
4. Confirm status update to `REINDEXING_READY_FOR_CURATION`
5. Progress through `REINDEXING_CURATED`
6. Final update to `REINDEXING_INDEXED_ON_PROD`

#### 3.2 Data Handling During Reindex
1. Verify existing DumpUrls are cleared
2. Check new full text data processing
3. Test DumpUrl to DeltaUrl migration
4. Verify pattern reapplication
5. Confirm CuratedUrl updates

Expected Results:
- Proper status progression through reindexing
- Data integrity maintained
- Patterns correctly reapplied
- Existing customizations preserved

## Edge Cases and Stress Testing

### URL Pattern Edge Cases
1. Test URLs with/without trailing slashes
2. Verify handling of overlapping wildcards
3. Check pattern resolution with equal URL count matches
4. Test maximum pattern chain depth
5. Verify handling of malformed URLs

### Status Transition Edge Cases
1. Test interrupted transitions
2. Verify handling of failed automated actions
3. Check concurrent status updates
4. Test invalid status progressions
5. Verify recovery procedures

### Data Volume Testing
1. Test with large number of URLs (>100k)
2. Check pattern application performance
3. Verify migration speed with large datasets
4. Test memory usage during bulk operations
5. Check system response under heavy concurrent access

## Common Issues to Watch For

1. Pattern Precedence
   - Multiple patterns affecting same URL
   - Include/exclude pattern conflicts
   - Resolution of equal-specificity patterns

2. Data Integrity
   - Field preservation during transitions
   - Manual change retention
   - Pattern effect tracking

3. Performance
   - Large collection handling
   - Multiple pattern application
   - Status transition timing

4. Status Management
   - Automated trigger reliability
   - Status update race conditions
   - Recovery from failed transitions
