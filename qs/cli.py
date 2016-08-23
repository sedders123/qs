import click
import os
import json
from typing import List


def _load_config() -> None:
    if _config_exists():
        with open('config.json', 'r') as f:
            config = json.load(f)
    else:
        config = _create_config()
    return config


def _config_exists() -> None:
    if os.path.isfile('config.json'):
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


@click.group(invoke_without_command=True)
@click.option('--base-dir', '-p', is_flag=True, help='Base Projects Folder')
@click.pass_context
def main(ctx, base_dir):
    """A simple CLI to aid in common, repetitive development tasks"""
    config = _load_config()
    if base_dir:
        config["BASE_DIR"] = base_dir
    else:
        click.echo(ctx.get_help())
