import click

from .utils import *

def edit_config(ctx, base_dir, github_token):
    config = ctx.obj['CONFIG']
    if base_dir:
        config["BASE_DIR"] = base_dir
    if github_token:
        config["GITHUB_TOKEN"] = github_token
    save_file(CONFIG_PATH, config)
