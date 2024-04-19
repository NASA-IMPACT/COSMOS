from django.conf import settings
from github import Github
from github.GithubException import GithubException, UnknownObjectException

from config_generation.db_to_xml import XmlEditor

from ..models.collection_choice_fields import CurationStatusChoices


class GitHubHandler:
    def __init__(self, collections=None, *args, **kwargs):
        self.github_token = settings.GITHUB_ACCESS_TOKEN
        self.g = Github(self.github_token)
        self.repo = self.g.get_repo(f"{settings.SINEQUA_CONFIGS_GITHUB_REPO}")
        self.master_branch = settings.SINEQUA_CONFIGS_REPO_MASTER_BRANCH
        self.dev_branch = settings.SINEQUA_CONFIGS_REPO_DEV_BRANCH
        self.webapp_pr_branch = settings.SINEQUA_CONFIGS_REPO_WEBAPP_PR_BRANCH
        self.collections = collections
        # if we still need operations performed on a collection list
        # we should refactor, as this functionality should not be a
        # part of the base GithubHandler class.
        # maybe it should just be passed to an individual method

    def _get_file_contents(self, file_path, strict=True):
        """
        try to get file contents, first from the pr branch and then from the dev branch
        if strict is True, raise an exception if the file is not found
        """

        try:
            contents = self.repo.get_contents(file_path, ref=self.webapp_pr_branch)
        except UnknownObjectException:
            try:
                contents = self.repo.get_contents(file_path, ref=self.dev_branch)
            except UnknownObjectException:
                if strict:
                    raise Exception(
                        f"File {file_path} not found on {self.dev_branch} or {self.webapp_pr_branch} branches"
                    )
                return None

        return contents

    def check_file_exists(self, file_path):
        """
        Check if file exists on GitHub
        """

        if self._get_file_contents(file_path, strict=False) is None:
            return False
        else:
            return True

    def create_file(self, file_path, file_string, branch=None):
        """
        Create file contents on GitHub
        if no branch is provided, it will default to the webapp_pr_branch
        """

        if not branch:
            branch = self.webapp_pr_branch

        if self.check_file_exists(file_path):
            raise Exception(f"File {file_path} already exists on GitHub")

        COMMIT_MESSAGE = f"Webapp: Create {file_path}"

        self.repo.create_file(
            file_path,
            COMMIT_MESSAGE,
            file_string,
            branch=branch,
        )

    def create_or_update_file(self, file_path, file_string, branch=None):
        """
        Update file contents on GitHub
        if no branch is provided, it will default to the webapp_pr_branch
        """

        if not branch:
            branch = self.webapp_pr_branch

        if self.check_file_exists(file_path):
            contents = self._get_file_contents(file_path)
            COMMIT_MESSAGE = f"Webapp: Update {file_path}"

            self.repo.update_file(
                contents.path,
                COMMIT_MESSAGE,
                file_string,
                contents.sha,
                branch=branch,
            )
        else:
            self.create_file(file_path, file_string, branch)

    def update_config_with_current_rules(self, collection):
        """
        DEPRECATED?
        this runs the update_config_xml method from the collection model
        which adds the latest rules to the xml file
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
            self.update_config_with_current_rules(collection)
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

    def _get_config_folder(self, collection_folder):
        return collection_folder.removeprefix("sources/SDE/")

    def _get_list_of_collections(self):
        BASE_PATH = "sources/SDE"
        collections = self.repo.get_contents(BASE_PATH, ref=self.dev_branch)
        collection_folders = [
            collection.path
            for collection in collections
            if ".xml" not in collection.path  # to prevent source.xml from being included
        ]
        return collection_folders

    def _get_contents_from_path(self, path):
        # we don't need to check if the file exists because we already did that in _get_list_of_collections
        contents = self.repo.get_contents(path, ref=self.dev_branch)
        FILE_CONTENTS = contents.decoded_content.decode("utf-8")
        collection_xml = XmlEditor(FILE_CONTENTS)
        return collection_xml

    def get_collections_from_github(self, config_folders=[]):
        # get a list of folders in sources/SDE/ from the dev branch on github
        collection_folders = self._get_list_of_collections()

        # create a dict of all collections and their metadata
        collection_list = []

        # for each folder in the list, get the metadata: config_folder, name, url, division, tree_root, document_type
        for collection_folder in collection_folders:
            config_folder = self._get_config_folder(collection_folder)
            collection_xml_file_path = self._get_config_file_path(config_folder)
            collection_xml = self._get_contents_from_path(collection_xml_file_path)

            division, name = collection_xml.fetch_division_name()

            if not division or not name:
                print(f"Skipping {config_folder} because it has no division or name")
                continue

            collection_dict = {
                "config_folder": config_folder,
                "name": name,
                "url": collection_xml.fetch_url(),
                "division": division,
                "document_type": collection_xml.fetch_document_type(),
                "connector": collection_xml.fetch_connector(),
            }
            collection_list.append(collection_dict)

        # return the list of collections and their metadata
        return collection_list

    def sync_rules_with_github(self, config_folders=[]):
        pass
