from ..models.collection import Collection


def test_create_config_xml():
    # Collection.objects.create(name="test", division=3)
    collection = Collection(name="test", division=3)
    assert False, collection.create_config_xml()
