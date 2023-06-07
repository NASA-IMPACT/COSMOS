from django.conf import settings
from github import Github


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

    def _update_file_contents(self, collection):
        """
        Update file contents on GitHub
        """
        FILE_PATH = self._get_config_file_path(collection)
        contents = self.repo.get_contents(FILE_PATH, ref=self.github_branch)

        FILE_CONTENTS = contents.decoded_content.decode("utf-8")
        # add two lines to the end of the file. this is just to test the pipeline
        FILE_CONTENTS = FILE_CONTENTS + "\n\n"

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
        self.create_pull_request()
