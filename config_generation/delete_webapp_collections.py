"""
this script is used in conjunction with deletes_config_folders.py and delete_content.py to purge a collection
in this case, from the webapp
"""

from sde_collections.models.collection import Collection


def delete_collections_by_config_folder(names_to_delete):
    for name in names_to_delete:
        Collection.objects.filter(config_folder__exact=name).delete()
        print(f"Deleted collections with config folder: {name}")


# run this in the shell on your list of collection names
# dmshell is the alias
