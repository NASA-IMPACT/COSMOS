import pytest


@pytest.fixture(autouse=True)
def _use_transactional_db(transactional_db):
    """Enable transaction rollback for all tests"""
    pass
