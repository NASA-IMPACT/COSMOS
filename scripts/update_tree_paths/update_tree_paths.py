# import json
# myjson = {}
# for collection in Collection.objects.all():
#     myjson[f"/SMD/{collection.config_folder}"] = collection.tree_root
# json.dump(myjson, open('scripts/update_tree_paths/collections.json', 'w'))

import json

import xmltodict

collections = json.load(
    open(
        "/Users/aacharya/work/sde-indexing-helper/scripts/update_tree_paths/collections.json",
    )
)
with open("command.xml") as commandfile:
    command = xmltodict.parse(commandfile.read())

with open("job.xml") as jobfile:
    job = xmltodict.parse(jobfile.read())

for collection_config_folder, collection_tree_root in collections.items():
    COMMAND_FILE_NAME = "consolidated_tree_path_update_command"
    # command["Sinequa"]["WhereClause"] = f"collection='{collection_config_folder}/'"
    # command["Sinequa"]["UpdateColumn"]["Value"] = f'"/{collection_tree_root}"'
    # job["Sinequa"]["Command"] = COMMAND_FILE_NAME

    with open(f"{COMMAND_FILE_NAME}.xml", "w") as collection_command_file:
        collection_command_file.write(xmltodict.unparse(command, pretty=True))

    # with open(
    #     f"jobs/update_treepath_{collection_config_folder.split('/')[2]}_job.xml", "w"
    # ) as collection_job_file:
    #     collection_job_file.write(xmltodict.unparse(job, pretty=True))
