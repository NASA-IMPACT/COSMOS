import os

server_configs = {
    "dev": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": os.getenv("BASE_URL_DEV"),
        "index": "sde_index",
    },
    "test": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": os.getenv("BASE_URL_TEST"),
        "index": "sde_index",
    },
    "production": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": os.getenv("BASE_URL_PROD"),
        "index": "sde_index",
    },
    "secret_test": {
        "app_name": "nasa-sba-sde",
        "query_name": "query-sde-primary",
        "base_url": os.getenv("BASE_URL_TEST"),
        "index": "sde_index",
    },
    "secret_production": {
        "app_name": "nasa-sba-sde",
        "query_name": "query-sde-primary",
        "base_url": os.getenv("BASE_URL_PROD"),
        "index": "sde_index",
    },
    "xli": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": os.getenv("BASE_URL_XLI"),
        "index": "sde_index",
    },
    "lrm_dev": {
        "app_name": "sde-init-check",
        "query_name": "query-init-check",
        "base_url": os.getenv("BASE_URL_LRM_DEV"),
        "index": "sde_init_check",
    },
    "lrm_qa": {
        "app_name": "sde-init-check",
        "query_name": "query-init-check",
        "base_url": os.getenv("BASE_URL_LRM_QA"),
        "index": "sde_init_check",
    },
    "ren_server": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": os.getenv("BASE_URL_REN"),
        "index": "sde_index",
    },
    "test_server": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": os.getenv("BASE_URL_TEST_SERVER"),
        "index": "sde_index",
    },
}
