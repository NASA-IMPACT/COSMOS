## Overview
As of early 2025, we have only recently been writing tests for new features, and have about 250 tests in total, mostly centered around the EJ portal, the reindexing process, and pattern applications. 

Although this covers much of the core system logic, there still remain a number of untested logical areas such as the config file generation, core project settings, frontend features, etc.

This document outlines a testing strategy for the project, which will guide us towards adding tests in the most critical areas first, followed by a plan to fully cover the remaining areas.

## Current Coverage
Using the coverage library, the following report was generated:
Name      |                                                                                            Stmts |  Miss | Cover |  Missing
----------|--------------------------------------------------------------------------------------------------|-------|--------|--------
config/__init__.py  |                                                                                        2 |      0 |   100% |
config/celery_app.py  |                                                                                      6 |      0 |   100% |
config/settings/__init__.py  |                                                                               0 |      0 |   100% |
config/settings/base.py  |                                                                                  94 |      0 |   100% |
config/settings/local.py  |                                                                                 20 |     20 |     0% |   1-65
config/settings/production.py  |                                                                            48 |     48 |     0% |   1-162
config/urls.py  |                                                                                           14 |      4 |    71% |   26-47
config/wsgi.py  |                                                                                            8 |      8 |     0% |   17-36
config_generation/__init__.py  |                                                                             0 |      0 |   100% |
config_generation/api.py  |                                                                                 34 |     34 |     0% |   1-88
config_generation/config_example.py  |                                                                      15 |     15 |     0% |   1-69
config_generation/db_to_xml.py  |                                                                          203 |    133 |    34% |   45, 47, 50, 96, 119-125, 129-136, 142-149, 197-200, 206-214, 225-230, 242-271, 274-278, 285-292, 303-308, 311, 317, 326-332, 342-349, 361-368, 371-374, 377-378, 382-390, 393-399, 402-412, 415-429
config_generation/db_to_xml_file_based.py  |                                                                52 |     52 |     0% |   4-119
config_generation/delete_config_folders.py  |                                                               24 |     24 |     0% |   9-50
config_generation/delete_server_content.py  |                                                               12 |     12 |     0% |   3-25
config_generation/delete_webapp_collections.py  |                                                            5 |      5 |     0% |   6-12
config_generation/export_collections.py  |                                                                  36 |     36 |     0% |   1-73
config_generation/export_whole_index.py  |                                                                  28 |     28 |     0% |   1-58
config_generation/generate_collection_list.py  |                                                            29 |     29 |     0% |   8-69
config_generation/generate_commands.py  |                                                                   41 |     41 |     0% |   6-87
config_generation/generate_emac_indexer.py  |                                                               24 |     24 |     0% |   1-81
config_generation/generate_jobs.py  |                                                                       42 |     42 |     0% |   8-100
config_generation/generate_scrapers.py  |                                                                   15 |     15 |     0% |   2-54
config_generation/minimum_api.py  |                                                                         33 |     33 |     0% |   1-81
config_generation/preprocess_sources.py  |                                                                  25 |     25 |     0% |   1-50
config_generation/sources_to_scrape.py  |                                                                   28 |     28 |     0% |   2-1631
docs/__init__.py  |                                                                                          0 |      0 |   100% |
docs/conf.py  |                                                                                             17 |     17 |     0% |   13-62
environmental_justice/__init__.py  |                                                                         0 |      0 |   100% |
environmental_justice/admin.py  |                                                                            5 |      0 |   100% |
environmental_justice/apps.py  |                                                                             4 |      0 |   100% |
environmental_justice/models.py  |                                                                          29 |      1 |    97% |   44
environmental_justice/serializers.py  |                                                                      6 |      0 |   100% |
environmental_justice/views.py  |                                                                           23 |      0 |   100% |
feedback/__init__.py  |                                                                                      0 |      0 |   100% |
feedback/admin.py  |                                                                                        14 |      0 |   100% |
feedback/apps.py  |                                                                                          4 |      0 |   100% |
feedback/models.py  |                                                                                       42 |     15 |    64% |   20-29, 35-44, 61-63
feedback/serializers.py  |                                                                                  10 |      0 |   100% |
feedback/urls.py  |                                                                                          4 |      0 |   100% |
feedback/views.py  |                                                                                         9 |      0 |   100% |
manage.py  |                                                                                                16 |     16 |     0% |   2-31
merge_production_dotenvs_in_dotenv.py  |                                                                    15 |      1 |    93% |   26
scripts/ej/cmr_processing.py  |                                                                            241 |      5 |    98% |   160, 186-188, 397, 410
scripts/ej/config.py  |                                                                                      6 |      0 |   100% |
scripts/ej/test_cmr_processing.py  |                                                                       225 |      1 |    99% |   610
scripts/ej/test_threshold_processing.py  |                                                                  97 |      1 |    99% |   209
scripts/ej/threshold_processing.py  |                                                                       20 |      0 |   100% |
sde_collections/__init__.py  |                                                                               0 |      0 |   100% |
sde_collections/admin.py  |                                                                                212 |     72 |    66% |   22-24, 29, 34, 40-60, 65-81, 86-89, 98-101, 110-112, 120-134, 143, 148, 153, 158, 163, 168, 173, 178-189, 196-197, 260, 265, 270, 275, 302-303, 308-309, 314-316, 345-372, 478-480
sde_collections/apps.py  |                                                                                   4 |      0 |   100% |
sde_collections/forms.py  |                                                                                 15 |      0 |   100% |
sde_collections/management/commands/database_backup.py  |                                                   62 |      1 |    98% |   68
sde_collections/management/commands/database_restore.py  |                                                  83 |      8 |    90% |   34, 36, 87-89, 142-145
sde_collections/models/__init__.py  |                                                                        0 |      0 |   100% |
sde_collections/models/candidate_url.py  |                                                                  89 |     16 |    82% |   124, 128-134, 138-142, 145, 176-177
sde_collections/models/collection.py  |                                                                    414 |    144 |    65% |   241, 269, 277-287, 291-301, 305-315, 319-344, 348-357, 361, 365, 369-376, 380-387, 394, 403-406, 419, 436-439, 449-470, 478, 482-515, 519, 523, 527, 531-532, 536, 540-546, 550-553, 558-567, 575-617, 640, 679, 689, 703, 707-732, 765, 769-777, 785
sde_collections/models/collection_choice_fields.py  |                                                      138 |     20 |    86% |   14-17, 36-39, 56-59, 74-77, 168-171
sde_collections/models/delta_patterns.py  |                                                                313 |     33 |    89% |   119, 123, 139, 226-227, 263, 267, 291, 382-389, 439-449, 498, 503-506, 592, 627-641
sde_collections/models/delta_url.py  |                                                                      81 |     19 |    77% |   117-125, 129-135, 139-143, 146
sde_collections/models/pattern.py  |                                                                       145 |     79 |    46% |   40-48, 56-63, 66, 69, 73-74, 78-79, 87, 94-96, 105, 117-119, 128, 139-151, 163-205, 208-212, 215-216, 230-233, 243, 257-260, 268
sde_collections/serializers.py  |                                                                          191 |     47 |    75% |   80-81, 84-85, 88-89, 92-93, 129-130, 133-134, 137-138, 141-142, 197, 201, 211-214, 244-247, 257-260, 271, 274, 307-315, 335-343, 358-366
sde_collections/sinequa_api.py  |                                                                          102 |      3 |    97% |   65, 255, 289
sde_collections/tasks.py  |                                                                                119 |     67 |    44% |   25-67, 72-108, 113-117, 122-125, 130-148, 153-155, 215-216
sde_collections/urls.py  |                                                                                  17 |      0 |   100% |
sde_collections/utils/__init__.py  |                                                                         0 |      0 |   100% |
sde_collections/utils/bulk_github_push.py  |                                                                 8 |      8 |     0% |   7-22
sde_collections/utils/generate_deployment_message.py  |                                                      8 |      8 |     0% |   1-24
sde_collections/utils/github_helper.py  |                                                                  115 |     93 |    19% |   12-18, 30-42, 49-52, 60-68, 81-96, 104-110, 119-123, 127-129, 132-142, 145-152, 155-172, 175, 178-185, 189-192, 196-224, 227
sde_collections/utils/health_check.py  |                                                                   123 |    106 |    14% |   33-46, 51-57, 61-98, 102-143, 155-165, 172-187, 191-273
sde_collections/utils/paired_field_descriptor.py  |                                                         33 |      2 |    94% |   35, 52
sde_collections/utils/slack_utils.py  |                                                                     19 |      4 |    79% |   57-58, 66-67
sde_collections/utils/title_resolver.py  |                                                                  90 |      5 |    94% |   64, 75, 83, 85, 92
sde_collections/views.py  |                                                                                368 |    229 |    38% |   70, 82-89, 102-141, 144-187, 194, 208-212, 215-223, 226-237, 246, 249-251, 256-265, 273-277, 280-306, 309-315, 323-327, 330-336, 339-345, 353-355, 358-368, 410, 413-422, 430, 433-442, 450, 458, 461-475, 483, 486-490, 505-511, 523-530, 538-566, 577-583, 586-607, 610-613, 628-634
sde_indexing_helper/__init__.py  |                                                                           2 |      0 |   100% |
sde_indexing_helper/conftest.py  |                                                                           9 |      0 |   100% |
sde_indexing_helper/contrib/__init__.py  |                                                                   0 |      0 |   100% |
sde_indexing_helper/contrib/sites/__init__.py  |                                                             0 |      0 |   100% |
sde_indexing_helper/users/__init__.py  |                                                                     0 |      0 |   100% |
sde_indexing_helper/users/adapters.py  |                                                                    11 |     11 |     0% |   1-16
sde_indexing_helper/users/admin.py  |                                                                       13 |      0 |   100% |
sde_indexing_helper/users/apps.py  |                                                                        10 |      0 |   100% |
sde_indexing_helper/users/context_processors.py  |                                                           3 |      0 |   100% |
sde_indexing_helper/users/forms.py  |                                                                       15 |      0 |   100% |
sde_indexing_helper/users/models.py  |                                                                      10 |      0 |   100% |
sde_indexing_helper/users/tasks.py  |                                                                        6 |      0 |   100% |
sde_indexing_helper/users/urls.py  |                                                                         4 |      0 |   100% |
sde_indexing_helper/users/views.py  |                                                                       27 |      0 |   100% |
sde_indexing_helper/utils/__init__.py  |                                                                     0 |      0 |   100% |
sde_indexing_helper/utils/exceptions.py  |                                                                   7 |      0 |   100% |
sde_indexing_helper/utils/storages.py  |                                                                     7 |      7 |     0% |   1-11
tests/test_merge_production_dotenvs_in_dotenv.py  |                                                         13 |      0 |   100 |%

## Critical Areas
### Config Generation
- config_generation/db_to_xml.py
   - update_or_add_element_value()
   - _update_config_xml()
   - convert_template_to_scraper()
   - add_document_type()
   - add_url_exclude()
   - add_title_mapping()
   - add_job_list_item()
   - get_tag_value()
   - fetch_treeroot()
   - fetch_document_type()
- config_generation/generate_jobs.py
   - make_all_parallel_jobs()

### Models
  - environmental_justice/models.py
  - sde_collections/models/collection.py
    - clear_delta_urls()
    - clear_dump_urls()
    - refresh_url_lists_for_all_patterns ()
    - migrate_dump_to_delta ()
    - create_or_update_delta_url
    - promote_to_curate
    - add_to_public_query()
    - create_scraper_config()
    - create_indexer_config()
    - create_plugin_config()
    - _write_to_github()
    - update_config_xml()
    - apply_all_patterns()
    - handle_workflow_status_change()
  - sde_collections/models/collection_choice_fields.py
  - sde_collections/models/delta_patterns.py
  - sde_collections/models/delta_url.py
  - sde_collections/models/pattern.py
  - sde_indexing_helper/users/models.py

### Views
  - environmental_justice/views.py
  - sde_collections/views.py
  - sde_indexing_helper/users/views.py

### Serializers and APIs
  - environmental_justice/serializers.py
  - sde_collections/serializers.py

### Admin Interface
  - environmental_justice/admin.py
  - sde_collections/admin.py
    - fetch_full_text_lrm_dev_action()
    - fetch_full_text_xli_action()
  - sde_indexing_helper/users/admin.py

### Utilities and Helpers
  - sde_collections/utils/github_helper.py
  - sde_collections/utils/health_check.py
  - sde_collections/utils/title_resolver.py
  - sde_collections/utils/github_helper.py
     - fetch_metadata()
     - _get_contents_from_path()

### Task Automation and Background Jobs
  - sde_collections/tasks.py

### Key Operational Pipelines in the Repository
The selection of critical areas for testing is guided by the following pipelines of the repository:
1. Sinequa config files are generated
2. COSMOS imports data from LRM Dev
3. Imported data is processed
4. Curators update URL metadata
5. Sinequa reads results from the COSMOS APIs

### Critical Areas Lacking Tests
- **Config Generation**: Config generation files are under-tested. Develop unit tests for all critical functions in the config_generation files.
- **Project Settings**: Environment-specific configurations (`local.py`, `production.py`) have no tests.
- **Frontend Features**: Currently, there are no tests covering frontend logic and interactions.
- **Utilities and Helpers**: Essential utility modules like github_helper.py and health_check.py lack tests

