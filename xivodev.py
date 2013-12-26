#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

"""
usage: $0 options

This script git pulls all repos in directory with a few bells and whistles.

OPTIONS:
   +h      Show this message
   -r      Rsync given xivo vm
   -p      git pull repositories
   -t      Update ctags
   +l      List all repositories and their current branch
   -v      Verbose
"""

import argparse
import logging
import os
import shlex
import subprocess

DEV_HOST = "root@%s"
SOURCE_DIRECTORY = "/home/jp/src/xivo"
SOURCE_DIRECTORY_FILES = "%s/*" % SOURCE_DIRECTORY
UPDATE_TAGS = False
PULL = False
RSYNC = False
LIST_BRANCHES = False
VERBOSE = False

REPOS = {
    'xivo-agent': ('xivo_agent', '/usr/lib/pymodules/python2.6/xivo_agent'),
    'xivo-agid': ('xivo_agid', '/usr/lib/pymodules/python2.6/xivo_agid'),
    'xivo-call-logs': ('xivo_call_logs', '/usr/lib/pymodules/python2.6/xivo_call_logs'),
    'xivo-config': ('dialplan/asterisk', '/usr/share/xivo-config/dialplan/'),
    'xivo-confgen': ('xivo_confgen', '/usr/lib/pymodules/python2.6/xivo_confgen'),
    'xivo-ctid': ('xivo_cti', '/usr/lib/pymodules/python2.6/xivo_cti'),
    'xivo-dao': ('xivo_dao', '/usr/lib/pymodules/python2.6/xivo_dao'),
    'xivo-dird': ('xivo_dird', '/usr/lib/pymodules/python2.6/xivo_dird'),
    'xivo-lib-python': ('xivo', '/usr/lib/pymodules/python2.6/xivo'),
    'xivo-provisioning': ('src/provd', '/usr/lib/pymodules/python2.6/provd'),
    'xivo-restapi': ('xivo_restapi', '/usr/lib/pymodules/python2.6/xivo_restapi'),
    'xivo-stat': ('xivo_stat', '/usr/lib/pymodules/python2.6/xivo_stat'),
    'xivo-sysconfd': ('xivo_sysconf', '/usr/lib/pymodules/python2.6/xivo_sysconf'),
    'xivo-web-interface': ('src', '/usr/share/xivo-web-interface'),
}

logger = logging.getLogger(__name__)
base_command = "rsync -v -rtlp --exclude '*.pyc' --exclude '*.swp' --delete"
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


def list_repositories_with_branch():
    for name in _get_repos():
        branch = _get_current_branch(name)
        print("%s : %s" % (name, branch))


def rsync_repositories(host, requested_repositories):
    logger.debug('host: %s | requested repos : %s', host, requested_repositories)
    for name in requested_repositories:
        _rsync_repository(name)


def _rsync_repository(name):
    cmd = "%s %s %s" % (base_command, local_path(name), remote_uri(name))
    print(cmd)


def local_path(name):
    return '%s/%s/%s/%s' % (SOURCE_DIRECTORY, name, name, REPOS[name][0])


def remote_uri(name):
    return '%s:%s' % (DEV_HOST, REPOS[name][1])


def update_ctags():
    ctag_file = "/home/jp/.mytags"
    cmd = 'ctags -R --exclude="*.js" -f {tag_file} {src} '.format(tag_file=ctag_file, src=SOURCE_DIRECTORY)
    subprocess.call(shlex.split(cmd))
    logger.info("Updated CTAGS %s", ctag_file)


def pull_repositories():
    for repo_name in _get_repos():
        logger.info('%s : %s', repo_name, _pull_repository_if_on_master(repo_name))


def _pull_repository_if_on_master(repo_name):
    cmd = 'git pull'
    current_branch = _get_current_branch(repo_name)
    if(current_branch == 'master'):
        return _exec_git_command(cmd, repo_name)
    else:
        return 'Not on branch master (%s)' % current_branch


def print_mantra():
    print bcolors.FAIL + "Ready, " + bcolors.ENDC + bcolors.WARNING + "Set, " + bcolors.ENDC + bcolors.OKGREEN + "C0D3!" + bcolors.ENDC


def _get_repos():
    return [p for p in os.listdir(SOURCE_DIRECTORY)
            if (os.path.isdir(os.path.join(SOURCE_DIRECTORY, p)) and p in REPOS)]


def _get_current_branch(repo):
    cmd = 'git rev-parse --abbrev-ref HEAD'
    return _exec_git_command(cmd, repo).strip()


def _exec_git_command(cmd, repo):
    logger.debug('%s on %s', cmd, repo)
    cmd = shlex.split(cmd)
    repo_dir = local_path(repo)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=repo_dir)
    result = process.communicate()
    return result[0].strip()


def is_handled_repo(repo_name):
    if repo_name not in REPOS.iterkeys():
        msg = '%s is not a supported repository name' % repo_name
        raise argparse.ArgumentTypeError(msg)
    return repo_name


def _parse_args():
    parser = argparse.ArgumentParser('XiVO dev toolkit')
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")
    parser.add_argument("-t", "--tags", help="update CTAGS",
                        action="store_true")
    parser.add_argument("-p", "--pull", help="git pull repositories",
                        action="store_true")
    parser.add_argument("-l", "--list", help="list all repositories and their current branch",
                        action="store_true")
    parser.add_argument("-s", "--sync", help='sync repos on given IP or domain')
    parser.add_argument("-r", "--repos", help='list of repos on which to operate (default : all handled repos)',
                        nargs='*', type=is_handled_repo, default=[name for name in REPOS.iterkeys()])

    return parser.parse_args()


def _init_logging(args):
    level = logging.DEBUG if args.verbose else logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s (%(levelname)s): %(message)s'))
    root_logger.addHandler(handler)


if __name__ == "__main__":
    args = _parse_args()
    _init_logging(args)

    if args.sync:
        rsync_repositories(args.sync, args.repos)

    if args.list:
        list_repositories_with_branch()

    if args.tags:
        update_ctags()

    if args.pull:
        pull_repositories()

    print_mantra()
