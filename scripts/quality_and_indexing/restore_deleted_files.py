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


def parse_git_log(log_output, target_file):
    # Split the log output into lines
    lines = log_output.splitlines()

    # Variables to hold the current commit hash, message, and file path
    current_commit = None
    current_message = None
    deleted_files = []

    # Iterate through each line of the log output
    for line in lines:
        if line.startswith("D"):
            # If the line starts with D, it's a deleted file path
            file_path = line[1:].strip()
            if target_file in file_path:
                deleted_files.append((current_commit, current_message, file_path))
        else:
            # Otherwise, it's a commit hash and message
            parts = line.split(" ", 1)
            if len(parts) == 2:
                current_commit = parts[0]
                current_message = parts[1]

    return deleted_files


def main():
    # The target file or path pattern to search for
    target_file = "solar_and_heliospheric_observatory_soho/default.xml"

    # Get the git log output
    log_output = get_git_log()

    # Parse the git log for the target file
    deleted_files = parse_git_log(log_output, target_file)

    # Print the results
    if deleted_files:
        for commit_hash, message, file_path in deleted_files:
            print(f"Commit: {commit_hash}")
            print(f"Message: {message}")
            print(f"Deleted File: {file_path}")
            print("-" * 40)
    else:
        print(f"No deletions found for {target_file}")


if __name__ == "__main__":
    main()
