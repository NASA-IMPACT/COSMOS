# rename this file to config.py and do not track it on git
# example on how to get the token are in the README.md
# go down to the bottom to the section called this is the stuff you want to change

from sources_to_scrape import sources_to_delete_20231108

# API Config
tokens: dict[str, str] = {
    "test_server": "token here",
    "ren_server": "token here",
}

AVAILABLE_INDEXERS_TEST = [
    "NodeIndexer1/identity0",
    "NodeWebapp1/identity0",
    "NodeWebapp2/identity0",
    "NodeWebapp3/identity0",
]

AVAILABLE_INDEXERS_PROD = ["NodeINDEX1/identity0", "NodeINDEX2/identity0"]

TEST_SERVER_INDEXES = [  # this is the test server list
    "HELIO_Repository_1",
    "SDE_Acronyms",
    "SMD_ASTRO_Repository_1",
    "SMD_ASTRO_Repository_2",
    "SMD_EARTHSCIENCE_Repository_1",
    "SMD_GENELAB_Repository_1",
    "SMD_PLANETARY_Repository_1",
    "SMD_PLANETARY_Repository_2",
]

PROD_SERVER_INDEXES = [
    # "EDP_Audit_1",
    "SMD_LSDA_Repository_1",
    # "EDP_UserMetadata_1",
    "SMD_NTRS_Repository_1",
    "GCMD_Repository_1",
    "SMD_PLANETARY_Repository_1",
    # "GCMD_Repository_1_Metadata",
    "SMD_PLANETARY_Repository_2",
    "GCMD_Repository_2",
    "STI_Repository_1",
    # "GCMD_Repository_3_Metadata",
    # "STI_Repository_1_Metadata",
    "HELIO_Repository_1",
    "STI_Repository_2",
    "SDE_Index",
    # "STI_Repository_2_Metadata",
    "SMD_ASTRO_Repository_1",
    "STI_Repository_3",
    "SMD_ASTRO_Repository_2",
    "STI_Repository_4",
    "SMD_EARTHSCIENCE_Repository_1",
    # "SinequaDoc",
    "SMD_GENELAB_Repository_1",
    "Test",
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

# this is the stuff you want to change
collection_list: list[str] = sources_to_delete_20231108  # python list
source = "SMD"
batch_name: str = "delete_everywhere_20231108_test"
server = "test"

# auto assigned
available_indexers = SERVER_INFO[server]["indexers"]
indexes_to_delete_from = SERVER_INFO[server]["indexes"]
