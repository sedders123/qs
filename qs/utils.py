import os
import json
import click

import qs.constants as constants


class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def load_file(file):
    if file_exists(file):
        with open(file, 'r') as f:
            file_contents = json.load(f)
    else:
        file_contents = create_file(file)
    return file_contents


def file_exists(file):
    return os.path.isfile(file)


def save_file(file, contents):
    with open(file, 'w') as f:
        json.dump(contents, f)


def create_file(file):
    if not os.path.exists(constants.APP_DIR):
        os.makedirs(constants.APP_DIR)
    if file[len(constants.APP_DIR):] == "config.json":
        file_contents = {
                         'BASE_DIR': os.path.expanduser("~/Projects/"),
                         'GITHUB_TOKEN': ""
                        }
    elif file[len(constants.APP_DIR):] == "projects.json":
        file_contents = {}
    save_file(file, file_contents)
    return file_contents
