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
    
class VMManager(object):
    normalize_cmds = [
        "sed -i 's/--- a\/drivers\/hv/--- a/g' {}",
	    "sed -i 's/+++ b\/drivers\/hv/+++ b/g' {}"
	    "sed -i 's/--- a\/drivers\/scsi/--- a/g' {}"
	    "sed -i 's/+++ b\/drivers\/scsi/+++ b/g' {}"
	    "sed -i 's/--- a\/tools\/hv\//--- a\/tools\//g' {}"
	    "sed -i 's/+++ b\/tools\/hv\//+++ b\/tools\//g' {}"
	    "sed -i 's/--- a\/drivers\/net\/hyperv/ --- a/g' {}"
	    "sed -i 's/+++ b\/drivers\/net\/hyperv/ +++ b/g' {}"
	    "sed -i 's/--- a\/arch\/x86\/include\/asm/ --- a\/arch\/x86\/include\/lis\/asm/g' {}"
	    "sed -i 's/+++ b\/arch\/x86\/include\/asm/ +++ b\/arch\/x86\/include\/lis\/asm/g' {}"
	    "sed -i 's/--- a\/arch\/x86\/include\/uapi\/asm/ --- a\/arch\/x86\/include\/uapi\/lis\/asm/g' {}"
	    "sed -i 's/+++ b\/arch\/x86\/include\/uapi\/asm/ +++ b\/arch\/x86\/include\/uapi\/lis\/asm/g' {}"
	    "sed -i 's/--- a\/drivers\/pci\/host/--- a/g' {}"
    	"sed -i 's/+++ b\/drivers\/pci\/host/+++ b/g' {}"
    ]


    def __init__(self, vm_name, server, vm_user, ssh, plink):
        self.name = vm_name
        self.server = server
        self.ssh = ssh
        self.plink = plink
        self.user = vm_user
    
    @run_remote_command
    def create_folder(folder_path):
        bash_cmd = '[ -d "{}" ] then rm -rf {} && mkdir {}; else mkdir {}; fi'.format(
            folder_path, folder_path, folder_path
        )
        return bash_cmd

    def run_remote_command(self, method):
        def wrapper(*args):
            cmd = method(*args)
            win_cmd = [ self.plink, '-i', self.ssh, 
                '{}@{}'.format(self.user, self.vm_ip),
                cmd
            ]
            return run_command(win_cmd)

        return wrapper

    @run_remote_command
    def copy_file(source_path, destination_path):
        pass

    @run_remote_command  
    def clone_repo(repo_url, dest='/root/'):
        cmd = 'git clone {} {}'.format(repo_url, dest)
        self.run_remote_cmd(cmd)
    
    
    def get_kvp_dict(self, kvp_fields=None):
        cmd_output = self.invoke_ps_command('kvp')
        if not kvp_fields:
            return VirtualMachine.parse_kvp_output(cmd_output)

        kvp_dict = VirtualMachine.parse_kvp_output(cmd_output)
        kvp_values = dict()
        for field in kvp_fields:
            try:
                kvp_values[field] = kvp_dict[field]
            except KeyError:
                logger.warning('Unable to find kvp value for %s', field)

        return kvp_values

    def get_kvp_cmd():
        pass

    def test_patch(patch_path, repo_path):
        self.chdir(repo_path)

        logger.info('Normalizing the paths in the patch')
        for cmd in normalize_cmds:
            self.run_remote_cmd(cmd.format(patch_path))
        
        logger.info("Applying patch in dry run")
        self.apply_patch(patch_path, dry_run=True)
        logger.info("Applying patch")
        self.apply_patch(patch_path)

        logger.info("Building LIS drivers")
        self.build_drivers()

        logger.info("Building LIS daemons")
        self.build_daemons()

        logger.info("Running repo cleanup")
        self.cleanup()

        logger.info("Create commit message")
        self.commit_changes(patch_file)


    def commit_changes():
        commit_description = ''
        commit_id = ''

        commit_cmds = [
            'git add -u .',
            'git add ./\*.c',
            'git add ./\*.h',
            'git commit -m "RH:{} <upstream:{}>"'.format(commit_description, commit_id)
        ]

        for cmd in commit_cmds:
            self.run_remote_cmd(cmd)
	
    @run_remote_command
    def build_drivers():
        cmd = 'make -C /lib/modules/$(uname -r)/build M=`pwd` clean'
        self.run_remote_cmd(cmd)
        cmd = 'make -C /lib/modules/$(uname -r)/build M=`pwd` modules'
        self.run_remote_cmd(cmd)
    
    @run_remote_command
    def build_daemons():
        cmd = 'make -C ./tools clean'
	    self.run_remote_cmd(cmd)
        cmd = 'make -C ./tools'
        self.run_remote_cmd(cmd)
    
    @run_remote_command
    def cleanup():
	    cmd = "make -C ./tools clean"
	    self.run_remote_cmd(cmd)
	    cmd = "make -C /lib/modules/$(uname -r)/build M=`pwd` clean"
	    self.run_remote_cmd(cmd)

    @run_remote_command
    def apply_patch(patch_file, dry_run=False):
        if dry_run:
            dry_run = '--dry-run'
        else:
            dry_run = ''

        cmd = 'patch {} --ignore-whitespace -p1 -F1 -f < {}'.format(
            dry_run, patch_file
        )

        return cmd


    def run_remote_cmd(cmd):
        win_cmd = [
            self.plink, '-i', self.ssh,
            '{}@{}'.format(self.user, self.vm_ip),
            cmd
        ]

        return run_command(win_cmd)

class GitManager(object):
    def __init__(self, repo_path, git_path='git', repo_url=None):
        self.repo_path = repo_path
        self.git_path = git_path
        if repo_url: self.run_command(self.get_clone_command(repo_url))
    
    def get_commit_ids(self, path, author=None, date=None):
        git_cmd = [self.git_path, 'log']
        if author: git_cmd.extend(['--author', author])
        if date: git_cmd.extend(['--since', date])

        git_cmd.append('--pretty=format:%H')
        git_cmd.extend(['--', path])

        return self.run_command(git_cmd).strip().split()

    def create_patch(self, commit_id, destination):
        command = [
            self.git_path, 'format-patch', '-1',
            commit_id, '-o', destination
            ]

        return self.run_command(command).strip()
    
    def get_clone_command(self, repo_url):
        return [
            self.git_path, 'clone', repo_url,
            self.repo_path
        ]
    
    @staticmethod
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
    



    dry = ''
    if dry_run: dry = '--dry-run'

    return 'patch {} --ignore-whitespace -p1 -F1 -f < {}'.format(
                dry, patch_file_path
            )


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