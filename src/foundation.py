import os
import shutil
import argparse
import git
from datetime import date
from src.setup_logging import logger


def safe_copy(src, dest):
    if os.path.exists(dest):
        logger.info(f"adding a .resource to the file name so as not to overwrite existing file with same name")
        dest += '.resource'
    logger.info(f"copying {repo_resource.name} to {args.dest + '/' + repo_resource.name}")
    shutil.copyfile(src, dest)
    return True


def append_authors(dest_repo, repo_folder):
    logger.info("Appending author info if available from destination repo")
    with open(repo_folder+"/AUTHORS.md", "wt") as authors_handle:
        authors_handle.write('Author name|Author Email|Entry date\n')
        authors_handle.write('-----------|------------|----------\n')
        try:
            first_commit = dest_repo.head.commit.author
            author_name = first_commit.name
            author_email = first_commit.email
        except git.exc.GitCommandError:
            logger.info("couldn't access author info for destination repo because there is no commit history")
            return False
        today = date.today()
        formatted_date = today.strftime("%m/%d/%Y")
        try:
            authors_handle.write(f"{author_name}|{author_email}|{formatted_date}\n")
        except IOError:
            logger.info("Couldn't write to authors file")
            return False
    return True


def update_license(dest_repo, repo_folder):
    logger.info("Modifying license to reflect current repo owner")
    try:
        first_commit = dest_repo.head.commit.author
        author_name = first_commit.name
    except git.exc.GitCommandError:
        logger.info("couldn't derive author name from destination repo, using _____")
        author_name = '_______'
    today = date.today()
    formatted_date = today.strftime("%Y")
    logger.info(f"Identified {author_name} for License and {formatted_date} for year")
    lines = []
    logger.info("reading existing license file")
    with open(repo_folder + "/LICENSE", "rt") as license_handle:
        for line in license_handle:
            oldline = line
            line = line.replace("Erik Pohl", author_name)
            line = line.replace('2024', formatted_date)
            if line != oldline:
                logger.info("made a replacement")
            lines.append(line)
    logger.info("writing new license file")
    with open(repo_folder+"/LICENSE.", "wt") as license_handle:
        for line in lines:
            license_handle.write(line)
    return True


if __name__ == '__main__':
    logger.info("Attempting to build a foundation based on https://github.com/ErikPohl444/resources")
    logger.info("Getting destination folder from the command line arguments")
    parser = argparse.ArgumentParser(description="move foundation files")
    parser.add_argument('dest', type=str, help="the destination for the foundation")
    args = parser.parse_args()
    if not args:
        logger.info("No destination was specified, so not building a foundation")
        raise ValueError
    logger.info("Obtaining git repo info from the destination")
    try:
        dest_repo = git.Repo(os.curdir)
    except git.exc.GitCommandError:
        logger.info("No destination git repo")
    if not os.path.exists(args.dest):
        logger.info(f"{args.dest} does not exist, so we can't build the foundation")
        raise ValueError
    else:
        logger.info(f"{args.dest} exists, so we can build the foundation")
    ignore_files = ["foundation.py", "README.md", ".gitkeep"]
    logger.info(f"defined ignore file list [{ignore_files}] for files not to copy to destination")
    for repo_resource in dest_repo.tree().traverse():
        resource_name = repo_resource.name
        if os.path.exists(repo_resource.name):
            dest_file_name = args.dest + '/' + resource_name
            logger.info(f"naming {dest_file_name} as the destination file and path for {resource_name}")
            if os.path.isdir(resource_name):
                logger.info(f"found a folder in source resources {resource_name}, copying as a folder {dest_file_name}")
                if not os.path.exists(dest_file_name):
                    shutil.copytree(resource_name, dest_file_name)
                else:
                    logger.info(f"Not copying folder {dest_file_name} because it already exists")
            elif resource_name == 'readme_template.md':
                logger.info(f"converting readme template to readme: {resource_name} to README.md")
                safe_copy('./readme_template.md', args.dest + '/README.md')
            elif resource_name in ignore_files:
                logger.info(f"ignoring {resource_name} from copy to destination")
            else:
                safe_copy(resource_name, dest_file_name)
                if resource_name == "AUTHORS.md":
                    append_authors(dest_repo, args.dest)
                if resource_name == "LICENSE":
                    update_license(dest_repo, args.dest)
