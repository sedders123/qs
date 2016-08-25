import click
import os
import json
import subprocess
from typing import List

APP_DIR = click.get_app_dir("qs") + "/"
CONFIG_PATH = APP_DIR + "config.json"
PROJECTS_PATH = APP_DIR + "projects.json"


class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def _load_file(file: str) -> None:
    if _file_exists(file):
        with open(file, 'r') as f:
            file_contents = json.load(f)
    else:
        file_contents = _create_file(file)
    return file_contents


def _file_exists(file: str) -> None:
    if os.path.isfile(file):
        return True
    else:
        return False


def _create_file(file: str) -> None:
    if not os.path.exists(APP_DIR):
        os.makedirs(APP_DIR)
    if file[len(APP_DIR):] == "config.json":
        file_contents = {'BASE_DIR': os.path.expanduser("~/git/")}
    elif file[len(APP_DIR):] == "projects.json":
        file_contents = {}
    with open(file, 'w') as f:
        json.dump(file_contents, f)
    return file_contents


def _get_sub_dirs(base_dir: str) -> List[str]:
    return list(filter(lambda x: os.path.isdir(os.path.join(base_dir, x)), os.listdir(base_dir)))


def _get_git_repos(dirs: List[str], base_dir: str) -> List[str]:
    repos = []
    for directory in dirs:
        path = os.path.join(base_dir, directory + "/.git/")
        if os.path.isdir(path):
            repos.append(base_dir + directory)
    return repos


def _parse_raw_git_branch(raw_branch: str):
    branch_text = raw_branch.decode("utf-8")
    branch = branch_text[10:-1]
    return branch


def _sync_repo(repo: str, base_dir: str):
    repo_name = repo[len(base_dir):]
    click.echo("Synching Repositry: {}".format(repo_name))
    with cd(repo):
        os.system("git pull upstream master")
    click.echo("-"*80)  # Fill terminal


def _sync_repos(repos: List[str], base_dir: str):
    for repo in repos:
        with cd(repo):
            raw_branch = subprocess.check_output("git status | head -1", shell=True)
            branch = _parse_raw_git_branch(raw_branch)
            if branch == "master":
                _sync_repo(repo, base_dir)


@click.group()
@click.pass_context
def main(ctx):
    """A simple CLI to aid in common, repetitive development tasks"""
    ctx.obj = {}
    ctx.obj['CONFIG'] = _load_file(CONFIG_PATH)


@main.command()
@click.option('--base-dir', '-p', is_flag=True, help='Base Projects Folder')
def config(ctx, base_dir):
    config = _load_file(CONFIG_PATH)
    if base_dir:
        config["BASE_DIR"] = base_dir


@main.command()
def sync():
    """Syncs all projects in the base directory"""
    config = _load_file(CONFIG_PATH)
    base_dir = config['BASE_DIR']
    click.echo(APP_DIR)
    dirs = _get_sub_dirs(base_dir)
    repos = _get_git_repos(dirs, base_dir)
    _sync_repos(repos, base_dir)


@main.group()
@click.pass_context
def project(ctx):
    ctx.obj['PROJECTS'] = _load_file(PROJECTS_PATH)


@project.command(name="add")
@click.argument('project_name')
def project_add(project_name):
    click.echo(project_name)


@main.command()
def test():
    click.echo(os.getcwd())
