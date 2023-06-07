from django.conf import settings


class GitHub:
    def __init__(self, *args, **kwargs):
        self.github_token = settings.GITHUB_ACCESS_TOKEN
        self.github_username = settings.GITHUB_USERNAME
        self.github_repo = settings.GITHUB_REPO
        self.github_branch = settings.GITHUB_BRANCH
        self.github_handler = GitHub(self.github_token)

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
