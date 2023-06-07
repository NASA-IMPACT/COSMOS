from django.conf import settings
from github import Github


class GitHubHandler:
    def __init__(self, collection, *args, **kwargs):
        self.github_token = settings.GITHUB_ACCESS_TOKEN
        self.github_repo = settings.SINEQUA_CONFIGS_GITHUB_REPO
        self.github_branch = settings.GITHUB_BRANCH_FOR_WEBAPP
        self.g = Github(self.github_token)
        self.repo = self.g.get_repo(f"{self.github_repo}")
        self.dev_branch = self.repo.default_branch
        self.collection = collection

    def update_file_contents(self, file_path, file_contents, commit_message):
        """
        Update file contents on GitHub
        """
        g = self.github_handler
        repo = g.get_repo(f"{self.github_username}/{self.github_repo}")
        contents = repo.get_contents(file_path, ref=self.github_branch)
        repo.update_file(
            contents.path,
            commit_message,
            file_contents,
            contents.sha,
            branch=self.github_branch,
        )

    def push_config_to_github(self):
        print(f"pushing config to github for collection {self.collection.name}")
