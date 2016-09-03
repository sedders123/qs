import click
import os

import qs.constants as constants
import qs.helpers as helpers
import qs.utils as utils
import qs.git as git
import qs.github as github
import qs.errors as errors


def _edit_config(ctx, base_dir, github_token):
    config = ctx.obj['CONFIG']
    if base_dir:
        config["BASE_DIR"] = base_dir
    if github_token:
        config["GITHUB_TOKEN"] = github_token
    utils.save_file(constants.CONFIG_PATH, config)


def _sync_projects(ctx, projects):
    for project in projects:
        _sync_project(ctx, project)


def _sync_project(ctx, project):
    upstream = project["upstream"]
    repo_paths = git.get_repo_paths(project["repos"])
    click.echo(repo_paths)
    git.sync_repos(ctx, repo_paths, upstream)


def _create_project(ctx, name, repos, upstream):
    projects = ctx.obj['PROJECTS']
    if upstream is None:
        upstream = "upstream"
    projects[name] = {"repos": repos, "stories": [], "upstream": upstream}
    utils.save_file(constants.PROJECTS_PATH, projects)


def _create_story(ctx, story_id, description, project_name):
    projects = ctx.obj["PROJECTS"]
    repos = projects[project_name]["repos"]
    stories = projects[project_name]["stories"]
    upstream = projects[project_name]["upstream"]
    for repo in repos:
        git.sync_repo(ctx, repo["path"], upstream)
        helpers.create_story_branch(ctx, repo["path"], story_id, description)
    story = {
            "id": story_id,
            "description": description,
            "status": "OPEN",
            "pr_created": False
            }
    stories.append(story)
    helpers.save_stories(ctx, project_name, stories)


@click.group()
@click.pass_context
def main(ctx):
    """A simple CLI to aid in common, repetitive development tasks"""
    ctx.obj = {}
    ctx.obj['CONFIG'] = utils.load_file(constants.CONFIG_PATH)
    ctx.obj['PROJECTS'] = utils.load_file(constants.PROJECTS_PATH)


@main.command()
@click.option('--base-dir')
@click.option('--github-token')
@click.pass_context
def config(ctx, base_dir, github_token):
    """Edit the config file"""
    if base_dir is None or github_token is None:
        click.echo(config.get_help(ctx))
    _edit_config(ctx, base_dir, github_token)


@main.command()
@click.argument('project_name', metavar='project', required=False)
@click.pass_context
def sync(ctx, project_name):
    """Sync projects"""
    projects = ctx.obj["PROJECTS"]
    if project_name:
        project = projects[project_name]
        _sync_project(ctx, project)
    else:
        _sync_projects(ctx, projects)


@main.command()
@click.pass_context
def test(ctx):
    """Used for development debugging"""
    click.echo(ctx.obj)


@main.group()
@click.pass_context
def project(ctx):
    """Commands to aid in project management"""
    pass


@project.command(name="add")
@click.argument('name')
@click.argument('repos', nargs=-1)
@click.option('--upstream')
@click.pass_context
def project_add(ctx, name, repos, upstream):
    """Create a new project"""
    raw_repo_list = list(repos)
    repo_list = helpers.get_full_path_repo_list(ctx, raw_repo_list)
    repos = git.create_repos(repo_list)
    _create_project(ctx, name, repos, upstream)


@project.command(name="list")
@click.argument('name', required=False)
@click.pass_context
def project_list(ctx, name):
    """Display the contents of projects"""
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
    """Commands to aid in story management"""
    pass


@story.command(name="new")
@click.argument('story_id', metavar="id")
@click.argument('description_tuple', nargs=-1, metavar="description")
@click.option('--project')
@click.pass_context
def story_new(ctx, story_id, description_tuple, project):
    """Create a new story"""
    story_id = str(story_id)
    description_list = list(description_tuple)
    description = " ".join(description_list)
    if not project:
        cwd = os.getcwd()
        project = helpers.get_project(ctx, cwd)
    if helpers.can_create_story(ctx, project):
        _create_story(ctx, story_id, description, project)
    else:
        current_id, current_description = helpers.get_current_story(ctx,
                                                                    project)
        click.echo("Story {0} {1} is currently in progress for this project"
                   .format(current_id, current_description))


@story.command(name="push")
@click.option('--project')
@click.pass_context
def story_push(ctx, project):
    """Commit all changes, then make a pull request"""
    projects = ctx.obj["PROJECTS"]
    if not project:
        cwd = os.getcwd()
        project = helpers.get_project(ctx, cwd)
    story_id, description = helpers.get_current_story(ctx, project)
    changed_repos = git.get_changed_repos(ctx, project)
    for repo in changed_repos:
        git.sync_repo(ctx, repo["path"], projects[project]["upstream"])
        commit_message = git.get_commit_message(ctx, repo["path"])
        git.git_stage_all(repo["path"])
        git.git_commit(repo["path"], commit_message)
        current_branch = git.get_current_git_branch(repo["path"])
        git.git_push_branch(repo["path"], current_branch)
        for story in projects[project]["stories"]:
            if story["id"] == story_id and not story["pr_created"]:
                github.create_github_pull_request(ctx, repo)
                story["pr_created"] = True
        utils.save_file(constants.PROJECTS_PATH, projects)


@story.command(name="complete")
@click.argument('story_id', metavar="id", required=False)
@click.option('--project')
@click.pass_context
def story_complete(ctx, story_id, project):
    """Mark as complete and revert to master branch"""
    projects = ctx.obj["PROJECTS"]
    if not project:
        cwd = os.getcwd()
        project = helpers.get_project(ctx, cwd)
    _sync_project(ctx, projects[project])
    try:
        current_id, current_description = helpers.get_current_story(ctx,
                                                                    project)
        for story in projects[project]["stories"]:
            if story["id"] == story_id and not story["pr_created"]:
                story["status"] = "COMPLETED"
        utils.save_file(constants.PROJECTS_PATH, projects)
        git.tear_down_story(ctx, project)
    except errors.NoStoriesError:
        click.echo("No stories have been created for this project.")
        click.echo("Create one before trying again")
