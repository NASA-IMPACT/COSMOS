from sources_to_scrape import (
    sources_to_index_test_grid_20240809,
)

tokens: dict[str, str] = {
    "test_server": "token here",
    "ren_server": "token here",
}

AVAILABLE_INDEXERS_TEST = [
    "IndexerServerA/identity0",
    "IndexerServerB/identity0",
]

AVAILABLE_INDEXERS_PROD = ["NodeINDEX1/identity0", "NodeINDEX2/identity0"]

TEST_SERVER_INDEXES = [  # this is the test server list
    # "sde_neural_test_index",
    "sde_index"
]

PROD_SERVER_INDEXES = [
    # "EDP_Audit_1",
    # "SMD_LSDA_Repository_1",
    # # "EDP_UserMetadata_1",
    # "SMD_NTRS_Repository_1",
    # "GCMD_Repository_1",
    # "SMD_PLANETARY_Repository_1",
    # # "GCMD_Repository_1_Metadata",
    # "SMD_PLANETARY_Repository_2",
    # "GCMD_Repository_2",
    # "STI_Repository_1",
    # # "GCMD_Repository_3_Metadata",
    # # "STI_Repository_1_Metadata",
    # "HELIO_Repository_1",
    # "STI_Repository_2",
    "SDE_Index",
    # "STI_Repository_2_Metadata",
    # "SMD_ASTRO_Repository_1",
    # "STI_Repository_3",
    # "SMD_ASTRO_Repository_2",
    # "STI_Repository_4",
    # "SMD_EARTHSCIENCE_Repository_1",
    # # "SinequaDoc",
    # "SMD_GENELAB_Repository_1",
    # "Test",
]


SERVER_INFO = {
    "test": {
        "indexes": TEST_SERVER_INDEXES,
        "indexers": AVAILABLE_INDEXERS_TEST,
    },
    "prod": {
        "indexes": PROD_SERVER_INDEXES,
        "indexers": AVAILABLE_INDEXERS_PROD,
    },
}

# Job Creation Config
collection_list: list[str] = sources_to_index_test_grid_20240809  # python list
date = "20240809"
source = "SDE"
server = "test"

# auto assigned
batch_delete_name: str = f"sources_to_delete_on_{server}_{date}"
batch_index_name: str = f"sources_to_index_on_{server}_{date}"
available_indexers = SERVER_INFO[server]["indexers"]
indexes_to_delete_from = SERVER_INFO[server]["indexes"]
