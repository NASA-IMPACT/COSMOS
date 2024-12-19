# COSMOS Release Notes
## v3.0.0 from v2.0.1

COSMOS v3.0.0 introduces several major architectural changes that fundamentally enhance the system's capabilities. The primary feature is a new website reindexing system that allows COSMOS to stay up-to-date with source website changes, addressing a key limitation of previous versions where websites could only be scraped once. This release includes comprehensive updates to the data models, frontend interface, rule creation system, and backend processing along with some bugfixes from v2.0.1.

The Environmental Justice (EJ) system has been significantly expanded, growing less than 100 manually curated datasets to approximately 1,000 datasets through the integration of machine learning classification of NASA CMR records. This expansion is supported by a new modular processing suite that generates and extracts metadata using Subject Matter Expert (SME) criteria.

To support future machine learning integration, COSMOS now implements a sophisticated two-column system that allows fields to maintain both ML-generated classifications and manual curator overrides. This system has been seamlessly integrated into the data models, serializers, and APIs, ensuring that both automated and human-curated data can coexist while maintaining clear precedence rules.

To ensure reliability and maintainability of these major changes, this release includes extensive testing coverage with 213 new tests spanning URL processing, pattern management, Environmental Justice functionality, workflow triggers, and data migrations. Additionally, we've added comprehensive documentation across 15 new README files that cover everything from fundamental pattern system concepts to detailed API specifications and ML integration guidelines.


### Major Features

#### Reindexing System
- **New Data Models**: Introduced DumpUrl, DeltaUrl, and CuratedUrl to support the reindexing workflow
- **Automated Workflows**:
  - New process to calculate deltas, deletions, and additions during migration
  - Automatic promotion of DeltaUrls to CuratedUrls
  - Status-based triggers for data ingestion and processing
- **Duplicate Prevention**: System now prevents duplicate patterns and URLs
- **Enhanced Frontend**:
  - Added reindexing status column to collection and URL list pages
  - New deletion tracking column on URL list page
  - Updated collection list to display delta URL counts
  - Improved URL list page accessibility via delta URL count

#### Pattern System Improvements
- Complete modularization of the pattern system
- Enhanced handling of edge cases including overlapping patterns
- Improved unapply logic
- Functional inclusion rules
- Pattern precedence system: most specific pattern takes priority, with pattern length as tiebreaker

#### Environmental Justice (EJ) Enhancement
- Expanded from 89 manual datasets to 1063 ML-classified NASA CMR records
- New modular processing suite for metadata generation
- Enhanced API with multiple data sources:
  - Spreadsheet (original manual classifications)
  - ML Production
  - ML Testing
  - Combined (ML production with spreadsheet overrides)
- Custom processing suite for CMR metadata extraction

#### Infrastructure Updates
- Streamlined database backup and restore
- Optimized Docker builds
- Fixed LetsEncrypt staging issues
- Modified Traefik timeouts for long-running jobs
- Updated Sinequa worker configuration:
  - Reduced worker count to 3 for neural workload optimization
  - Added neural indexing to all webcrawlers
  - Removed deprecated version mappings

#### API Enhancements
- New endpoints for curated and delta URLs:
  - GET /curated-urls-api/<str:config_folder>/
  - GET /delta-urls-api/<str:config_folder>/
- Backwards compatibility through remapped CandidateUrl endpoint
- Updated Environmental Justice API with new data source parameter

### Technical Improvements

#### Two-Column System
- New architecture to support dual ML/manual classifications
- Seamless integration with models, serializers, and APIs
- Prioritization system for manual overrides

#### Testing
Added 213 new tests across multiple areas:
- URL APIs and processing (19 tests)
- Delta and pattern management (31 tests)
- Environmental Justice API (7 tests)
- Environmental Justice Mappings and Thresholding (58)
- Workflow and status triggers (10 tests)
- Migration and promotion processes (31 tests)
- Field modifications and TDAMM tags (25 tests)
- Additional system functionality (30 tests)


#### Documentation
Added comprehensive documentation across 15 READMEs covering:
- Pattern system fundamentals and examples
- Reindexing statuses and triggers
- Model lifecycles and testing procedures
- URL inclusion/exclusion logic
- Environmental Justice classifier and API
- ML column functionality
- SQL dump restoration

### Bug Fixes
- Fixed non-functional includes
- Resolved pagination issues for patterns (previously limited to 50)
- Eliminated ability to create duplicate URLs and patterns
- Corrected faulty unapply logic for modification patterns
- Fixed unrepeatable logic for overlapping patterns
- Allowed long running jobs to complete without timeouts

### UI Updates
- Renamed application from "SDE Indexing Helper" to "COSMOS"
- Refactored collection list code for easier column management
- Enhanced URL list page with new status and deletion tracking
- Improved navigation through delta URL count integration

### Administrative Changes
- Added new admin panels for enhanced system management
- Updated installation requirements
- Enhanced database backup and restore functionality
