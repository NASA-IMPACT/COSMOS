## Overview
As of early 2025, we have only recently been writing tests for new features, and have about 250 tests in total, mostly centered around the EJ portal, the reindexing process, and pattern applications. 

Although this covers much of the core system logic, there still remain a number of untested logical areas such as the config file generation, core project settings, frontend features, etc.

This document outlines a testing strategy for the project, which will guide us towards adding tests in the most critical areas first, followed by a plan to fully cover the remaining areas.

## Current Coverage
Using the coverage library, the following report was generated:





Generating coverage report...
Name                                                                                                  Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------------------------------------------------------------------
config/__init__.py                                                                                        2      0   100%
config/celery_app.py                                                                                      6      0   100%
config/settings/__init__.py                                                                               0      0   100%
config/settings/base.py                                                                                  94      0   100%
config/settings/local.py                                                                                 20     20     0%   1-65
config/settings/production.py                                                                            48     48     0%   1-162
config/settings/test.py                                                                                   7      0   100%
config/urls.py                                                                                           14      4    71%   26-47
config/wsgi.py                                                                                            8      8     0%   17-36
config_generation/__init__.py                                                                             0      0   100%
config_generation/api.py                                                                                 34     34     0%   1-88
config_generation/config_example.py                                                                      15     15     0%   1-69
config_generation/db_to_xml.py                                                                          203    133    34%   45, 47, 50, 96, 119-125, 129-136, 142-149, 197-200, 206-214, 225-230, 242-271, 274-278, 285-292, 303-308, 311, 317, 326-332, 342-349, 361-368, 371-374, 377-378, 382-390, 393-399, 402-412, 415-429
config_generation/db_to_xml_file_based.py                                                                52     52     0%   4-119
config_generation/delete_config_folders.py                                                               24     24     0%   9-50
config_generation/delete_server_content.py                                                               12     12     0%   3-25
config_generation/delete_webapp_collections.py                                                            5      5     0%   6-12
config_generation/export_collections.py                                                                  36     36     0%   1-73
config_generation/export_whole_index.py                                                                  28     28     0%   1-58
config_generation/generate_collection_list.py                                                            29     29     0%   8-69
config_generation/generate_commands.py                                                                   41     41     0%   6-87
config_generation/generate_emac_indexer.py                                                               24     24     0%   1-81
config_generation/generate_jobs.py                                                                       42     42     0%   8-100
config_generation/generate_scrapers.py                                                                   15     15     0%   2-54
config_generation/minimum_api.py                                                                         33     33     0%   1-81
config_generation/preprocess_sources.py                                                                  25     25     0%   1-50
config_generation/sources_to_scrape.py                                                                   28     28     0%   2-1631
config_generation/tests/__init__.py                                                                       0      0   100%
config_generation/tests/test_db_to_xml.py                                                                23      3    87%   20, 24, 28
docs/__init__.py                                                                                          0      0   100%
docs/conf.py                                                                                             17     17     0%   13-62
environmental_justice/__init__.py                                                                         0      0   100%
environmental_justice/admin.py                                                                            5      0   100%
environmental_justice/apps.py                                                                             4      0   100%
environmental_justice/migrations/0001_initial.py                                                          5      0   100%
environmental_justice/migrations/0002_environmentaljusticerow_sde_links.py                                4      0   100%
environmental_justice/migrations/0003_remove_environmentaljusticerow_sde_links_and_more.py                4      0   100%
environmental_justice/migrations/0004_alter_environmentaljusticerow_data_visualization_and_more.py        4      0   100%
environmental_justice/migrations/0005_environmentaljusticerow_destination_server.py                       7      2    71%   5-6
environmental_justice/migrations/0006_remove_environmentaljusticerow_destination_server_and_more.py       9      4    56%   7-20
environmental_justice/migrations/__init__.py                                                              0      0   100%
environmental_justice/models.py                                                                          29      1    97%   44
environmental_justice/serializers.py                                                                      6      0   100%
environmental_justice/tests/conftest.py                                                                  15      0   100%
environmental_justice/tests/factories.py                                                                 24      0   100%
environmental_justice/tests/test_ej_api.py                                                               74      0   100%
environmental_justice/views.py                                                                           23      0   100%
feedback/__init__.py                                                                                      0      0   100%
feedback/admin.py                                                                                        14      0   100%
feedback/apps.py                                                                                          4      0   100%
feedback/migrations/0001_initial.py                                                                       5      0   100%
feedback/migrations/0002_alter_contentcurationrequest_additional_info.py                                  4      0   100%
feedback/migrations/0003_feedback_source.py                                                               4      0   100%
feedback/migrations/0004_contentcurationrequest_created_at_and_more.py                                    4      0   100%
feedback/migrations/__init__.py                                                                           0      0   100%
feedback/models.py                                                                                       42     15    64%   20-29, 35-44, 61-63
feedback/serializers.py                                                                                  10      0   100%
feedback/tests.py                                                                                         0      0   100%
feedback/urls.py                                                                                          4      0   100%
feedback/views.py                                                                                         9      0   100%
manage.py                                                                                                16     16     0%   2-31
merge_production_dotenvs_in_dotenv.py                                                                    15      1    93%   26
scripts/ej/cmr_processing.py                                                                            241      5    98%   160, 186-188, 397, 410
scripts/ej/config.py                                                                                      6      0   100%
scripts/ej/test_cmr_processing.py                                                                       225      1    99%   610
scripts/ej/test_threshold_processing.py                                                                  97      1    99%   209
scripts/ej/threshold_processing.py                                                                       20      0   100%
sde_collections/__init__.py                                                                               0      0   100%
sde_collections/admin.py                                                                                212     72    66%   22-24, 29, 34, 40-60, 65-81, 86-89, 98-101, 110-112, 120-134, 143, 148, 153, 158, 163, 168, 173, 178-189, 196-197, 260, 265, 270, 275, 302-303, 308-309, 314-316, 345-372, 478-480
sde_collections/apps.py                                                                                   4      0   100%
sde_collections/forms.py                                                                                 15      0   100%
sde_collections/management/commands/database_backup.py                                                   62      1    98%   68
sde_collections/management/commands/database_restore.py                                                  83      8    90%   34, 36, 87-89, 142-145
sde_collections/migrations/0001_initial.py                                                                6      0   100%
sde_collections/migrations/0002_remove_collection_machine_name.py                                         4      0   100%
sde_collections/migrations/0003_alter_collection_config_folder.py                                         4      0   100%
sde_collections/migrations/0004_collection_cleaning_order.py                                              4      0   100%
sde_collections/migrations/0005_alter_candidateurl_url.py                                                 4      0   100%
sde_collections/migrations/0006_alter_candidateurl_generated_title_and_more.py                            4      0   100%
sde_collections/migrations/0007_excludepattern_pattern_type.py                                            4      0   100%
sde_collections/migrations/0008_alter_excludepattern_match_pattern.py                                     4      0   100%
sde_collections/migrations/0009_titlepattern_pattern_type.py                                              4      0   100%
sde_collections/migrations/0010_rename_pattern_type_titlepattern_match_pattern_type_and_more.py           4      0   100%
sde_collections/migrations/0011_alter_titlepattern_title_pattern_type.py                                  4      0   100%
sde_collections/migrations/0012_collection_curated_by_collection_curation_started_and_more.py             6      0   100%
sde_collections/migrations/0013_alter_titlepattern_options_and_more.py                                    5      0   100%
sde_collections/migrations/0014_alter_documenttypepattern_unique_together_and_more.py                     4      0   100%
sde_collections/migrations/0015_candidateurl_document_type.py                                             4      0   100%
sde_collections/migrations/0016_alter_documenttypepattern_candidate_urls_and_more.py                      5      0   100%
sde_collections/migrations/0017_requiredurls.py                                                           5      0   100%
sde_collections/migrations/0018_alter_requiredurls_url.py                                                 4      0   100%
sde_collections/migrations/0019_alter_requiredurls_url.py                                                 4      0   100%
sde_collections/migrations/0020_alter_collection_curation_status.py                                       4      0   100%
sde_collections/migrations/0021_alter_collection_curation_status.py                                       4      0   100%
sde_collections/migrations/0022_alter_candidateurl_unique_together.py                                     4      0   100%
sde_collections/migrations/0023_collection_github_issue_number.py                                         4      0   100%
sde_collections/migrations/0024_alter_collection_curation_status.py                                       4      0   100%
sde_collections/migrations/0025_alter_documenttypepattern_match_pattern_type_and_more.py                  4      0   100%
sde_collections/migrations/0026_alter_collection_curation_status_and_more.py                              4      0   100%
sde_collections/migrations/0027_alter_collection_connector.py                                             4      0   100%
sde_collections/migrations/0028_collection_has_sinequa_config.py                                          4      0   100%
sde_collections/migrations/0029_alter_candidateurl_document_type_and_more.py                              4      0   100%
sde_collections/migrations/0030_candidateurl_inference_by.py                                              4      0   100%
sde_collections/migrations/0031_candidateurl_is_pdf.py                                                    4      0   100%
sde_collections/migrations/0032_collection_workflow_status.py                                             4      0   100%
sde_collections/migrations/0033_alter_collection_config_folder.py                                         4      0   100%
sde_collections/migrations/0034_rename_tree_root_collection_tree_root_deprecated.py                       4      0   100%
sde_collections/migrations/0035_alter_candidateurl_unique_together.py                                     4      0   100%
sde_collections/migrations/0036_candidateurl_present_on_prod_and_more.py                                  4      0   100%
sde_collections/migrations/0037_alter_collection_source.py                                                4      0   100%
sde_collections/migrations/0037_remove_collection_has_sinequa_config.py                                   4      0   100%
sde_collections/migrations/0038_merge_20231126_1152.py                                                    4      0   100%
sde_collections/migrations/0039_includepattern.py                                                         5      0   100%
sde_collections/migrations/0040_candidateurl_hash.py                                                      4      0   100%
sde_collections/migrations/0041_alter_candidateurl_hash.py                                                4      0   100%
sde_collections/migrations/0042_alter_collection_division_and_more.py                                     4      0   100%
sde_collections/migrations/0043_comments.py                                                               6      0   100%
sde_collections/migrations/0044_alter_collection_document_type.py                                         4      0   100%
sde_collections/migrations/0045_alter_collection_workflow_status.py                                       4      0   100%
sde_collections/migrations/0045_workflowhistory.py                                                        6      0   100%
sde_collections/migrations/0046_resolvedtitle_candidateurl_resolved_title.py                              6      0   100%
sde_collections/migrations/0046_workflowhistory_old_status.py                                             4      0   100%
sde_collections/migrations/0047_remove_candidateurl_resolved_title_and_more.py                            5      0   100%
sde_collections/migrations/0048_alter_resolvedtitle_candidate_url.py                                      5      0   100%
sde_collections/migrations/0049_alter_resolvedtitle_resolution_date_time.py                               4      0   100%
sde_collections/migrations/0050_alter_resolvedtitle_resolved_title.py                                     4      0   100%
sde_collections/migrations/0051_alter_resolvedtitle_error_string_and_more.py                              4      0   100%
sde_collections/migrations/0052_rename_resolution_date_time_resolvedtitle_created_at_and_more.py          5      0   100%
sde_collections/migrations/0053_alter_collection_url.py                                                   4      0   100%
sde_collections/migrations/0054_merge_20240531_1332.py                                                    4      0   100%
sde_collections/migrations/0055_alter_workflowhistory_old_status_and_more.py                              4      0   100%
sde_collections/migrations/0056_alter_candidateurl_document_type_and_more.py                              4      0   100%
sde_collections/migrations/0057_alter_collection_workflow_status_and_more.py                              4      0   100%
sde_collections/migrations/0058_candidateurl_division_collection_is_multi_division_and_more.py            5      0   100%
sde_collections/migrations/0059_candidateurl_scraped_text.py                                              4      0   100%
sde_collections/migrations/0059_candidateurl_tdamm_tag_manual_and_more.py                                 5      0   100%
sde_collections/migrations/0059_url_curatedurl_deltaurl_dumpurl.py                                        5      0   100%
sde_collections/migrations/0060_alter_candidateurl_scraped_text.py                                        4      0   100%
sde_collections/migrations/0060_remove_deltaurl_url_ptr_remove_dumpurl_url_ptr_and_more.py                4      0   100%
sde_collections/migrations/0061_dumpurl_deltaurl_curatedurl.py                                            5      0   100%
sde_collections/migrations/0062_deltatitlepattern_deltaresolvedtitleerror_and_more.py                     6      0   100%
sde_collections/migrations/0063_merge_20241112_1428.py                                                    4      0   100%
sde_collections/migrations/0064_alter_curatedurl_options_and_more.py                                      4      0   100%
sde_collections/migrations/0065_rename_delete_deltaurl_to_delete_and_more.py                              5      0   100%
sde_collections/migrations/0066_alter_deltadivisionpattern_unique_together_and_more.py                    5      0   100%
sde_collections/migrations/0066_merge_20241120_0158.py                                                    4      0   100%
sde_collections/migrations/0067_alter_deltadivisionpattern_options_and_more.py                            4      0   100%
sde_collections/migrations/0067_remove_candidateurl_tdamm_tag_manual_and_more.py                          4      0   100%
sde_collections/migrations/0068_alter_deltadivisionpattern_collection_and_more.py                         6      0   100%
sde_collections/migrations/0068_curatedurl_tdamm_tag_manual_curatedurl_tdamm_tag_ml_and_more.py           5      0   100%
sde_collections/migrations/0069_candidateurl_tdamm_tag_manual_and_more.py                                 5      0   100%
sde_collections/migrations/0070_merge_20241205_1437.py                                                    4      0   100%
sde_collections/migrations/0071_alter_candidateurl_tdamm_tag_manual_and_more.py                           5      0   100%
sde_collections/migrations/0072_collection_reindexing_status_reindexinghistory.py                        26     19    27%   8-52
sde_collections/migrations/0073_alter_collection_workflow_status_and_more.py                              4      0   100%
sde_collections/migrations/0074_alter_collection_reindexing_status_and_more.py                            4      0   100%
sde_collections/migrations/0075_alter_collection_reindexing_status_and_more.py                           25     19    24%   7-20, 24-39
sde_collections/migrations/__init__.py                                                                    0      0   100%
sde_collections/models/__init__.py                                                                        0      0   100%
sde_collections/models/candidate_url.py                                                                  89     16    82%   124, 128-134, 138-142, 145, 176-177
sde_collections/models/collection.py                                                                    414    144    65%   241, 269, 277-287, 291-301, 305-315, 319-344, 348-357, 361, 365, 369-376, 380-387, 394, 403-406, 419, 436-439, 449-470, 478, 482-515, 519, 523, 527, 531-532, 536, 540-546, 550-553, 558-567, 575-617, 640, 679, 689, 703, 707-732, 765, 769-777, 785
sde_collections/models/collection_choice_fields.py                                                      138     20    86%   14-17, 36-39, 56-59, 74-77, 168-171
sde_collections/models/delta_patterns.py                                                                313     33    89%   119, 123, 139, 226-227, 263, 267, 291, 382-389, 439-449, 498, 503-506, 592, 627-641
sde_collections/models/delta_url.py                                                                      81     19    77%   117-125, 129-135, 139-143, 146
sde_collections/models/pattern.py                                                                       145     79    46%   40-48, 56-63, 66, 69, 73-74, 78-79, 87, 94-96, 105, 117-119, 128, 139-151, 163-205, 208-212, 215-216, 230-233, 243, 257-260, 268
sde_collections/serializers.py                                                                          191     47    75%   80-81, 84-85, 88-89, 92-93, 129-130, 133-134, 137-138, 141-142, 197, 201, 211-214, 244-247, 257-260, 271, 274, 307-315, 335-343, 358-366
sde_collections/sinequa_api.py                                                                          102      3    97%   65, 255, 289
sde_collections/tasks.py                                                                                119     67    44%   25-67, 72-108, 113-117, 122-125, 130-148, 153-155, 215-216
sde_collections/tests.py                                                                                 24     24     0%   1-36
sde_collections/tests/__init__.py                                                                         0      0   100%
sde_collections/tests/factories.py                                                                       57      0   100%
sde_collections/tests/test_database_backup.py                                                            96      0   100%
sde_collections/tests/test_database_restore.py                                                          139      0   100%
sde_collections/tests/test_delta_patterns.py                                                            118      0   100%
sde_collections/tests/test_exclude_patterns.py                                                          142      7    95%   21-41
sde_collections/tests/test_field_modifier_patterns.py                                                   170      4    98%   20-31
sde_collections/tests/test_field_modifier_unapply.py                                                     85      0   100%
sde_collections/tests/test_fileext.py                                                                    15      0   100%
sde_collections/tests/test_import_fulltexts.py                                                           43      0   100%
sde_collections/tests/test_include_patterns.py                                                           53      0   100%
sde_collections/tests/test_migrate_dump.py                                                              188      0   100%
sde_collections/tests/test_migration.py                                                                  93      0   100%
sde_collections/tests/test_pattern_specificity.py                                                        84      0   100%
sde_collections/tests/test_promote_collection.py                                                        164      2    99%   169, 184
sde_collections/tests/test_sinequa_api.py                                                               147      2    99%   25-26
sde_collections/tests/test_tdamm_tags.py                                                                108      0   100%
sde_collections/tests/test_title_pattern_unapply.py                                                      94      0   100%
sde_collections/tests/test_title_resolution.py                                                           59      0   100%
sde_collections/tests/test_url_apis.py                                                                  162      0   100%
sde_collections/tests/test_workflow_status_triggers.py                                                  105      0   100%
sde_collections/urls.py                                                                                  17      0   100%
sde_collections/utils/__init__.py                                                                         0      0   100%
sde_collections/utils/bulk_github_push.py                                                                 8      8     0%   7-22
sde_collections/utils/generate_deployment_message.py                                                      8      8     0%   1-24
sde_collections/utils/github_helper.py                                                                  115     93    19%   12-18, 30-42, 49-52, 60-68, 81-96, 104-110, 119-123, 127-129, 132-142, 145-152, 155-172, 175, 178-185, 189-192, 196-224, 227
sde_collections/utils/health_check.py                                                                   123    106    14%   33-46, 51-57, 61-98, 102-143, 155-165, 172-187, 191-273
sde_collections/utils/paired_field_descriptor.py                                                         33      2    94%   35, 52
sde_collections/utils/slack_utils.py                                                                     19      4    79%   57-58, 66-67
sde_collections/utils/title_resolver.py                                                                  90      5    94%   64, 75, 83, 85, 92
sde_collections/views.py                                                                                368    229    38%   70, 82-89, 102-141, 144-187, 194, 208-212, 215-223, 226-237, 246, 249-251, 256-265, 273-277, 280-306, 309-315, 323-327, 330-336, 339-345, 353-355, 358-368, 410, 413-422, 430, 433-442, 450, 458, 461-475, 483, 486-490, 505-511, 523-530, 538-566, 577-583, 586-607, 610-613, 628-634
sde_indexing_helper/__init__.py                                                                           2      0   100%
sde_indexing_helper/conftest.py                                                                           9      0   100%
sde_indexing_helper/contrib/__init__.py                                                                   0      0   100%
sde_indexing_helper/contrib/sites/__init__.py                                                             0      0   100%
sde_indexing_helper/contrib/sites/migrations/0001_initial.py                                              6      0   100%
sde_indexing_helper/contrib/sites/migrations/0002_alter_domain_unique.py                                  5      0   100%
sde_indexing_helper/contrib/sites/migrations/0003_set_site_domain_and_name.py                            20     12    40%   12-31, 39-40, 50-51
sde_indexing_helper/contrib/sites/migrations/0004_alter_options_ordering_domain.py                        4      0   100%
sde_indexing_helper/contrib/sites/migrations/__init__.py                                                  0      0   100%
sde_indexing_helper/users/__init__.py                                                                     0      0   100%
sde_indexing_helper/users/adapters.py                                                                    11     11     0%   1-16
sde_indexing_helper/users/admin.py                                                                       13      0   100%
sde_indexing_helper/users/apps.py                                                                        10      0   100%
sde_indexing_helper/users/context_processors.py                                                           3      0   100%
sde_indexing_helper/users/forms.py                                                                       15      0   100%
sde_indexing_helper/users/migrations/0001_initial.py                                                      8      0   100%
sde_indexing_helper/users/migrations/0002_contactformmodel_contentcurationrequestmodel.py                 4      0   100%
sde_indexing_helper/users/migrations/0003_delete_contactformmodel_and_more.py                             4      0   100%
sde_indexing_helper/users/migrations/__init__.py                                                          0      0   100%
sde_indexing_helper/users/models.py                                                                      10      0   100%
sde_indexing_helper/users/tasks.py                                                                        6      0   100%
sde_indexing_helper/users/tests/__init__.py                                                               0      0   100%
sde_indexing_helper/users/tests/factories.py                                                             16      0   100%
sde_indexing_helper/users/tests/test_admin.py                                                            23      0   100%
sde_indexing_helper/users/tests/test_forms.py                                                            10      0   100%
sde_indexing_helper/users/tests/test_models.py                                                            3      0   100%
sde_indexing_helper/users/tests/test_tasks.py                                                            11      0   100%
sde_indexing_helper/users/tests/test_urls.py                                                             11      0   100%
sde_indexing_helper/users/tests/test_views.py                                                            65      1    98%   30
sde_indexing_helper/users/urls.py                                                                         4      0   100%
sde_indexing_helper/users/views.py                                                                       27      0   100%
sde_indexing_helper/utils/__init__.py                                                                     0      0   100%
sde_indexing_helper/utils/exceptions.py                                                                   7      0   100%
sde_indexing_helper/utils/storages.py                                                                     7      7     0%   1-11
tests/test_merge_production_dotenvs_in_dotenv.py                                                         13      0   100%
-----------------------------------------------------------------------------------------------------------------------------------
TOTAL                                                                                                  7449   1794    76%
All tests passed successfully!
Coverage summary has been output to the terminal.