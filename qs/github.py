import click
import requests
import os

import qs.utils as utils
import qs.git as git
import qs.helpers as helpers

GITHUB_API_BASE = "https://api.github.com"


def get_github_username(token):
    endpoint = "/user"
    url = GITHUB_API_BASE + endpoint
    r = requests.get(url, headers={'Authorization': 'token {}'.format(token)})
    return r.json()["login"]


def _create_pull_request_request_body(ctx, story_id, story_description,
                                      branch, base="master", body=""):
    token = ctx.obj["CONFIG"]["GITHUB_TOKEN"]
    username = get_github_username(token)
    title = "id:{0} {1}".format(story_id, story_description)
    head = "{0}:{1}".format(username, branch)
    request = {
        "title": title,
        "body": body,
        "head": head,
        "base": base
    }
    return request


def post_github_pull_request(ctx, remote_owner, remote_repo, request_body):
    token = ctx.obj["CONFIG"]["GITHUB_TOKEN"]
    endpoint = "/repos/{owner}/{repo}/pulls".format(owner=remote_owner,
                                                    repo=remote_repo)
    url = GITHUB_API_BASE + endpoint
    # Used for debugging
    # req = requests.Request('POST', url,
    #                       headers={'Authorization': 'token {}'.format(token)},
    #                       json=request_body)
    # prepared = req.prepare()
    # pretty_print_POST(prepared)
    r = requests.post(url,
                      headers={'Authorization': 'token {}'.format(token)},
                      json=request_body)


def pretty_print_POST(req):
    """
    Help debug requests
    """
    click.echo('{}\n{}\n{}\n\n{}\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
        '------------END------------',
    ))


def create_github_pull_request(ctx, repo):
    branch = git.get_current_git_branch(repo["path"])
    for remote in repo["remotes"]:
        if remote["type"] == "push":
            push_remote = remote
    remote_owner, remote_repo = git.parse_git_remote_url(push_remote["url"])
    project = helpers.get_project(ctx, repo["path"])
    story_id, story_description = helpers.get_current_story(ctx, project)
    # TODO: Allow different base branhces and bodies of pull requests
    request_body = _create_pull_request_request_body(ctx, story_id,
                                                     story_description, branch)
    post_github_pull_request(ctx, remote_owner, remote_repo, request_body)
