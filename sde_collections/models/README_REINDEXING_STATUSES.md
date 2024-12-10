# Reindexing Status Documentation

### Reindexing Not Needed
- Variable name: `REINDEXING_NOT_NEEDED` (1)
- Default status for new collections
- Applied to collections in early workflow stages (research, engineering, etc.)

### Reindexing Needed on LRM Dev
- Variable name: `REINDEXING_NEEDED_ON_DEV` (2)
- Indicates collections that need to be reindexed on LRM Dev environment
- For collections that have already been indexed on production

### Reindexing Finished on LRM Dev
- Variable name: `REINDEXING_FINISHED_ON_DEV` (3)
- For collections that have completed reindexing on LRM Dev
- Currently managed manually by LRM team via admin interface

### Ready for Curation
- Variable name: `REINDEXING_READY_FOR_CURATION` (4)
- Automatically set when:
  - A collection's dump URLs are migrated to delta URLs AND there are curated URLs present
  - Triggered by Collection.migrate_dump_to_delta() method

### Curated
- Variable name: `REINDEXING_CURATED` (5)
- Automatically set when:
  - Delta URLs are promoted to curated URLs AND there are curated URLs present
  - Triggered by Collection.promote_to_curated() method

### Indexed on Prod
- Variable name: `REINDEXING_INDEXED_ON_PROD` (6)
- Currently managed manually via command line
- Future: Will be set automatically via plugin ping

### Key Code Locations for Automatic Changes

1. In migrate_dump_to_delta():
```python
# After migrating, check if we should update reindexing status
curated_urls_count = self.curated_urls.count()
if curated_urls_count > 0:
    self.reindexing_status = ReindexingStatusChoices.REINDEXING_READY_FOR_CURATION
    self.save()
```

2. In promote_to_curated():
```python
# After promoting, check if we should update reindexing status
curated_urls_count = self.curated_urls.count()
if curated_urls_count > 0:
    self.reindexing_status = ReindexingStatusChoices.REINDEXING_CURATED
    self.save()
```

Note: All status changes are logged in the ReindexingHistory model for tracking purposes.
