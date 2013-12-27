#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

"""
usage: $0 options

This script git pulls all repos in directory with a few bells and whistles.

OPTIONS:
   -h      Show this message
   -s      Rsync given xivo ip|hostname
   -p      git pull repositories
   -t      Update ctags
   -l      List all repositories and their current branch
   -r      Concerned Repositories. By default, options affect all managed repositories. specifiying repos will limit the scope on wich options operate.
   -v      Verbose
"""

import argparse
import logging
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
    'xivo-amid': ('xivo_ami', '/usr/lib/pymodules/python2.6/'),
    'xivo-agent': ('xivo_agent', '/usr/lib/pymodules/python2.6/'),
    'xivo-agid': ('xivo_agid', '/usr/lib/pymodules/python2.6/'),
    'xivo-call-logs': ('xivo_call_logs', '/usr/lib/pymodules/python2.6/'),
    #'xivo-config': ('dialplan/asterisk', '/usr/share/xivo-config/dialplan/'),
    'xivo-confgen': ('xivo_confgen', '/usr/lib/pymodules/python2.6/'),
    'xivo-ctid': ('xivo_cti', '/usr/lib/pymodules/python2.6/'),
    'xivo-dao': ('xivo_dao', '/usr/lib/pymodules/python2.6/'),
    'xivo-dird': ('xivo_dird', '/usr/lib/pymodules/python2.6/'),
    'xivo-lib-python': ('xivo', '/usr/lib/pymodules/python2.6/'),
    #'xivo-provisioning': ('src/provd', '/usr/lib/pymodules/python2.6/'),
    'xivo-restapi': ('xivo_restapi', '/usr/lib/pymodules/python2.6/'),
    'xivo-stat': ('xivo_stat', '/usr/lib/pymodules/python2.6/'),
    'xivo-sysconfd': ('xivo_sysconf', '/usr/lib/pymodules/python2.6/'),
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


def list_repositories_with_branch(requested_repositories):
    for name in requested_repositories:
        branch = _get_current_branch(name)
        print("%s : %s" % (name, branch))


def rsync_repositories(remote_host, requested_repositories):
    logger.debug('host: %s | requested repos : %s', remote_host, requested_repositories)
    for repo_name in requested_repositories:
        _rsync_repository(remote_host, repo_name)


def _rsync_repository(remote_host, repo_name):
    cmd = "%s %s %s" % (base_command, _local_path(repo_name), _remote_uri(remote_host, repo_name))
    logger.debug('about to execute rsync command : %s', cmd)
    subprocess.call(shlex.split(cmd))


def _local_path(name):
    return '%s/%s/%s/%s' % (SOURCE_DIRECTORY, name, name, REPOS[name][0])


def _remote_uri(remote_host, repo_name):
    return '%s:%s' % (remote_host, REPOS[repo_name][1])


def update_ctags():
    ctag_file = "/home/jp/.mytags"
    cmd = 'ctags -R --exclude="*.js" -f {tag_file} {src} '.format(tag_file=ctag_file, src=SOURCE_DIRECTORY)
    subprocess.call(shlex.split(cmd))
    logger.info("Updated CTAGS %s", ctag_file)


def pull_repositories(requested_repositories):
    for repo_name in requested_repositories:
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


def _get_current_branch(repo):
    cmd = 'git rev-parse --abbrev-ref HEAD'
    return _exec_git_command(cmd, repo).strip()


def _exec_git_command(cmd, repo):
    logger.debug('%s on %s', cmd, repo)
    cmd = shlex.split(cmd)
    repo_dir = _local_path(repo)
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
    parser.add_argument("-s", "--sync", help='sync repos on given IP or hostname')
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
        list_repositories_with_branch(args.repos)

    if args.tags:
        update_ctags()

    if args.pull:
        pull_repositories(args.repos)

    print_mantra()
