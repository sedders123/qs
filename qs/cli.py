import click
import os

from qs.constants import *
from qs.helpers import *
from qs.utils import *
from qs.git import *
import qs.github as github


def _edit_config(ctx, base_dir, github_token):
    config = ctx.obj['CONFIG']
    if base_dir:
        config["BASE_DIR"] = base_dir
    if github_token:
        config["GITHUB_TOKEN"] = github_token
    save_file(CONFIG_PATH, config)


def _sync_projects(ctx, projects):
    for project in projects:
        _sync_project(ctx, project)


def _sync_project(ctx, project):
    upstream = project["upstream"]
    repo_paths = get_repo_paths(project["repos"])
    click.echo(repo_paths)
    sync_repos(ctx, repo_paths, upstream)


def _create_project(ctx, name, repos, upstream):
    projects = ctx.obj['PROJECTS']
    if upstream is None:
        upstream = "upstream"
    projects[name] = {"repos": repos, "stories": [], "upstream": upstream}
    save_file(PROJECTS_PATH, projects)


def _create_story(ctx, story_id, description, project_name):
    projects = ctx.obj["PROJECTS"]
    repos = projects[project_name]["repos"]
    stories = projects[project_name]["stories"]
    upstream = projects[project_name]["upstream"]
    for repo in repos:
        sync_repo(ctx, repo["path"], upstream)
        create_story_branch(ctx, repo["path"], story_id, description)
    story = {"id": story_id, "description": description, "status": "OPEN"}
    stories.append(story)
    save_stories(ctx, project_name, stories)


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
    _edit_config(ctx, base_dir, github_token)


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
    repo_list = get_full_path_repo_list(ctx, raw_repo_list)
    repos = create_repos(repo_list)
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
        project = get_project(ctx, cwd)
    if can_create_story(ctx, project):
        _create_story(ctx, story_id, description, project)
    else:
        current_id, current_description = get_current_story(ctx, project)
        click.echo("Story {0} {1} is currently in progress for this project"
                   .format(current_id, current_description))


@story.command(name="push")
@click.option('--project')
@click.pass_context
def story_push(ctx, project):
    if not project:
        cwd = os.getcwd()
        project = get_project(ctx, cwd)
    story_id, description = get_current_story(ctx, project)
    changed_repos = ctx.obj["PROJECTS"][project]["repos"]  # get_changed_repos(ctx, project)
    # process_unused_repos(ctx, project, changed_repos)
    for repo in changed_repos:
        #sync_repo(ctx, repo["path"], ctx.obj["PROJECTS"][project]["upstream"])
        #commit_message = get_commit_message(ctx, repo["path"])
        #git_stage_all(repo["path"])
        #git_commit(repo["path"], commit_message)
        #current_branch = get_current_git_branch(repo["path"])
        #git_push_branch(repo["path"], current_branch)
        github.create_github_pull_request(ctx, repo)
