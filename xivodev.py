#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

"""
usage: $0 options

This script git pulls all repos in directory with a few bells and whistles.

OPTIONS:
   -c      Check Code Coverage
   -f      Git fetch repos
   -h      Show this message
   -l      List repositories and their current branch
   -s      Rsync repositories on given xivo ip|hostname
   -p      git pull repositories
   -r      Concerned Repositories. By default, options affect all managed repositories. specifiying repos will limit the scope on wich options operate.
   -t      Update ctags
   -vl     List Virtualbox VMs
   -v1     Start given Virtualbox VMs
   -v0     Stop given Virtualbox VMs
   -v      Verbose
   -d      Dry run mode : echoes commands without executing
"""

import argparse
import logging
import shlex
import subprocess
import sh


SOURCE_DIRECTORY = "/home/jp/src/xivo"

REPOS = {
    'xivo-amid': ('', 'xivo_ami', '/usr/lib/python2.7/dist-packages/'),
    'xivo-agent': ('xivo-agent', 'xivo_agent', '/usr/lib/python2.7/dist-packages/'),
    'xivo-agid': ('xivo-agid', 'xivo_agid', '/usr/lib/python2.7/dist-packages/'),
    'xivo-bus': ('xivo-bus', 'xivo_bus', '/usr/lib/python2.7/dist-packages/'),
    'xivo-call-logs': ('xivo-call-logs', 'xivo_call_logs', '/usr/lib/python2.7/dist-packages/'),
    'xivo-config': ('xivo-config/dialplan/asterisk', None, '/usr/share/xivo-config/dialplan/'),
    'xivo-confgen': ('xivo-confgen', 'xivo_confgen', '/usr/lib/python2.7/dist-packages/'),
    'xivo-ctid': ('xivo-ctid', 'xivo_cti', '/usr/lib/python2.7/dist-packages/'),
    'xivo-dao': ('xivo-dao', 'xivo_dao', '/usr/lib/python2.7/dist-packages/'),
    'xivo-dird': ('xivo-dird', 'xivo_dird', '/usr/lib/python2.7/dist-packages/'),
    'xivo-lib-python': ('xivo-lib-python', 'xivo', '/usr/lib/python2.7/dist-packages/'),
    'xivo-provisioning': ('xivo-provisioning/src', 'provd', '/usr/lib/python2.7/dist-packages/'),
    'xivo-restapi': ('xivo-restapi', 'xivo_restapi', '/usr/lib/python2.7/dist-packages/'),
    'xivo-stat': ('xivo-stat', 'xivo_stat', '/usr/lib/python2.7/dist-packages/'),
    'xivo-sysconfd': ('xivo-sysconfd', 'xivo_sysconf', '/usr/lib/python2.7/dist-packages/'),
    'xivo-web-interface': ('xivo-web-interface/src', None, '/usr/share/xivo-web-interface'),
    'xivo-upgrade': ('xivo-upgrade', None, None),
    'xivo-doc': ('source', None, None),
    'xivo': ('', None, None),
    'xivo-acceptance': ('', None, None),
    'create_archive_file': ('', None, None),
    'asterisk11': ('', None, None),
    'debian-installer': ('', None, None),
    'pylinphonelib': ('', None, None),
    'xivo-acceptance': ('', None, None),
    'xivo-backup': ('', None, None),
    'xivo-build-tools': ('', None, None),
    'xivo-client-qt': ('', None, None),
    'xivo-experimental': ('', None, None),
    'xivo-fetchfw': ('', None, None),
    'xivo-install-cd': ('', None, None),
    'xivo-lib-js': ('', None, None),
    'xivo-libsccp': ('', None, None),
    'xivo-loadtest': ('', None, None),
    'xivo-manage-db': ('', None, None),
    'xivo-monitoring': ('', None, None),
    'xivo-presentations': ('', None, None),
    'xivo-provd-plugins': ('', None, None),
    'xivo-sounds': ('', None, None),
    'xivo-tools': ('', None, None),
    'xivo-utils': ('', None, None),
    'xivo-ws': ('', None, None),
}

logger = logging.getLogger(__name__)
xivo_src = '/home/jp/src/xivo'


class bcolors:
    """
    old colors :
        #print "\e[00;31mReady\e[00m, \e[1;33mSet\e[00m, \e[0;32mC0DE!\e[00m"
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def parse_args():
    parser = argparse.ArgumentParser('XiVO dev toolkit')
    parser.add_argument("-c", "--coverage", help="check code coverage",
                        action="store_true")
    parser.add_argument("-d", "--dry", help="dry run - displays but do not execute commands (when applicable)",
                        action="store_true")
    parser.add_argument("-f", "--fetch", help="git fetch repositories",
                        action="store_true")
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")
    parser.add_argument("-t", "--tags", help="update CTAGS",
                        action="store_true")
    parser.add_argument("-p", "--pull", help="git pull repositories",
                        action="store_true")
    parser.add_argument("-l", "--list", help="list all repositories and their current branch",
                        action="store_true")
    parser.add_argument("-s", "--sync", help='sync repos on given IP or hostname')
    parser.add_argument("-vl", "--vmlist", help='list virtualbox vms',
                        action="store_true")
    parser.add_argument("-v1", "--vmstart", help='start virtualbox vm with given name')
    parser.add_argument("-v0", "--vmstop", help=' stop virtualbox vm with given name')
    parser.add_argument("-vs", "--vmsnapshot", help=' snapshot virtualbox vm with given name',
                        nargs=2, metavar=('name', 'description'))
    parser.add_argument("-r", "--repos", help='list of repos on which to operate (default : all handled repos)',
                        nargs='*', type=is_handled_repo, default=[name for name in REPOS.iterkeys()])

    return parser.parse_args()


def is_handled_repo(repo_name):
    if repo_name not in REPOS.iterkeys():
        msg = '%s is not a supported repository name' % repo_name
        raise argparse.ArgumentTypeError(msg)
    return repo_name


def init_logging(args):
    level = logging.DEBUG if args.verbose else logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s (%(levelname)s): %(message)s'))
    root_logger.addHandler(handler)


def print_mantra():
    print ("\n" + bcolors.FAIL + "Ready, " + bcolors.ENDC + bcolors.WARNING + "Set, " + bcolors.ENDC + bcolors.OKGREEN + "C0D3!" + bcolors.ENDC)


def list_repositories_with_branch(requested_repositories):
    for name in requested_repositories:
        format_non_master = bcolors.FAIL + "{branch}" + bcolors.ENDC
        branch = _get_current_branch(name)
        if branch != 'master':
            branch = format_non_master.format(branch=branch)
        print("%s : %s" % (name, branch))


def fetch_repositories(requested_repositories):
    for repo_name in requested_repositories:
        cmd = 'git fetch -p'
        ret = _exec_git_command(cmd, repo_name)
        if ret:
            print("%s" % ret)


def rsync_repositories(remote_host, requested_repositories):
    logger.debug('host: %s | requested repos : %s', remote_host, requested_repositories)
    for repo_name in requested_repositories:
        _rsync_repository(remote_host, repo_name)


def update_ctags():
    ctag_file = "/home/jp/.mytags"
    print(sh.ctags('-R', '--exclude="*.js"', '-f', ctag_file, SOURCE_DIRECTORY))
    logger.info('Updated CTAGS %s', ctag_file)


def pull_repositories(repositories):
    for repo_name in repositories:
        logger.info('%s : %s', repo_name, _pull_repository_if_on_master(repo_name))


#
# code coverage
#
def check_coverage(repositories):
    for repo_name in repositories:
        path = _get_local_path(repo_name)
        pymodule = _get_pymodule(repo_name)
        print(sh.nosetests2("--with-coverage", "--cover-package", pymodule, path, _err_to_out=True, _cwd='/tmp'))


# vm management
# see https://nfolamp.wordpress.com/2010/06/10/running-virtualbox-guest-vms-in-headless-mode/
#
def list_vms():
    msg_all = bcolors.FAIL + "All VMs" + bcolors.ENDC + '\n'
    result_all = sh.VBoxManage('list', 'vms')
    msg_running = "\n" + bcolors.OKGREEN + "Running VMs" + bcolors.ENDC + '\n'
    result_running = sh.VBoxManage('list', 'runningvms')
    print('%s %s %s %s' % (msg_all, result_all, msg_running, result_running))


def start_vm(name):
    cmd = 'sh -c "nohup VBoxHeadless -s {vm_name} -v on &"'.format(vm_name=name)
    subprocess.call(shlex.split(cmd))
    logger.info("started vm %s", name)


def kill_vm(name):
    cmd = 'VBoxManage contolvm {vm_name} poweroff'.format(vm_name=name)
    subprocess.call(shlex.split(cmd))
    logger.info("stopped vm %s", name)


def snapshot_vm(name, description):
    cmd = 'VBoxManage snapshot {vm_name} take {description}'.format(vm_name=name, description=description)
    subprocess.call(shlex.split(cmd))
    logger.info("snapshot vm %s with description %s", name, description)


def _rsync_repository(remote_host, repo_name):
    if _repo_is_syncable(repo_name):
        base_command = "rsync -v -rtlp --exclude '*.pyc' --exclude '*.swp' --delete"
        remote_uri = _remote_uri(remote_host, repo_name)
        cmd = "%s %s %s" % (base_command, _get_local_path(repo_name), remote_uri)
        logger.debug('about to execute rsync command : %s', cmd)
        if not args.dry:
            subprocess.call(shlex.split(cmd))


def _repo_is_syncable(name):
    return REPOS[name][2]


def _get_local_path(name):
    path = _repo_path(name)
    if REPOS[name][0]:
        path = "%s/%s" % (path, REPOS[name][0])
    if REPOS[name][1]:
        path = "%s/%s" % (path, REPOS[name][1])
    return path


def _get_pymodule(name):
    return REPOS[name][1]


def _repo_path(name):
    return '%s/%s' % (SOURCE_DIRECTORY, name)


def _remote_uri(remote_host, repo_name):
    remote_path = REPOS[repo_name][2]
    if remote_path:
        return '%s:%s' % (remote_host, remote_path)
    else:
        return None


def _pull_repository_if_on_master(repo_name):
    cmd = 'git pull'
    current_branch = _get_current_branch(repo_name)
    if(current_branch == 'master'):
        return _exec_git_command(cmd, repo_name)
    else:
        return 'Not on branch master (%s)' % current_branch


def _get_current_branch(repo):
    cmd = 'git rev-parse --abbrev-ref HEAD'
    return _exec_git_command(cmd, repo).strip()


def _exec_git_command(cmd, repo):
    logger.debug('%s on %s', cmd, repo)
    cmd = shlex.split(cmd)
    repo_dir = _repo_path(repo)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=repo_dir)
    result = process.communicate()
    return result[0].strip()


if __name__ == "__main__":
    args = parse_args()
    init_logging(args)
    print("")  # enforced newline

    if args.coverage:
        check_coverage(args.repos)

    if args.list:
        list_repositories_with_branch(args.repos)

    if args.fetch:
        fetch_repositories(args.repos)

    if args.pull:
        pull_repositories(args.repos)

    if args.tags:
        update_ctags()

    if args.sync:
        rsync_repositories(args.sync, args.repos)

    if args.vmlist:
        list_vms()

    if args.vmstop:
        kill_vm(args.vmstop)

    if args.vmsnapshot:
        name, description = args.vmsnapshot
        snapshot_vm(name, description)

    if args.vmstart:
        start_vm(args.vmstart)

    print_mantra()
