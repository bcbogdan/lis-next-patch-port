import subprocess
import logging

logger=logging.getLogger(__name__)

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
