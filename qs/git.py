import os
import subprocess
import click

import qs.utils as utils


def git_checkout(repo_path, branch):
    with utils.cd(repo_path):
        os.system("git checkout {}".format(branch))


def git_delete_branch(repo_path, branch):
    with utils.cd(repo_path):
        os.system("git branch -d {}".format(branch))


def git_stage_all(repo_path):
    with utils.cd(repo_path):
        os.system("git add .")


def git_commit(repo_path, commit_message):
    with utils.cd(repo_path):
        os.system("git commit -m '{0}'".format(commit_message))


def git_push_branch(repo_path, branch):
    with utils.cd(repo_path):
        os.system("git push origin {0}".format(branch))


def git_list_remotes(repo_path):
    with utils.cd(repo_path):
        return subprocess.check_output("git remote -v", shell=True)


def sync_repo(ctx, repo_path, upstream):
    repo_name = get_repo_name(ctx, repo_path)
    click.echo("Synching Repositry: {}".format(repo_name))
    with utils.cd(repo_path):
        os.system("git pull {} master".format(upstream))
    click.echo("-"*80)  # Fill terminal


def sync_repos(ctx, repos, upstream):
    for repo in repos:
        with utils.cd(repo):
            raw_branch = subprocess.check_output("git status | head -1",
                                                 shell=True)
            branch = parse_raw_git_branch(raw_branch)
            if branch == "master":
                sync_repo(ctx, repo, upstream)


def parse_raw_git_branch(raw_branch):
    branch_text = raw_branch.decode("utf-8")
    branch = branch_text[10:-1]
    return branch


def get_repo_name(ctx, repo_path):
    return repo_path.split("/")[-1]


def get_current_git_branch(repo_path):
    with utils.cd(repo_path):
        raw_branch = subprocess.check_output("git status | head -1",
                                             shell=True)
        branch = parse_raw_git_branch(raw_branch)
    return branch


def create_git_branch(ctx, repo_path, branch_name):
    repo_name = get_repo_name(ctx, repo_path)
    click.echo("Creating branch {0} for {1}".format(branch_name, repo_name))
    with utils.cd(repo_path):
        os.system("git checkout -b {}".format(branch_name))


def get_git_repos(dirs, warn=False):
    repos = []
    for directory in dirs:
        if os.path.isdir(directory + "/.git/"):
            repos.append(os.path.normpath(directory))
        elif warn:
            click.echo("{} is not a git repositry".format(directory))
    return repos


def get_repo_paths(repos):
    paths = []
    for repo in repos:
        paths.append(repo["path"])
    return paths


def get_commit_message(ctx, repo_path):
    repo_name = get_repo_name(ctx, repo_path)
    commit_message = click.prompt("Please enter a commit message")
    return commit_message


def get_changed_repo(repo):
    with utils.cd(repo["path"]):
        diff = subprocess.check_output("git diff",
                                       shell=True)
        return not diff == b''


def get_changed_repos(ctx, project):
    changed_repos = []
    repos = ctx.obj["PROJECTS"][project]["repos"]
    for repo in repos:
        if get_changed_repo(repo):
            changed_repos.append(repo)
    return changed_repos


def tear_down_story(ctx, project):
    repos = ctx.obj["PROJECTS"][project]["repos"]
    for repo in repos:
        current_branch = get_current_git_branch(repo["path"])
        git_checkout(repo["path"], "master")
        git_delete_branch(repo["path"], current_branch)


def get_remotes(repo_path):
    raw_remotes = git_list_remotes(repo_path)
    return parse_raw_git_remotes(raw_remotes)


def create_repos(repo_list):
    repos = []
    for repo in repo_list:
        remotes = get_remotes(repo)
        repos.append({"path": repo, "remotes": remotes})
    return repos


def parse_raw_git_remotes(raw_remotes):
    # This function is awful.
    # TODO: Rewrite this
    remotes = []
    raw_remotes_list = raw_remotes.splitlines()
    for raw_remote in raw_remotes_list:
        raw_remote = raw_remote.decode("utf-8")
        remote_name = raw_remote.split("\t")[0]
        raw_remote_url = raw_remote.split("\t")[1]
        remote_url = raw_remote_url.split(" ")[0]
        remote_type = raw_remote_url.split(" ")[1].strip("()")
        remote = {"name": remote_name, "url": remote_url, "type": remote_type}
        remotes.append(remote)
    return remotes


def parse_git_remote_url(remote_url):
    # TODO: Make this support http/https
    if "@" in remote_url:
        remote = remote_url.split(":")[1]
        remote_owner = remote.split("/")[0]
        remote_repo_full = remote.split("/")[1]
        remote_repo = remote_repo_full.split(".git")[0]
    return remote_owner, remote_repo
