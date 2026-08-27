# Reindexing Status Documentation

### Status Flow

The typical reindexing status flow is:

1. `REINDEXING_NOT_NEEDED` ("Re-Indexing Not Needed") → Default state
2. `REINDEXING_NEEDED_ON_DEV` ("Re-Indexing Needed") → When a re-scrape is required
3. `REINDEXING_FINISHED_ON_DEV` ("Re-Indexing Finished") → After the scrape results are ingested
4. `REINDEXING_READY_FOR_CURATION` ("Ready for Re-Curation") → After dump URLs are migrated
5. `REINDEXING_CURATION_IN_PROGRESS` ("Re-Curation in Progress") → During active re-curation
6. `REINDEXING_CURATED` ("Re-Curation Finished") → After re-curation is complete
7. `REINDEXING_INDEXED_ON_PROD` ("Re-Indexed on Prod") → After successful prod indexing

## Status Descriptions
### Reindexing Not Needed
- Variable name: `REINDEXING_NOT_NEEDED` (1)
- Default status for new collections
- Applied to collections in early workflow stages (research, engineering, etc.)

### Reindexing Needed
- Variable name: `REINDEXING_NEEDED_ON_DEV` (2)
- Indicates collections that need to be re-scraped
- For collections that have already been indexed on production
- Manually set by a curator or engineer; triggers `dispatch_scrape_job`, which sends the
  job to the crawl4ai host via SSM (the same dispatch/poll path as the initial workflow)

### Reindexing Finished
- Variable name: `REINDEXING_FINISHED_ON_DEV` (3)
- For collections whose re-scrape has completed and whose results have been claimed
- Set automatically by `ingest_scraped_collection` as its atomic compare-and-swap claim
  on the re-scrape path (`REINDEXING_NEEDED_ON_DEV` → `REINDEXING_FINISHED_ON_DEV`)
- This status deliberately triggers nothing: the ingest sets it, so a trigger here would
  double-fire

### Ready for Re-Curation
- Variable name: `REINDEXING_READY_FOR_CURATION` (4)
- Automatically set after a collection's dump URLs are migrated to delta URLs
- Set by the `migrate_dump_to_delta_and_handle_status_transistions` task, for collections
  that entered migration at `REINDEXING_FINISHED_ON_DEV`

### Re-Curation in Progress
- Variable name: `REINDEXING_CURATION_IN_PROGRESS` (5)
- Indicates that collection is actively being re-curated
- Manually set when curator begins re-curation work
- Transitions to `REINDEXING_CURATED` when re-curation is complete

### Re-Curation Finished
- Variable name: `REINDEXING_CURATED` (6)
- Manually set by the curator when re-curation is finished
- Setting it is what *triggers* promotion: the `handle_workflow_status_change` receiver
  calls `Collection.promote_to_curated()`, moving delta URLs to curated URLs

### Re-Indexed on Prod
- Variable name: `REINDEXING_INDEXED_ON_PROD` (7)
- Manually set by a dev after the collection has been indexed on prod

### Key Code Locations for Automatic Changes

1. In `ingest_scraped_collection()` (`sde_collections/tasks.py`) — the claim on the
   re-scrape path:
```python
claimed = Collection.objects.filter(
    id=collection_id,
    reindexing_status=ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV,
).update(reindexing_status=ReindexingStatusChoices.REINDEXING_FINISHED_ON_DEV)
```

2. In `migrate_dump_to_delta_and_handle_status_transistions()` (`sde_collections/tasks.py`):
```python
# Check reindexing status transition
if initial_reindexing_status == ReindexingStatusChoices.REINDEXING_FINISHED_ON_DEV:
    collection.reindexing_status = ReindexingStatusChoices.REINDEXING_READY_FOR_CURATION
    collection.save()
```

3. In `handle_workflow_status_change()` (`sde_collections/models/collection.py`) — the
   status set by the curator drives the action, not the other way around:
```python
if instance.reindexing_status == ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV:
    dispatch_scrape_job.delay(instance.id)
elif instance.reindexing_status == ReindexingStatusChoices.REINDEXING_CURATED:
    instance.promote_to_curated()
```

Note: Status changes made through `Collection.save()` are logged in the ReindexingHistory
model for tracking purposes. The ingest claim above is a queryset `.update()`, which
bypasses the `post_save` receiver and so is not recorded there.
