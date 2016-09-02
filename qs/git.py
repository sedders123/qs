import os
import subprocess

from .utils import *


def git_checkout(repo, branch):
    with cd(repo):
        os.system("git checkout {}".format(branch))


def git_delete_branch(repo, branch):
    with cd(repo):
        os.system("git branch -d {}".format(branch))


def git_stage_all(repo):
    with cd(repo):
        os.system("git add .")


def git_commit(repo, commit_message):
    with cd(repo):
        os.system("git commit -m '{0}'".format(commit_message))


def git_push_branch(repo, branch):
    with cd(repo):
        os.system("git push origin {0}".format(branch))


def git_list_remotes(repo):
    with cd(repo):
        return subprocess.check_output("git remote -v", shell=True)


def sync_repo(ctx, repo, upstream):
    repo_name = get_repo_name(ctx, repo)
    click.echo("Synching Repositry: {}".format(repo_name))
    with cd(repo):
        os.system("git pull {} master".format(upstream))
    click.echo("-"*80)  # Fill terminal


def sync_repos(ctx, repos, upstream):
    for repo in repos:
        with cd(repo):
            raw_branch = subprocess.check_output("git status | head -1",
                                                 shell=True)
            branch = parse_raw_git_branch(raw_branch)
            if branch == "master":
                sync_repo(ctx, repo, upstream)


def parse_raw_git_branch(raw_branch):
    branch_text = raw_branch.decode("utf-8")
    branch = branch_text[10:-1]
    return branch


def get_repo_name(ctx, repo):
    return repo.split("/")[-1]


def get_current_git_branch(repo):
    with cd(repo):
        raw_branch = subprocess.check_output("git status | head -1",
                                             shell=True)
        branch = parse_raw_git_branch(raw_branch)
    return branch


def create_git_branch(ctx, repo, branch_name):
    repo_name = get_repo_name(ctx, repo)
    click.echo("Creating branch {0} for {1}".format(branch_name, repo_name))
    with cd(repo):
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


def get_commit_message(ctx, repo):
    repo_name = get_repo_name(ctx, repo)
    commit_message = click.prompt("Please enter a commit message")
    return commit_message


def get_changed_repo(repo):
    with cd(repo):
        diff = subprocess.check_output("git diff",
                                       shell=True)
        return diff == b''


def get_changed_repos(ctx, project):
    changed_repos = []
    repos = ctx.obj["PROJECTS"][project][repos]
    for repo in repo:
        get_changed_repo(repo)
        changed_repos.append(repo)
    return changed_repos


def process_unused_repos(ctx, project, changed_repos):
    repos = ctx.obj["PROJECTS"][project][repos]
    for repo in repos:
        if repo not in changed_repos:
            current_branch = get_current_git_branch(repo)
            git_checkout(repo, "master")
            git_delete_branch(repo, current_branch)


def get_remotes(repo):
    raw_remotes = git_list_remotes(repo)
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
