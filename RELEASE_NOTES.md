# COSMOS Release Notes
## Unreleased — `cosmos-rewiring` (Sinequa removal, crawl4ai + web-indexing hand-off)

Sinequa, the GitHub config push and XML generation are removed. Collections are now scraped by the
crawl4ai crawler (dispatched over SSM, results ingested from S3) and indexed by the `sde-api-scrapers`
`WEB_COSMOS` ECS task (curated export to S3, `ecs:RunTask`, status polled from S3). Six workflow
statuses are added (Scraping Successful/Failed, Test Indexing, Indexing Failed on Test/Prod,
Production Indexing). See `WORKFLOW.md` and `sde_collections/DEPLOYMENT.md`.

### Behaviour changes to be aware of
- **TDAMM classification threshold now takes effect.** `map_classification_to_tdamm_tags` previously
  accepted `threshold` and ignored it; it is now honoured (`inference/utils/classification_utils.py`).
  Inference is shipped disabled (`INFERENCE_ENABLED=False`); when re-enabled, collections will receive
  different TDAMM tags than earlier runs at the same `TDAMM_CLASSIFICATION_THRESHOLD`.
- **Orphaned workflow statuses.** `Secret Deployment Started` (8), `Ready for LRM Quality Check` (10),
  `Merge Pending` (17) and `Indexing Finished on Dev` (20) remain selectable but nothing advances them
  any more (the Sinequa/LRM steps that consumed them are gone). Collections currently parked in those
  statuses need to be moved by hand — audit them before/after deploying.
- Celery beat schedules for the two S3 pollers are DB rows written on `post_migrate`; their `enabled`
  flag is re-asserted from `SCRAPE_POLL_ENABLED` / `INDEX_POLL_ENABLED` on **every** `migrate`.
  Toggling a poller therefore requires `manage.py migrate`, not just a restart.
- Status-triggered Celery tasks are now enqueued with `transaction.on_commit`.
- A failed re-scrape (`Re-Indexing Needed`) no longer rewrites the collection's live workflow status;
  it clears the reindexing request and posts a Slack alert instead.

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
- Expanded from 92 manual datasets to 1063 ML-classified NASA CMR records
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
