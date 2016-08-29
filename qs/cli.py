import click
import os
import json
import subprocess

APP_DIR = click.get_app_dir("qs") + "/"
CONFIG_PATH = APP_DIR + "config.json"
PROJECTS_PATH = APP_DIR + "projects.json"


class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def _load_file(file):
    if _file_exists(file):
        with open(file, 'r') as f:
            file_contents = json.load(f)
    else:
        file_contents = _create_file(file)
    return file_contents


def _file_exists(file):
    return os.path.isfile(file)


def _save_file(file, contents):
    with open(file, 'w') as f:
        json.dump(contents, f)


def _create_file(file):
    if not os.path.exists(APP_DIR):
        os.makedirs(APP_DIR)
    if file[len(APP_DIR):] == "config.json":
        file_contents = {'BASE_DIR': os.path.expanduser("~/Projects/")}
    elif file[len(APP_DIR):] == "projects.json":
        file_contents = {}
    _save_file(file, file_contents)
    return file_contents


def _get_sub_dirs(base_dir):
    return list(filter(lambda x: os.path.isdir(os.path.join(base_dir, x)), os.listdir(base_dir)))


def _get_git_repos(dirs, warn=False):
    repos = []
    for directory in dirs:
        if os.path.isdir(directory + "/.git/"):
            repos.append(directory)
        elif warn:
            click.echo("{} is not a git repositry".format(directory))
    return repos


def _parse_raw_git_branch(raw_branch):
    branch_text = raw_branch.decode("utf-8")
    branch = branch_text[10:-1]
    return branch


def _sync_repo(ctx, repo):
    base_dir = ctx.obj['CONFIG']['BASE_DIR']
    repo_name = repo[len(base_dir):]
    click.echo("Synching Repositry: {}".format(repo_name))
    with cd(repo):
        os.system("git pull upstream master")
    click.echo("-"*80)  # Fill terminal


def _sync_repos(ctx, repos):
    base_dir = ctx.obj['CONFIG']['BASE_DIR']
    for repo in repos:
        with cd(repo):
            raw_branch = subprocess.check_output("git status | head -1",
                                                 shell=True)
            branch = _parse_raw_git_branch(raw_branch)
            if branch == "master":
                _sync_repo(ctx, repo)


def _create_project(ctx, name, repo_list):
    projects = ctx.obj['PROJECTS']
    projects[name] = {"repos": repo_list, "stories": []}
    _save_file(PROJECTS_PATH, projects)


def _edit_config(ctx, base_dir):
    config = ctx.obj['CONFIG']
    if base_dir:
        config["BASE_DIR"] = base_dir
    _save_file(CONFIG_PATH, config)


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
    repo_name = repo[len(base_dir):]
    return repo_name


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
    base_dir = ctx.obj["CONFIG"]["BASE_DIR"]
    repo_name = repo[len(base_dir):]
    click.echo("Creating branch {0} for {1}".format(branch_name, repo_name))
    with cd(repo):
        os.system("git checkout -b {}".format(branch_name))


def _save_stories(ctx, project, stories):
    projects = ctx.obj["PROJECTS"]
    projects[project]["stories"] = stories
    _save_file(PROJECTS_PATH, projects)


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


@click.group()
@click.pass_context
def main(ctx):
    """A simple CLI to aid in common, repetitive development tasks"""
    ctx.obj = {}
    ctx.obj['CONFIG'] = _load_file(CONFIG_PATH)
    ctx.obj['PROJECTS'] = _load_file(PROJECTS_PATH)


@main.command()
@click.option('--base-dir')
@click.pass_context
def config(ctx, base_dir):
    _edit_config(ctx, base_dir)


@main.command()
@click.pass_context
def sync(ctx):
    """Syncs all projects in the base directory"""
    base_dir = ctx.obj['CONFIG']['BASE_DIR']
    dirs = _get_sub_dirs(base_dir)
    full_path_dirs = _get_full_path_dir_list(ctx, dirs)
    repos = _get_git_repos(full_path_dirs)
    _sync_repos(ctx, repos)


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
@click.pass_context
def project_add(ctx, name, repos):
    raw_repo_list = list(repos)
    repo_list = _get_full_path_repo_list(ctx, raw_repo_list)
    _create_project(ctx, name, repo_list)


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
