import click
import os
import json
import subprocess
import requests

from .constants import *
from .helpers import *
from .utils import *


def _get_sub_dirs(base_dir):
    return list(filter(lambda x: os.path.isdir(os.path.join(base_dir, x)), os.listdir(base_dir)))


def _get_git_repos(dirs, warn=False):
    repos = []
    for directory in dirs:
        if os.path.isdir(directory + "/.git/"):
            repos.append(os.path.normpath(directory))
        elif warn:
            click.echo("{} is not a git repositry".format(directory))
    return repos


def _parse_raw_git_branch(raw_branch):
    branch_text = raw_branch.decode("utf-8")
    branch = branch_text[10:-1]
    return branch


def _sync_repo(ctx, repo, upstream):
    repo_name = _get_repo_name(ctx, repo)
    click.echo("Synching Repositry: {}".format(repo_name))
    with cd(repo):
        os.system("git pull {} master".format(upstream))
    click.echo("-"*80)  # Fill terminal


def _sync_repos(ctx, repos, upstream):
    for repo in repos:
        with cd(repo):
            raw_branch = subprocess.check_output("git status | head -1",
                                                 shell=True)
            branch = _parse_raw_git_branch(raw_branch)
            if branch == "master":
                _sync_repo(ctx, repo, upstream)


def _sync_projects(ctx, projects):
    for project in projects:
        _sync_project(ctx, project)


def _sync_project(ctx, project):
    upstream = project["upstream"]
    repo_paths = _get_repo_paths(project["repos"])
    _sync_repos(ctx, repo_paths, upstream)


def _get_repo_paths(repos):
    paths = []
    for repo in repos:
        paths.append(repo["path"])
    return paths



def _create_project(ctx, name, repos, upstream):
    projects = ctx.obj['PROJECTS']
    if upstream is None:
        upstream = "upstream"
    projects[name] = {"repos": repos, "stories": [], "upstream": upstream}
    save_file(PROJECTS_PATH, projects)


def _get_full_path_dir_list(ctx, dirs, warn=False):
    cwd = os.getcwd() + "/"
    base_dir = ctx.obj['CONFIG']["BASE_DIR"]
    dir_list = []
    for directory in dirs:
        if os.path.isdir(cwd + directory):
            dir_list.append(cwd + directory)
        elif os.path.isdir(base_dir + directory):
            dir_list.append(base_dir + directory)
        elif os.path.isdir(directory):
            dir_list.append(directory)
        elif warn:
            click.echo("Can not find directory {}".format(directory))
            click.echo("Please enter the directory's full path")
    return dir_list


def _get_full_path_repo_list(ctx, repo_list):
    full_path_repo_list = []
    dir_list = _get_full_path_dir_list(ctx, repo_list, warn=True)
    full_path_repo_list = _get_git_repos(dir_list, warn=True)
    if os.name == "nt":
        windows_full_path_repo_list = []
        for repo in full_path_repo_list:
            windows_repo = repo.replace("\\\\", "\\")
            windows_full_path_repo_list.append(windows_repo)
        return windows_full_path_repo_list
    return full_path_repo_list


def _get_projects(ctx, cwd):
    projects = ctx.obj["PROJECTS"]
    possible_projects = []
    for project in projects:
        if cwd in projects[project]["repos"]:
            possible_projects.append(project)
    if len(possible_projects) == 1:
        project = possible_projects[0]
    elif len(possible_projects) == 0:
        click.echo("The current directory is not assigned to a project.")
        click.echo("Create one before starting a story")
    else:
        project = _get_project(possible_projects)
    return project


def _get_project(possible_projects):
    click.echo("Multiple projects found. Please select one: ")
    for i, project in enumerate(possible_projects):
        click.echo("{0}.) {1}".format(i + 1, project))
    user_response = click.prompt("Enter choice", default=1)
    return possible_projects[user_response-1]


def _can_create_story(ctx, project):
    projects = ctx.obj["PROJECTS"]
    stories = projects[project]["stories"]
    for story in stories:
        if story["status"] == "OPEN":
            return False
    return True


def _get_repo_name(ctx, repo):
    base_dir = ctx.obj["CONFIG"]["BASE_DIR"]
    return repo[len(base_dir):]


def _get_current_git_branch(repo):
    with cd(repo):
        raw_branch = subprocess.check_output("git status | head -1",
                                             shell=True)
        branch = _parse_raw_git_branch(raw_branch)
    return branch


def _create_story_branch(ctx, repo, story_id, description):
    branch_name = story_id + "_" + description.replace(' ', '_')
    current_branch = _get_current_git_branch(repo)
    if current_branch == "master":
        _create_git_branch(ctx, repo, branch_name)
    else:
        repo_name = _get_repo_name(ctx, repo)
        click.echo("{} is currently on branch {}".format(repo_name, current_branch))
        response = click.confirm("Do you want to create the new branch anyway?")
        if response:
            _create_git_branch(ctx, repo, branch_name)
        else:
            click.echo("Skipping repositry {}".format(repo_name))


def _create_git_branch(ctx, repo, branch_name):
    repo_name = _get_repo_name(ctx, repo)
    click.echo("Creating branch {0} for {1}".format(branch_name, repo_name))
    with cd(repo):
        os.system("git checkout -b {}".format(branch_name))


def _save_stories(ctx, project, stories):
    projects = ctx.obj["PROJECTS"]
    projects[project]["stories"] = stories
    save_file(PROJECTS_PATH, projects)


def _create_story(ctx, story_id, description, project_name):
    projects = ctx.obj["PROJECTS"]
    repos = projects[project_name]["repos"]
    stories = projects[project_name]["stories"]
    for repo in repos:
        _sync_repo(ctx, repo)
        _create_story_branch(ctx, repo, story_id, description)
    story = {"id": story_id, "description": description, "status": "OPEN"}
    stories.append(story)
    _save_stories(ctx, project_name, stories)


def _get_current_story(ctx, project):
    project = ctx.obj["PROJECTS"][project]
    for story in project["stories"]:
        if story["status"] == "OPEN":
            return story["id"], story["description"]


def _get_commit_message(ctx, repo):
    repo_name = _get_repo_name(ctx, repo)
    commit_message = click.prompt("Please enter a commit message")
    return commit_message


def _get_changed_repo(repo):
    with cd(repo):
        diff = subprocess.check_output("git diff",
                                        shell=True)
        return diff == b''


def _get_changed_repos(ctx, project):
    changed_repos = []
    repos = ctx.obj["PROJECTS"][project][repos]
    for repo in repo:
        _get_changed_repo(repo)
        changed_repos.append(repo)
    return changed_repos


def _process_unused_repos(ctx, project, changed_repos):
    repos = ctx.obj["PROJECTS"][project][repos]
    for repo in repos:
        if not repo in changed_repos:
            current_branch = _get_current_git_branch(repo)
            _git_checkout(repo, "master")
            _git_delete_branch(repo, current_branch)


def _git_checkout(repo, branch):
    with cd(repo):
        os.system("git checkout {}".format(branch))


def _git_delete_branch(repo, branch):
    with cd(repo):
        os.system("git branch -d {}".format(branch))

def _git_stage_all(repo):
    with cd(repo):
        os.system("git add .")


def _git_commit(repo, commit_message):
    with cd(repo):
        os.system("git commit -m '{0}'".format(commit_message))

def _git_push_branch(repo, branch):
    with cd(repo):
        os.system("git push origin {0}".format(branch))


def _git_list_remotes(repo):
    with cd(repo):
        return subprocess.check_output("git remote -v", shell=True)


def _create_github_pull_request(repo, branch, remote):
    pass

# This function is awful.
# TODO: Rewrite this
def _parse_raw_git_remotes(raw_remotes):
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

def _get_remotes(repo):
    raw_remotes = _git_list_remotes(repo)
    return _parse_raw_git_remotes(raw_remotes)


def _create_repos(repo_list):
    repos = []
    for repo in repo_list:
        remotes = _get_remotes(repo)
        repos.append({"path": repo, "remotes": remotes})
    return repos


@click.group()
@click.pass_context
def main(ctx):
    """A simple CLI to aid in common, repetitive development tasks"""
    ctx.obj = {}
    ctx.obj['CONFIG'] = load_file(CONFIG_PATH)
    ctx.obj['PROJECTS'] = load_file(PROJECTS_PATH)


@main.command()
@click.option('--base-dir')
@click.option('--github-token')
@click.pass_context
def config(ctx, base_dir, github_token):
    edit_config(ctx, base_dir, github_token)


@main.command()
@click.argument('project_name', metavar='project', required=False)
@click.pass_context
def sync(ctx, project_name):
    """Syncs all projects"""
    projects = ctx.obj["PROJECTS"]
    if project_name:
        project = projects[project_name]
        _sync_project(ctx, project)
    else:
        _sync_projects(ctx, projects)


@main.command()
@click.pass_context
def test(ctx):
    click.echo(ctx.obj)


@main.group()
@click.pass_context
def project(ctx):
    pass


@project.command(name="add")
@click.argument('name')
@click.argument('repos', nargs=-1)
@click.option('--upstream')
@click.pass_context
def project_add(ctx, name, repos, upstream):
    raw_repo_list = list(repos)
    repo_list = _get_full_path_repo_list(ctx, raw_repo_list)
    repos = _create_repos(repo_list)
    _create_project(ctx, name, repos, upstream)


@project.command(name="list")
@click.argument('name', required=False)
@click.pass_context
def project_list(ctx, name):
    if name:
        try:
            click.echo(ctx.obj["PROJECTS"][name])
        except KeyError:
            click.echo("Project '{}' could not be found".format(name))
    else:
        click.echo(ctx.obj["PROJECTS"])


@main.group()
@click.pass_context
def story(ctx):
    pass


@story.command(name="new")
@click.argument('story_id', metavar="id")
@click.argument('description_tuple', nargs=-1, metavar="description")
@click.option('--project')
@click.pass_context
def story_new(ctx, story_id, description_tuple, project):
    story_id = str(story_id)
    description_list = list(description_tuple)
    description = " ".join(description_list)
    if not project:
        cwd = os.getcwd()
        project = _get_projects(ctx, cwd)
    if _can_create_story(ctx, project):
        _create_story(ctx, story_id, description, project)
    else:
        current_id, current_description = _get_current_story(ctx, project)
        click.echo("Story {0} {1} is currently in progress for this project".format(current_id, current_description))

@story.command(name="push")
@click.option('--project')
@click.pass_context
def story_push(ctx, project):
    if not project:
        cwd = os.getcwd()
        project = _get_projects(ctx, cwd)
    story_id, description = _get_current_story(ctx, project)
    changed_repos = _get_changed_repos(ctx, project)
    _process_unused_repos(ctx, project, changed_repos)
    for repo in changed_repos:
        _sync_repo(repo)
        commit_message = _get_commit_message(ctx, repo)
        _git_stage_all(repo)
        _git_commit(repo, commit_message)
        current_branch = _get_current_git_branch(repo)
        _git_push_branch(repo, current_branch)
        # TODO: _github_create_pull_request(repo)
