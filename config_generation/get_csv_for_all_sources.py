from api import Api
from generate_collection_list import turned_on_remaining_webcrawlers


api = Api("test_server")

for collection in turned_on_remaining_webcrawlers:
    response = api.sql("SMD", collection)
    # TODO: save response to a csv with f'{collection}.xml' as the name
