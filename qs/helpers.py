import click

from qs.utils import *
from qs.git import *


def get_full_path_dir_list(ctx, dirs, warn=False):
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


def get_full_path_repo_list(ctx, repo_list):
    full_path_repo_list = []
    dir_list = get_full_path_dir_list(ctx, repo_list, warn=True)
    full_path_repo_list = get_git_repos(dir_list, warn=True)
    if os.name == "nt":
        windows_full_path_repo_list = []
        for repo in full_path_repo_list:
            windows_repo = repo.replace("\\\\", "\\")
            windows_full_path_repo_list.append(windows_repo)
        return windows_full_path_repo_list
    return full_path_repo_list


def get_project(ctx, path):
    projects = ctx.obj["PROJECTS"]
    possible_projects = []
    for possible_project in projects:
        if path in projects[possible_project]["repos"][0]["path"]:
            possible_projects.append(possible_project)
    if len(possible_projects) == 1:
        project = possible_projects[0]
    elif len(possible_projects) == 0:
        # TODO: Make this raise an exception
        click.echo("The current directory is not assigned to a project.")
        click.echo("Create one before starting a story")
        return
    else:
        project = get_desired_project(possible_projects)
    return project


def get_desired_project(possible_projects):
    click.echo("Multiple projects found. Please select one: ")
    for i, project in enumerate(possible_projects):
        click.echo("{0}.) {1}".format(i + 1, project))
    user_response = click.prompt("Enter choice", default=1)
    return possible_projects[user_response-1]


def create_story_branch(ctx, repo, story_id, description):
    branch_name = story_id + "_" + description.replace(' ', '_')
    current_branch = get_current_git_branch(repo)
    if current_branch == "master":
        create_git_branch(ctx, repo, branch_name)
    else:
        repo_name = get_repo_name(ctx, repo)
        click.echo("{} is currently on branch {}"
                   .format(repo_name, current_branch))
        response = click.confirm("Create new branch anyway?")
        if response:
            create_git_branch(ctx, repo, branch_name)
        else:
            click.echo("Skipping repositry {}".format(repo_name))


def can_create_story(ctx, project):
    projects = ctx.obj["PROJECTS"]
    stories = projects[project]["stories"]
    for story in stories:
        if story["status"] == "OPEN":
            return False
    return True


def save_stories(ctx, project, stories):
    projects = ctx.obj["PROJECTS"]
    projects[project]["stories"] = stories
    save_file(PROJECTS_PATH, projects)


def get_current_story(ctx, project):
    project = ctx.obj["PROJECTS"][project]
    for story in project["stories"]:
        if story["status"] == "OPEN":
            return story["id"], story["description"]
