"""
you need to run this script in the root of the repository that from which the file was deleted, in this case the root of the sinequa_configs repository.
"""

import subprocess


def get_git_log():
    # Run the git log command and capture the output
    result = subprocess.run(
        ["git", "log", "--diff-filter=D", "--pretty=format:%H %s", "--name-status", "--all"],
        capture_output=True,
        text=True,
    )
    return result.stdout


def parse_git_log(log_output, target_files):
    # Split the log output into lines
    lines = log_output.splitlines()

    # Variables to hold the current commit hash, message, and file path
    current_commit = None
    deleted_files_info = []

    # Iterate through each line of the log output
    for line in lines:
        if line.startswith("D"):
            # If the line starts with D, it's a deleted file path
            file_path = line[1:].strip()
            if any(target in file_path for target in target_files):
                deleted_files_info.append((current_commit, file_path))
        else:
            # Otherwise, it's a commit hash and message
            parts = line.split(" ", 1)
            if len(parts) == 2:
                current_commit = parts[0]

    return deleted_files_info


def restore_files(deleted_files_info):
    # Iterate over the list of deleted files and restore them
    for commit_hash, file_path in deleted_files_info:
        try:
            print(f"Restoring {file_path} from commit {commit_hash}")
            subprocess.run(["git", "checkout", f"{commit_hash}^", "--", file_path], check=True)
            print(f"Restored {file_path}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to restore {file_path}: {e}")


def main():
    # List of possible files to restore
    target_files = [
        "solar_and_heliospheric_observatory_soho/default.xml",
        "another_possible_path/default.xml",
        # Add more files as needed
    ]

    # Get the git log output
    log_output = get_git_log()

    # Parse the git log for the target files
    deleted_files_info = parse_git_log(log_output, target_files)

    # Restore the files to the working directory
    restore_files(deleted_files_info)


if __name__ == "__main__":
    main()
