"""
this file deletes the files associated with a folder name as defined in config.py
it will delete
    - config folders
    - commands
    - jobs
"""
import glob
import os
import shutil

from config import collections_to_delete as collection_names


def delete_folders_by_name(collection_names, directory):
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in dirs:
            if name in collection_names:
                folder_path = os.path.join(root, name)
                shutil.rmtree(folder_path)
                print(f"Deleted folder: {folder_path}")


def delete_xml_files_by_name(collection_names, directory):
    """
    this deletes files that match the sinequa pattern of
    command.collectioncache.SMD.PDS_Users_Guides_Website.xml
    where the name is surrounded by periods. this will prevent accidental matches to
    similar names, but may leave a few stray undeleted files
    """
    # Define the pattern to match the files
    for collection_name in collection_names:
        pattern = f"*.{collection_name}.xml"

        # Use glob to find all files in the directory that match the pattern
        for file_path in glob.glob(os.path.join(directory, pattern)):
            try:
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            except OSError as e:
                print(f"Error deleting file {file_path}: {e.strerror}")


delete_folders_by_name(collection_names, "../sinequa_configs/sources/SMD/")
delete_xml_files_by_name(collection_names, "../sinequa_configs/commands/")
delete_xml_files_by_name(collection_names, "../sinequa_configs/jobs/")
