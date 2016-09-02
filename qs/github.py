import click
import requests
import os

import qs.git as git
import qs.helpers as helpers

GITHUB_API_BASE = "https://api.github.com"


def create_github_pull_request(ctx, repo, branch, remote):
    # TODO: Complete this function
    token = ctx.obj["CONFIG"]["GITHUB_TOKEN"]
    remote_owner, remote_repo = git.parse_git_remote_url(remote["url"])
    endpoint = "/repos/{owner}/{repo}/pulls".format(owner=remote_owner,
                                                    repo=remote_repo)
    url = GITHUB_API_BASE + endpoint
    title = "id:{0} {1}".format(story_id, story_description)
    if not body:
        body = ""
    head = "{0}:{1}".format(username, branch)
    if not base:
        base = "master"
    request = {
        "title": title,
        "body": body,
        "head": head,
        "base": base
    }
