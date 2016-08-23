import click
import os
import json


def _load_config():
    if _config_exists():
        with open('config.json', 'r') as f:
            config = json.load(f)
    else:
        config = _create_config()
    return config

def _config_exists():
    if os.path.isfile('config.json'):
        return true
    else:
        return false

def _create_config():
    config = { 'BASE_DIR': os.path.expanduser("~")}


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
