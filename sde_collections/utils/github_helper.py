import xmltodict
from django.conf import settings
from github import Github
from github.GithubException import UnknownObjectException

from ..models.collection_choice_fields import ConnectorChoices, CurationStatusChoices


class GitHubHandler:
    def __init__(self, collections, *args, **kwargs):
        self.github_token = settings.GITHUB_ACCESS_TOKEN
        self.github_repo = settings.SINEQUA_CONFIGS_GITHUB_REPO
        self.github_branch = settings.GITHUB_BRANCH_FOR_WEBAPP
        self.g = Github(self.github_token)
        self.repo = self.g.get_repo(f"{self.github_repo}")
        self.dev_branch = self.repo.default_branch
        self.collections = collections

    def _get_config_file_path(self, collection):
        file_path = f"sources/SMD/{collection.config_folder}/default.xml"
        return file_path

    def _get_file_contents(self, collection):
        """
        Get file contents from GitHub
        """
        FILE_PATH = self._get_config_file_path(collection)

        try:
            contents = self.repo.get_contents(FILE_PATH, ref=self.github_branch)
        except UnknownObjectException:
            return None

        return contents

    def _update_file_contents(self, collection):
        """
        Update file contents on GitHub
        """
        contents = self._get_file_contents(collection)
        FILE_CONTENTS = contents.decoded_content.decode("utf-8")

        COMMIT_MESSAGE = f"Webapp: Update {collection.name}"

        self.repo.update_file(
            contents.path,
            COMMIT_MESSAGE,
            FILE_CONTENTS,
            contents.sha,
            branch=self.github_branch,
        )

    def create_pull_request(self):
        title = f"Webapp: Update {self.collections.count()} config files"
        body = "\n".join(self.collections.values_list("name", flat=True))
        self.repo.create_pull(
            title=title,
            body=body,
            base=self.dev_branch,
            head=self.github_branch,
        )

    def push_to_github(self):
        for collection in self.collections:
            self._update_file_contents(collection)
            collection.curation_status = CurationStatusChoices.GITHUB_PR_CREATED
            collection.save()
        self.create_pull_request()

    def get_connector_type(self):
        for collection in self.collections:
            print("WORKING ON: ", collection.name)
            contents = self._get_file_contents(collection)

            if not contents:
                continue

            FILE_CONTENTS = contents.decoded_content.decode("utf-8")

            connector_xml = xmltodict.parse(FILE_CONTENTS)
            try:
                connector_type = connector_xml["Sinequa"]["Connector"]
            except KeyError:
                connector_type = None

            if connector_type is None:
                collection.connector = ConnectorChoices.NO_CONNECTOR
            elif connector_type == "crawler2":
                collection.connector = ConnectorChoices.CRAWLER2
            elif connector_type == "json":
                collection.connector = ConnectorChoices.JSON
            elif connector_type == "hyperindex":
                collection.connector = ConnectorChoices.HYPERINDEX
            collection.save()
