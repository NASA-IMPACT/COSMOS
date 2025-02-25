"""
sometimes spot fixes need to be run on a list of collections
this file provides a quick framework to generate a batch of commands based on an input json
"""

from db_to_xml_file_based import XmlEditor
from generate_jobs import ParallelJobCreator

from config import source


# note that there is an xml folder that contains templates
class CommandGenerator:
    def __init__(
        self,
        command_batch_name,
        template_root_path="xmls/",
        command_root_path="../sinequa_configs/commands/",
        source=source,
    ):
        self.command_batch_name = command_batch_name  # this is used to name the commands
        self.template_root_path = template_root_path
        self.command_template_path = f"{template_root_path}command_template.xml"
        self.job_command_template_path = f"{template_root_path}job_command_template.xml"
        self.command_root_path = command_root_path
        self.source = source

    def _generate_job_command_name(self, collection_name):
        # TODO
        # return f"job.{}"
        pass

    def _generate_job_command_file_path(self, collection_name):
        return f"{self.command_root_path}/{self._generate_command_name(collection_name)}.xml"

    def _generate_command_name(self, collection_name):
        """command names are used in the xml file name and are referenced by jobs (without the folder or .xml)"""
        return f"{self.command_batch_name}.{collection_name}"

    def _generate_command_file_path(self, collection_name):
        return f"{self.command_root_path}/{self._generate_command_name(collection_name)}.xml"

    def generate_command_file(self, collection_name, commands):
        command_file = XmlEditor(self.command_template_path)
        command_file.update_or_add_element_value(
            element_name="WhereClause",
            element_value=f"collection='/{self.source}/{collection_name}'",
        )
        for command in commands:
            command_file.add_column_update(
                column=command["Column"],
                value=command["Value"],
                selection=command.get("Selection", None),
            )
        command_file._update_config_xml(self._generate_command_file_path(collection_name))

    def generate_job_file(self, collection_name):
        # each command needs an job file to reference it
        job_file = XmlEditor(self.job_command_template_path)
        job_file.update_or_add_element_value(element_name="Command", element_value=command_name)
        job_file._update_config_xml()


# here's how you would list the commands to generate
commands_to_generate = {
    "collection_name": [
        {
            "Column": "treepath",
            "Value": "/Earth Science/Documents/Publications/NTRS Publication Database/",
            # 'Selection': 'selection_here'
        },
    ],
}

job_command_names = []
for collection_name, commands in commands_to_generate.items():
    generator = CommandGenerator(command_batch_name="fix_treeroots")
    generator.generate_command_file(collection_name=collection_name, commands=commands)
    command_name = generator._generate_command_name(collection_name)
    JOB_COMMAND_TEMPLATE_PATH = "config_generation/xmls/job_command_template.xml"
    job_file = XmlEditor(JOB_COMMAND_TEMPLATE_PATH)
    job_file.update_or_add_element_value(element_name="Command", element_value=command_name)
    job_file._update_config_xml()
    job_creator = ParallelJobCreator(
        [collection_name]
    )  # this class is a bit misconfigured for this task, but it works...
    job_creator()
