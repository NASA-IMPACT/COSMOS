"""
indexes lots of stuff at once
splits a big list of collections into n subgroups. each collection has a job created.
each indexing job is added to one of the n subgroups. a master runner is made that executes the n 
subgroups in parallel
"""

from db_to_xml import XmlEditor

# fake list of collections
collection_list = [f"test_collection_{index}" for index in range(0, 12)]

template_root_path = "xmls/"
joblist_template_path = f"{template_root_path}joblist_template.xml"

job_path_root = "..sinequa_configs/jobs/"
job_path_root = "xmls/jobtesting/"
n = 3  # number of collections to run in parellel (as well as number of joblists)


def create_job_name(collection_name):
    return f"collection.indexer.{collection_name}.xml"


def create_joblist_name(index):
    return f"parallel_indexing_list-{index}.xml"


# create single jobs to run each collection
for collection in collection_list:
    job = XmlEditor(f"{template_root_path}job_template.xml")
    job.update_or_add_element_value("Collection", collection)
    job._write_xml(f"{job_path_root}{create_job_name(collection)}")


# Create an empty list of lists
sublists = [[] for _ in range(n)]

# Distribute elements of the big list into sublists
for i in range(len(collection_list)):
    # Use modulus to decide which sublist to put the item in
    sublist_index = i % n
    sublists[sublist_index].append(collection_list[i])

# create the n joblists (which will execute their contents serially in parellel)
job_names = []
for index, sublist in enumerate(sublists):
    joblist = XmlEditor(joblist_template_path)
    for collection in sublist:
        joblist.add_job_list_item(create_job_name(collection))

    joblist._write_xml(f"{job_path_root}{create_joblist_name(index)}")
    job_names.append(create_joblist_name.replace(".xml", ""))

master = XmlEditor(joblist_template_path)
master.update_or_add_element_value("RunJobsInParallel", "true")
[master.add_job_list_item(job_name) for job_name in job_names]
master._write_xml(f"{job_path_root}parallel_indexing_list-master.xml")
