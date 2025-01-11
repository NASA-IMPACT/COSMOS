# URL Pattern Management System

## Overview
This system provides a framework for managing and curating collections of URLs through pattern-based rules. It enables systematic modification, categorization, and filtering of URLs while maintaining a clear separation between work-in-progress changes and production content.

## Core Concepts

### URL States
Content progresses through three states:
- **Dump URLs**: Raw content from initial scraping/indexing
- **Delta URLs**: Work-in-progress changes and modifications
- **Curated URLs**: Production-ready, approved content

### Pattern Types
- **Include/Exclude Patterns**: Control which URLs are included in collections
  - Include patterns always override exclude patterns
  - Use wildcards for matching multiple URLs

- **Modification Patterns**: Change URL properties
  - Title patterns modify final titles shown in search results
  - Document type patterns affect which tab the URL appears under
  - Division patterns assign URLs within the Science Knowledge Sources

### Pattern Resolution
The system uses a "smallest set priority" strategy which resolves conflicts by always using the most specific pattern that matches a URL:
- Multiple patterns can match the same URL
- Pattern matching the smallest number of URLs takes precedence
- Applies to title, division, and document type patterns
- More specific patterns naturally override general ones

## Getting Started

To effectively understand this system, we recommend reading through the documentation in the following order:

1. Begin with the Pattern System Overview to learn the fundamental concepts of how patterns work and interact with URLs
2. Next, explore the URL Lifecycle documentation to understand how content moves through different states
3. The Pattern Resolution documentation will show you how the system handles overlapping patterns
4. Learn how to control which URLs appear in your collection with the Include/Exclude patterns guide
5. Finally, review the Pattern Unapplication Logic to understand how pattern removal affects your URLs

Each section builds upon knowledge from previous sections, providing a comprehensive understanding of the system.

## Documentation

[Pattern System Overview](./README_PATTERN_SYSTEM.md)
- Core concepts and pattern types
- Pattern lifecycle and effects
- Delta URL generation rules
- Working principles (idempotency, separation of concerns)
- Pattern interaction examples

[URL Lifecycle Management](./README_LIFECYCLE.md)
- Migration process (Dump → Delta)
- Promotion process (Delta → Curated)
- Field handling during transitions
- Pattern application timing
- Data integrity considerations

[Pattern Resolution](./README_PATTERN_RESOLUTION.md)
- Smallest set priority mechanism
- URL counting and precedence
- Performance considerations
- Edge case handling
- Implementation details

[URL Inclusion/Exclusion](./README_INCLUSION.md)
- Wildcard pattern matching
- Include/exclude precedence
- Example pattern configurations
- Best practices
- Common pitfalls and solutions

[Pattern Unapplication Logic](./README_UNAPPLY_LOGIC.md)
- Pattern removal handling
- Delta management during unapplication
- Manual change preservation
- Cleanup procedures
- Edge case handling
