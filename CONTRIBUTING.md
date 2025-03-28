Thank you for your interest in contributing to COSMOS! We welcome contributions and appreciate your help in making this project better. Please follow the guidelines below to ensure a smooth contribution process.

## Pull Requests

### Prerequisites

- **GitHub CLI (`gh`)**: Make sure you have the GitHub CLI installed. If not, you can install it from [GitHub CLI installation page](https://cli.github.com/).

### 1. **Create an Issue on the Repo**

1. **Navigate to Your Repository**:

    ```bash
    $ cd path/to/your/repository
    ```

2. **Create an Issue**:
Use the `gh issue create` command to create a new issue.

    ```bash
    $ gh issue create --title "Issue Title" --body "Description of the issue"
    ```

    After running this command, you’ll get an issue number in the output. Note this number as it will be used to create a branch.


### 2. **Create a Branch for the Issue**

1. **Create a Branch**:
Use the `gh` CLI to create a branch associated with the issue. The `gh` CLI can automatically create a branch for you based on the issue number. In this case, the `<issue_number>` is 989.

    ```bash
    $ gh issue develop -c 989
    github.com/NASA-IMPACT/COSMOS/tree/989-make-coding-syntax-consistent
    From https://github.com/NASA-IMPACT/COSMOS
     * [new branch]      989-make-coding-syntax-consistent -> origin/989-make-coding-syntax-consistent

    ```

    This command creates a new branch named `<issue_number>-issue` and switches to it. This branch will be used to work on the issue.

2. **Make Your Changes and Push:**
Edit files, add code, or make any changes needed to address the issue. Commit your changes and push the branch to the remote repository.

    ```bash
    git add .
    git commit -m "Fixes issue #<issue_number>"
    git push origin <issue_number>-issue
    ```


### 3. **Create a Pull Request**

1. **Create the Pull Request**:
After pushing the branch, create a pull request using the `gh pr create` command:

    ```bash
    gh pr create --base dev --head <issue_number>-issue --title "Title of the Pull Request" --body "Description of the changes"
    ```

    - **`-base`**: The base branch you want to merge your changes into (`dev` in our case)
    - **`-head`**: The branch that contains your changes (e.g., `<issue_number>-issue`).
    - **`-title`**: The title of the pull request.
    - **`-body`**: The description or body of the pull request.

    This command will create a pull request from your branch into the base branch specified.

2. **Review and Merge**:
Once the pull request is created, we will review it on GitHub and merge it if everything looks good. If any changes are required, we might ask you to make adjustments before the merge.
