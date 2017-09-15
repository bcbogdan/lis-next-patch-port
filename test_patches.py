import logging
import os
from shutil import rmtree
from utils import run_command, git_clone
from constants import LIS_NEXT_REPO_URL

logger=logging.getLogger(__name__)

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
    
def test_patch(patch_path):
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

def test_patches(patches_folder):
    root_path = os.getcwd()
    for patch_file in os.list_dir(patches_folder):
        os.chdir(root_path)
        commit_id = patch_file.split('/')[-1].split('.')[0]
        repo_path = './lis-next-{}'.format(commit_id)
        clone_repo(LIS_NEXT_REPO_URL, repo_path)
        os.chdir(os.path.join(repo_path, '/hv-rhel7.x/hv'))
        test_patch(patch_file)
