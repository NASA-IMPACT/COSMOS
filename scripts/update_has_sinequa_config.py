from sde_collections.models.collection import Collection

with open("no_folders.txt") as no_folders_list:
    no_folders = no_folders_list.readlines()

for no_folder in no_folders:
    Collection.objects.filter(name=no_folder.strip()).update(has_sinequa_config=False)
