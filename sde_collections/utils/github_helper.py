import datetime

from django.conf import settings
from github import Github
from github.GithubException import GithubException, UnknownObjectException

from config_generation.db_to_xml import XmlEditor

from ..models.collection_choice_fields import CurationStatusChoices


class GitHubHandler:
    def __init__(self, collections, *args, **kwargs):
        self.github_token = settings.GITHUB_ACCESS_TOKEN
        self.github_repo = settings.SINEQUA_CONFIGS_GITHUB_REPO
        self.time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.github_branch = settings.GITHUB_BRANCH_FOR_WEBAPP + "-" + self.time_stamp
        self.g = Github(self.github_token)
        self.repo = self.g.get_repo(f"{self.github_repo}")
        self.dev_branch = self.repo.default_branch
        self.collections = collections

    def _get_config_file_path(self, collection) -> str:
        file_path = f"sources/SMD/{collection.config_folder}/default.xml"
        return file_path

    def _get_file_contents(self, collection):
        """
        Get file contents from GitHub dev or update branch
        """
        FILE_PATH = self._get_config_file_path(collection)

        try:
            contents = self.repo.get_contents(FILE_PATH, ref=self.dev_branch)
        except UnknownObjectException:
            try:
                contents = self.repo.get_contents(FILE_PATH, ref=self.github_branch)
            except UnknownObjectException:
                return None

        return contents

    def create_and_initialize_config_file(self, collection, xml_string=""):
        """
        Create file contents on GitHub
        """
        FILE_PATH = self._get_config_file_path(collection)
        COMMIT_MESSAGE = f"Webapp: Create {collection.name}"

        if self._get_file_contents(collection) is None:
            self.repo.create_file(
                FILE_PATH,
                COMMIT_MESSAGE,
                xml_string,
                branch=self.github_branch,
            )
            return "Created"
        else:
            return "Exists"

    def _update_file_contents(self, collection):
        """
        Update file contents on GitHub
        """
        contents = self._get_file_contents(collection)
        FILE_CONTENTS = contents.decoded_content.decode("utf-8")
        updated_xml = collection.update_config_xml(FILE_CONTENTS)

        COMMIT_MESSAGE = f"Webapp: Update {collection.name}"

        self.repo.update_file(
            contents.path,
            COMMIT_MESSAGE,
            updated_xml,
            contents.sha,
            branch=self.github_branch,
        )

    def branch_exists(self, branch_name: str) -> bool:
        try:
            self.repo.get_branch(branch=branch_name)
            return True
        except GithubException:
            return False

    def create_branch(self, branch_name: str):
        # Get the SHA of the commit you want to branch from (basically the Dev branch)
        base_sha = self.repo.get_branch(self.dev_branch).commit.sha
        # Create the new branch
        self.repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_sha)

    def create_pull_request(self) -> None:
        title = "Webapp: Update config files"
        body = "\n".join(self.collections.values_list("name", flat=True))
        try:
            self.repo.create_pull(
                title=title,
                body=body,
                base=self.dev_branch,
                head=self.github_branch,
            )
        except GithubException:  # PR exists
            print("PR exists")

    def push_to_github(self) -> None:
        if not self.branch_exists(self.github_branch):
            self.create_branch(self.github_branch)
        for collection in self.collections:
            print(f"Pushing {collection.name} to GitHub.")
            self._update_file_contents(collection)
            collection.curation_status = CurationStatusChoices.GITHUB_PR_CREATED
            collection.save()
        self.create_pull_request()

    def fetch_metadata(self):
        metadata = {}
        for collection in self.collections:
            contents = self._get_file_contents(collection)

            if not contents:
                continue

            FILE_CONTENTS = contents.decoded_content.decode("utf-8")
            collection_xml = XmlEditor(FILE_CONTENTS)

            tree_root = collection_xml.fetch_treeroot()
            document_type = collection_xml.fetch_document_type()

            metadata[collection.config_folder] = {
                "tree_root": tree_root,
                "document_type": document_type,
            }
        return metadata
