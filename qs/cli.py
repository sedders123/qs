import click
import os
import json
from typing import List

CONFIG_PATH = click.get_app_dir("qs") + "config.json"


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
    with open('config.json', 'w') as f:
        json.dump(config, f)
    return config


def _get_sub_dirs(base_dir: str) -> List[str]:
    return list(filter(lambda x: os.path.isdir(os.path.join(base_dir, x)), os.listdir(base_dir)))

def _get_git_repos(dirs: List[str], base_dir: str) -> List[str]:
    pass


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
    git_repos = _get_git_repos(dirs, base_dir)

@main.command()
def test():
    click.echo(os.getcwd())
