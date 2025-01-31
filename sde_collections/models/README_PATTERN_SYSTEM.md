# Understanding the Pattern System

## Overview
The pattern system is designed to manage and track changes to URLs in a content curation workflow. It provides a way to systematically modify, exclude, or categorize URLs while maintaining a clear separation between work-in-progress changes (Delta URLs) and production content (Curated URLs).

## Core Concepts

### URL States
- **Curated URLs**: Production-ready, approved content
- **Delta URLs**: Work-in-progress changes, additions, or deletions to curated content
- **Dump URLs**: Raw content from the dev server

### Pattern Types
1. **Exclude Patterns**: Mark URLs for exclusion from the collection
2. **Include Patterns**: Explicitly include URLs in the collection
3. **Title Patterns**: Change or modify the original title
4. **Document Type Patterns**: Assign document type classifications
5. **Division Patterns**: Assign SMD division

## Pattern Lifecycle

### 1. Pattern Creation & Application
When a new pattern is created:
1. System identifies all matching URLs based on the pattern criteria
2. For matching Curated URLs:
   - If the pattern would change the URL's properties
   - And no Delta URL exists → Create a Delta URL with the changes
   - If Delta URL exists → Update it with additional changes
3. For matching Delta URLs:
   - Apply the pattern's effects directly


### 2. Pattern Effects
- Each pattern type has specific effects:
  - Exclude: Sets exclusion status
  - Include: Clears exclusion status
  - Title: Modifies scraped title
  - Document Type: Sets document classification
  - Division: Sets organizational division

### 3. Delta URL Generation Rules
Delta URLs are created when:
1. A new pattern would modify a Curated URL
2. An existing pattern effecting a Curated URL is removed, requiring reversal of its effects
3. Reindexed content in DumpUrl differs from Curated content

Delta URLs are not created when:
1. Pattern effects match current Curated URL state
2. Reindexed content matches Curated content

### 4. Pattern Removal
When a pattern is deleted:
1. System identifies all URLs affected by the pattern
2. For each affected Curated URL:
   - Create Delta URL to reverse effects
3. For affected Delta URLs:
   - Remove pattern's effects
   - If other patterns still affect it → Keep with updated state
   - If Delta URL becomes identical to Curated URL → Delete Delta URL

## Working Principles

### 1. Idempotency
- Applying the same pattern multiple times should have the same effect as applying it once
- System tracks pattern effects to ensure consistency
- Multiple patterns can affect the same URL

### 2. Separation of Concerns
- Pattern effects on Delta URLs don't directly affect Curated URLs
- Exclusion status tracked separately for Delta and Curated URLs
- Changes only propagate to Curated URLs during promotion

### 3. Change Tracking
- System maintains relationships between patterns and affected URLs
- Each pattern's effects are tracked separately
- Changes can be reversed if patterns are removed

### 4. Delta URL Lifecycle
1. Creation:
   - When patterns would modify Curated URLs
   - When DumpUrl content differs from Curated content
   - When patterns are removed and effects on CuratedUrls need reversal

2. Updates:
   - When new patterns affect the URL
   - When pattern effects change
   - When source content changes

3. Deletion:
   - When identical to Curated URL with no pattern effects
   - When explicitly marked for deletion
   - During promotion to Curated status

## Pattern Interaction Examples

### Scenario 1: Multiple Patterns
- Pattern A excludes URLs containing "draft"
- Pattern B sets document type for URLs containing "spec"
- URL: "example.com/draft-spec"
- Result: URL is excluded, document type is set (both patterns apply)

### Scenario 2: Pattern Removal
- Pattern sets custom title for URLs
- URLs have custom titles in production
- Pattern is deleted
- Result: Delta URLs created to restore original titles

### Scenario 3: Conflicting Patterns
- Pattern A includes URLs containing "docs"
- Pattern B excludes URLs containing "internal"
- URL: "example.com/docs/internal"
- Result: Url is included - Includes always take precedence
