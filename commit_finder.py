import subprocess
import logging
import os
import argparse
import sys

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)
from shutil import rmtree
GIT_CMD = 'git'
linux_repo_path = r'C:\Users\bogda\AppData\Local\lxss\root\linux'


current_path = os.getcwd()
os.chdir(linux_repo_path)


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
        default=None
    )
    create_patch_parser.add_argument(
        '-g', '--git-bin',
        help='Path to git binary',
        default='git'
    )
    create_patch_parser.add_argument(
        '-p', '--patches-folder',
        help='Folder where the patch files will be created',
        default='./patches'
    )

    test_patches_parser = sub_parsers.add_parser('test-patches', help='Build and test the new patches with lis next')
    test_patches_parser.add_argument(
        '-v', '--vm-name',
        help='Test VM name'
        )
    test_patches_parser.add_argument(
        '-s', '--server-name',
        help='Hyper-V Server name',
        default='localhost'
    )
    test_patches_parser.add_argument(
        '-k', '--ssh-key',
        help='SSH Key Path',
        default='.\ssh\id_rsa.ppk'
    )
    test_patches_parser.add_argument(
        '-i', '--ipv4',
        help='VM ip'
    )
    return parser

    
files_map = {
    "drivers/hv": "hv/",
    "tools/hv": "hv/tools/",
    "drivers/net/hyperv": "hv/"
}

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

def normalize_path(patch_path):
    normalize_base = ["sed", '-i']
    parse_cmds = [
        "'s/--- a\/drivers\/hv/--- a/g'", "'s/+++ b\/drivers\/hv/+++ b/g'",
        "'s/--- a\/drivers\/scsi/--- a/g'", "'s/+++ b\/drivers\/scsi/+++ b/g'",
        "'s/--- a\/tools\/hv\//--- a\/tools\//g'", "'s/+++ b\/tools\/hv\//+++ b\/tools\//g'",
        "'s/--- a\/drivers\/net\/hyperv/ --- a/g'", "'s/+++ b\/drivers\/net\/hyperv/ +++ b/g'",
        "'s/--- a\/arch\/x86\/include\/asm/ --- a\/arch\/x86\/include\/lis\/asm/g'",
        "'s/+++ b\/arch\/x86\/include\/asm/ +++ b\/arch\/x86\/include\/lis\/asm/g'",
        "'s/--- a\/arch\/x86\/include\/uapi\/asm/ --- a\/arch\/x86\/include\/uapi\/lis\/asm/g'",
        "'s/+++ b\/arch\/x86\/include\/uapi\/asm/ +++ b\/arch\/x86\/include\/uapi\/lis\/asm/g'",
        "'s/--- a\/drivers\/pci\/host/--- a/g'", "'s/+++ b\/drivers\/pci\/host/+++ b/g'"
        ]
    
    for cmd in parse_cmds:
        final_cmd = normalize_base + cmd + [patch_path]
        run_command(final_cmd)

def apply_patch(patch_file, dry_run=False):
    if dry_run:
        dry_run = '--dry-run'
    else:
        dry_run = ''

    cmd = ['patch', dry_run, '--ignore-whitespace',
            '-p1', '-F1', '-f', '<', patch_file
    ]

    return run_command(cmd)

def build(clean=False):
    base_build_cmd = ['make', '-C']
    drivers = '/lib/modules/$(uname -r)/build M=`pwd`'
    daemons = './tools'
    # First run the clean commands
    run_command(base_build_cmd, [drivers, 'clean'])
	run_command(base_build_cmd, [daemons, 'clean'])
    
    if not clean:
        run_command(base_build_cmd + [drivers])
        run_command(base_build_cmd + [daemons])
    
def test_patch(patch_path, repo_path):
    os.chdir(repo_path)

    logger.info('Normalizing the paths in the patch')
    normalize_path(patch_path)
    
    logger.info("Applying patch in dry run")
    self.apply_patch(patch_path, dry_run=True)
    logger.info("Applying patch")
    self.apply_patch(patch_path)

    logger.info("Building LIS drivers and daemons")
    self.build()

    logger.info("Running repo cleanup")
    self.build(clean=True)

    #logger.info("Create commit message")
    #self.commit_changes(patch_file)

def get_commit_ids(self, path, author=None, date=None):
    git_cmd = ['git', 'log']
    if author: git_cmd.extend(['--author', author])
    if date: git_cmd.extend(['--since', date])

    git_cmd.append('--pretty=format:%H')
    git_cmd.extend(['--', path])

    return run_command(git_cmd).strip().split()

def create_patch(self, commit_id, destination):
    command = [
        'git', 'format-patch', '-1',
        commit_id, '-o', destination
        ]

    return run_command(command).strip()

def clone_repo(self, repo_url, repo_path):
    return run_command([
        'git', 'clone', repo_url,
        repo_path
    ])
    

def test_patches(args):
    vm_manager = VMManager(name=args.vm_name, )
    for patch_file in os.list_dir(args.patches_folder):
        vm_manager.create_dir('/root/patches')
        vm_manager.copy_file(patch_file, '/root/patches')
        vm_manager.clone_repo(lis_next_repo, dest='/root/lis-next')
        vm_manager.test_patch('/root/patches/something', lis_next_repo)
        vm_manager.copy_lis_next()

def create_patches(args):
    patches_folder = args.patches_folder
    
    linux_repo = GitManager(args.linux_repo, git_path=args.git_bin)
    os.chdir(linux_repo_path)
    commit_list = []
    for linux_path, lis_next_path in files_map.items():
        commits = linux_repo.get_commit_ids(linux_path, date=args.date, author=args.author)
        commit_list.extend(commits)
        
    commit_list = set(commit_list)

    logger.info('Creating patches for the following commits: {}'.format(', '.join(commit_list)))
    if os.path.exists(patches_folder): rmtree(patches_folder)
    os.mkdir(patches_folder)
    patch_list = []
    for commit_id in commit_list:
        patch_list.append(linux_repo.create_patch(commit_id, patches_folder))

    logger.info('Created the following patches: {}'.format(', '.join(patch_list)))

if __name__ == '__main__':
    parser = get_arg_parser()
    args = parser.parse_args(sys.argv[1:])
    command = sys.argv[1]
    if command == 'create-patches':
        create_patches(args)
    elif command == 'test-patches':
        test_patches(args)
    else:
        pass