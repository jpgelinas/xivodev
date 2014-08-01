#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

"""
usage: $0 options

This script git pulls all repos in directory with a few bells and whistles.

OPTIONS:
   -b      Batch execute git command on repos
   -c      Check Code Coverage
   -f      Git fetch repos
   -g      Grep branches containing given query in branch name
   -h      Show this message
   -l      List repositories and their current branch
   -ll     List REPOS array
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
import sh
from xivo_dev.repositories import REPOS, SOURCE_DIRECTORY


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
    parser.add_argument("-bc", "--buildclient", help="rebuild XiVO client from sources",
                        action="store_true")
    parser.add_argument("-bd", "--builddoc", help="rebuild XiVO doc from sources",
                        action="store_true")
    parser.add_argument("-c", "--coverage", help="check code coverage",
                        action="store_true")
    parser.add_argument("-d", "--dry", help="dry run - displays but do not execute commands (when applicable)",
                        action="store_true")
    parser.add_argument("-D", "--deletemerged", help="Delete branch already merged into masters",
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
    parser.add_argument("-ll", "--longlist", help="list all repositories with additionnal infos",
                        action="store_true")
    parser.add_argument("-s", "--sync", help='sync repos on given IP or hostname')
    parser.add_argument("-b", "--batch", help='batch execute git command on given repos')
    parser.add_argument("-g", "--grepbranches", help='find branches names for given query')
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


def list_repositories_with_details(requested_repositories):
    for name in requested_repositories:
        path = REPOS[name][2]
        print("%s : %s" % (name, path))


def grep_branches(requested_repositories, query):
    for repo in requested_repositories:
        branches = _find_matching_branches(repo, query)
        if branches:
            print("%s : %s" % (repo, branches))


def fetch_repositories(requested_repositories):
    for repo_name in requested_repositories:
        cmd = sh.git.bake('fetch', '-p')
        ret = _exec_git_command(cmd, repo_name)
        if ret:
            print("%s" % ret)


def rsync_repositories(remote_host, requested_repositories, dry_run):
    logger.debug('host: %s | requested repos : %s', remote_host, requested_repositories)
    for repo_name in requested_repositories:
        _rsync_repository(remote_host, repo_name, dry_run)


def batch_git_repositories(git_command, requested_repositories):
    logger.debug('git command: %s | requested repos : %s', git_command, requested_repositories)
    for repo_name in requested_repositories:
        ret = _exec_git_command(git_command, repo_name)
        if ret:
            print("%s" % ret)


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
    sh.VBoxHeadless('-s', name, '-v', 'on', _bg=True)
    logger.info("started vm %s", name)


def kill_vm(name):
    sh.VBoxManage('controlvm', name, 'poweroff')
    logger.info("stopped vm %s", name)


def snapshot_vm(name, description):
    sh.VBoxManage('snapshot', name, 'take', description)
    logger.info("snapshot vm %s with description %s", name, description)


def build_client():
        sh.make('distclean', _ok_code=(0, 1, 2))
        repo_dir = _repo_path('xivo-client-qt')
        print('running qmake...')
        sh.Command('qmake')('QMAKE_CXX=colorgcc', _cwd=repo_dir)
        print('running make...')
        sh.make('-j4', 'FUNCTESTS=yes', 'DEBUG=yes', _cwd=repo_dir)


def build_doc():
    pass


def _rsync_repository(remote_host, repo_name, dry_run):
    if _repo_is_syncable(repo_name):
        remote_uri = _remote_uri(remote_host, repo_name)
        local_path = _get_local_path(repo_name)
        rsync = sh.rsync.bake("-v", "-rtlp", "--exclude", "'*.pyc'", "--exclude", "'*.swp'", "--delete")
        logger.debug('about to execute rsync command : %s %s %s', rsync, local_path, remote_uri)
        if not dry_run:
            rsync(local_path, remote_uri)


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
    cmd = sh.git.bake('pull')
    current_branch = _get_current_branch(repo_name)
    if(current_branch == 'master'):
        return _exec_git_command(cmd, repo_name)
    else:
        return 'Not on branch master (%s)' % current_branch


def _get_current_branch(repo):
    cmd = sh.git.bake('name-rev', '--name-only', 'HEAD')
    return _exec_git_command(cmd, repo).strip()


def _find_matching_branches(repo, query):
    repo_dir = _repo_path(repo)
    branches = sh.git('br', '-a', _cwd=repo_dir)
    return str(sh.ag(branches, query, _ok_code=(0, 1))).strip()


def _exec_git_command(command, repo):
    logger.debug('%s on %s', command, repo)
    repo_dir = _repo_path(repo)
    return command(_cwd=repo_dir)


def delete_merged_branches(repositories, dry_run):
    if dry_run:
        print '*****************************************************************'
        print 'Deleting branches already merged into master'
        print 'Will not actually delete anything yet.'
        print 'Drop the -d (--dry) argument to confirm'
        print '*****************************************************************'
        print ''

    for repository in repositories:
        # logger.info('%s : %s', repo_name, _pull_repository_if_on_master(repo_name))
        for branch in _get_merged_branches(repository):
            if dry_run:
                print ("%s : About to delete branch %s" % (repository, branch))
            else:
                print _delete_branch(repository, branch)


def _get_merged_branches(repository):
    ''' a list of merged branches, not couting the current branch or master '''
    cmd = sh.git.bake('branch', '--merged', 'origin/master')
    raw_results = _exec_git_command(cmd, repository)
    return [b.strip() for b in raw_results.split('\n')
            if b.strip() and not b.startswith('*') and b.strip() != 'master']


def _delete_branch(repository, branch):
    cmd = sh.git.bake('branch', '-D', branch)
    return _exec_git_command(cmd, repository)


def _dispatch(args):
    if args.fetch:
        fetch_repositories(args.repos)

    if args.coverage:
        check_coverage(args.repos)

    if args.pull:
        pull_repositories(args.repos)

    if args.tags:
        update_ctags()

    if args.sync:
        rsync_repositories(args.sync, args.repos, args.dry)

    if args.batch:
        git_command = sh.git.bake(args.batch.split())
        batch_git_repositories(git_command, args.repos)

    if args.vmlist:
        list_vms()

    if args.vmstop:
        kill_vm(args.vmstop)

    if args.vmsnapshot:
        name, description = args.vmsnapshot
        snapshot_vm(name, description)

    if args.vmstart:
        start_vm(args.vmstart)

    if args.buildclient:
        build_client()

    if args.builddoc:
        build_doc()

    if args.grepbranches:
        grep_branches(args.repos, args.grepbranches)

    if args.list:
        list_repositories_with_branch(args.repos)

    if args.longlist:
        list_repositories_with_details(args.repos)

    if args.deletemerged:
        delete_merged_branches(args.repos, args.dry)


def main():
    args = parse_args()
    init_logging(args)
    print("")  # enforced newline
    _dispatch(args)
    print_mantra()


if __name__ == "__main__":
    main()
