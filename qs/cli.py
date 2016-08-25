import click
import os
import json
from typing import List

CONFIG_PATH = click.get_app_dir("qs") + "config.json"

class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def _load_config() -> None:
    if _config_exists():
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
    else:
        config = _create_config()
    return config


def _config_exists() -> None:
    if os.path.isfile(CONFIG_PATH):
        return True
    else:
        return False


def _create_config() -> None:
    config = {'BASE_DIR': os.path.expanduser("~/Projects")}
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f)
    return config


def _get_sub_dirs(base_dir: str) -> List[str]:
    return list(filter(lambda x: os.path.isdir(os.path.join(base_dir, x)), os.listdir(base_dir)))


def _get_git_repos(dirs: List[str], base_dir: str) -> List[str]:
    repos = []
    for directory in dirs:
        path = os.path.join(base_dir, directory + "/.git/")
        if os.path.isdir(path):
            repos.append(base_dir + "/" + directory)
    return repos

def _parse_git_branch(raw_branch: str):
    pass

def _sync_repos(repos: List[str]):
    #for repo in repos:
    #    with cd(repo):
    #        click.echo(str(os.system("git status | head -1")))
    with cd(repos[0]):
        raw_branch = str(os.system("git status | head -1"))
        branch = _parse_git_branch(raw_branch)


@click.group()
@click.pass_context
def main(ctx):
    """A simple CLI to aid in common, repetitive development tasks"""
    ctx.obj = {}
    ctx.obj['CONFIG'] = _load_config()


@main.command()
@click.option('--base-dir', '-p', is_flag=True, help='Base Projects Folder')
def config(ctx, base_dir):
    config = _load_config()
    if base_dir:
        config["BASE_DIR"] = base_dir

@main.command()
@click.pass_context
def sync(ctx):
    base_dir = ctx.obj['CONFIG']['BASE_DIR']
    dirs = _get_sub_dirs(base_dir)
    repos = _get_git_repos(dirs, base_dir)
    _sync_repos(repos)

@main.command()
def test():
    click.echo(os.getcwd())
