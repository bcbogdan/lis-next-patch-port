import os
import logging
from shutil import rmtree
from utils import change_dir, run_command
from constants import FILES_MAP
logger=logging.getLogger(__name__)

def get_commit_list(linux_repo_path, date='a day ago', author=None):
    commit_list = []
    for linux_path, lis_next_path in FILES_MAP.items():
        commits = get_commit_ids(linux_path, date=date, author=author)
        commit_list.extend(commits)
        
    return set(commit_list)

def create_patch_files(commit_list, patches_folder='./patches'):
    if os.path.exists(patches_folder): rmtree(patches_folder)
    os.mkdir(patches_folder)
    patch_list = []
    for commit_id in commit_list:
        patch_list.append(create_patch(commit_id, patches_folder))
    return patch_list

def get_commit_ids(path, author=None, date=None):
    git_cmd = ['git', 'log']
    if author: git_cmd.extend(['--author', author])
    if date: git_cmd.extend(['--since', date])

    git_cmd.append('--pretty=format:%H')
    git_cmd.extend(['--', path])

    return run_command(git_cmd).strip().split()

def create_patch(commit_id, destination):
    command = [
        'git', 'format-patch', '-1',
        commit_id, '-o', destination
        ]

    return run_command(command).strip()

