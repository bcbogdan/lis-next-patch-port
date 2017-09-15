import subprocess
import logging
import argparse
import os
from constants import LINUX_REPO_URL, LINUX_NEXT_REMOTE
logger=logging.getLogger(__name__)

def change_dir(func):
    def wrapper(*args, **kwargs):
        cur_dir = os.getcwd()
        result = func(*args, **kwargs)
        os.chdir(cur_dir)
        return result
    return wrapper

def get_arg_parser():
    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers(help='CLI Commands')
    
    create_patch_parser = sub_parsers.add_parser('create-patches', help='Create patches in folder')
    create_patch_parser.add_argument(
        '-d', '--date',
        help='Date since last commit. Default - a day ago',
        default="1 day ago")
    create_patch_parser.add_argument(
        '-a', '--author',
        help='Specific commit author',
        default=None
    )
    create_patch_parser.add_argument(
        '-l', '--linux-repo',
        help='Linux repo path',
        default='None'
    )
    create_patch_parser.add_argument(
        '-p', '--patches-folder',
        help='Folder where the patch files will be created',
        default='./patches'
    )

    test_patches_parser = sub_parsers.add_parser('test-patches', help='Build and test the new patches with lis next')
    test_patches_parser.add_argument(
        'patches_folder',
        help='Patches folder path',
        default='.\patches'
    )
    return parser

def clone_repo(repo_url, repo_path):
    return run_command([
        'git', 'clone', repo_url,
        repo_path
    ])

def add_remote(remote_name, remote_url):
    return run_command([
        'git', 'remote', 'add',
        remote_name, remote_url
    ])

@change_dir
def manage_linux_repo(repo_path, create=False):
    if create:
        clone_repo(LINUX_REPO_URL, repo_path)
        os.chdir(repo_path)
        add_remote('linux-next', LINUX_NEXT_REMOTE)
        run_command(['git', 'fetch', 'linux-next']) 
        run_command(['git', 'fetch', '--tags', 'linux-next'])
    else:
        os.chdir(repo_path)
        run_command(['git', 'checkout', 'master'])
        run_command(['git', 'remote', 'update'])

def run_command(command_arguments):
    ps_command = subprocess.Popen(
    command_arguments,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
    )

    stdout_data, stderr_data = ps_command.communicate()

    logger.debug('Command output %s', stdout_data)
    if ps_command.returncode != 0:
        raise RuntimeError(
            "Command failed, status code %s stdout %r stderr %r" % (
                ps_command.returncode, stdout_data, stderr_data
            )
        )
    else:
        return stdout_data
