"""
indexes lots of stuff at once
splits a big list of collections into n subgroups. each collection has a job created.
each indexing job is added to one of the n subgroups. a master runner is made that executes the n
subgroups in parallel
"""

from db_to_xml_file_based import XmlEditor

from config import available_indexers, batch_index_name, collection_list, source


class ParallelJobCreator:
    def __init__(
        self,
        collection_list,
        template_root_path="xmls/",
        job_path_root="../sinequa_configs/jobs/",
        source=source,
    ):
        """
        these default values rely on the old file structure, where the sinequa_configs were a
        sub-repo of sde-indexing-helper. so when running this, you will need the sde-backend
        code to be inside a folder called sinequa_configs
        """

        self.collection_list = collection_list
        self.template_root_path = template_root_path
        self.joblist_template_path = f"{template_root_path}joblist_template.xml"
        self.job_path_root = job_path_root
        self.source = source

    def _create_job_name(self, collection_name):
        """
        each job that runs an individual collection needs a name based on the collection name
        this code generates that file name as a string, and it will be passed to the function that
            creates the actual job file
        """
        if source == "SDE":
            return f"collection.indexer.{collection_name}.xml"
        else:
            return f"collection.{source}.{collection_name}.xml"

    def _create_joblist_name(self, index):
        """
        each job that runs an list of collections a name based on:
            - the date the batch was created
            - the index out of n total batches
        this code generates that file name as a string, and it will be passed to the function that
            creates the actual job file
        """
        return f"parallel_indexing_list-{batch_index_name}-{index}.xml"

    def _create_collection_jobs(self):
        """
        in order to run a collection, a job must exist that runs it
        this code:
            - creates a job based on the job template
            - adds the exact collection name
            - saves it with a name that will reference the collection name
        """
        # create single jobs to run each collection
        for collection in self.collection_list:
            job = XmlEditor(f"{self.template_root_path}job_template.xml")
            job.update_or_add_element_value("Collection", f"/{self.source}/{collection}/")
            job._update_config_xml(f"{self.job_path_root}{self._create_job_name(collection)}")

    def make_all_parallel_jobs(self):
        # create initial single jobs that will be referenced by the parallel job lists
        self._create_collection_jobs()
        n = len(available_indexers)
        # Create an empty list of lists
        sublists = [[] for _ in range(n)]

        # Distribute elements of the big list into sublists
        for i in range(len(self.collection_list)):
            # Use modulus to decide which sublist to put the item in
            sublist_index = i % n
            sublists[sublist_index].append(self.collection_list[i])

        # create the n joblists (which will execute their contents serially in parallel
        job_names = []
        for index, sublist in enumerate(sublists):
            joblist = XmlEditor(self.joblist_template_path)
            joblist.update_or_add_element_value("StartIdentity", available_indexers[index])
            for collection in sublist:
                joblist.add_job_list_item(self._create_job_name(collection).replace(".xml", ""))

            joblist._update_config_xml(f"{self.job_path_root}{self._create_joblist_name(index)}")
            job_names.append(self._create_joblist_name(index).replace(".xml", ""))

        master = XmlEditor(self.joblist_template_path)
        master.update_or_add_element_value("RunJobsInParallel", "true")
        [master.add_job_list_item(job_name) for job_name in job_names]
        master._update_config_xml(f"{self.job_path_root}parallel_indexing_list-{batch_index_name}-master.xml")


if __name__ == "__main__":
    job_creator = ParallelJobCreator(collection_list=collection_list)
    job_creator.make_all_parallel_jobs()
