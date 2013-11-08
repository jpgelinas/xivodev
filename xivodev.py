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
import os
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

base_command = "rsync -v -rtlp --exclude '*.pyc' --exclude '*.swp' --delete"
xivo_src = '/home/jp/src/xivo'


def list_repositories_with_branch():
    repos = [name for name in os.listdir(SOURCE_DIRECTORY) if (os.path.isdir(os.path.join(SOURCE_DIRECTORY, name)) and name in REPOS)]
    for name in repos:
        branch = _get_current_branch(name)
        print("%s : %s" % (name, branch))


def sync_all():
    for name in REPOS.iterkeys():
        sync(name)


def sync(name):
    cmd = "%s %s %s" % (base_command, local_path(name), remote_uri(name))
    print(cmd)


def local_path(name):
    return '%s/%s/%s/%s' % (SOURCE_DIRECTORY, name, name, REPOS[name][0])


def remote_uri(name):
    return '%s:%s' % (DEV_HOST, REPOS[name][1])


def update_tags():
    subprocess.call(['ctags', '-R', '-f', '~/.mytags', SOURCE_DIRECTORY_FILES])


# Broken : no colors
def print_mantra():
    print "\e[00;31mReady\e[00m, \e[1;33mSet\e[00m, \e[0;32mC0DE!\e[00m"


def _get_current_branch(repo):
    cmd = ['git', 'rev-parse',  '--abbrev-ref',  'HEAD']
    return _exec_git_command(cmd, repo).strip()


def _exec_git_command(cmd, repo):
    repo_dir = local_path(repo)
    #print repo_dir
    #print cmd
    #subprocess.['pushd', repo_dir])
    #result = subprocess.call(cmd)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=repo_dir)
    result = process.communicate()
    #subprocess.call(['popd'])
    return result[0]


def update_ctags():
    #result=`ctags -R -f ~/.mytags $SOURCE_DIRECTORY_FILES`
    ctag_file = "~/.mytags"
    cmd = "ctags -R -f %s %s" % (ctag_file, SOURCE_DIRECTORY_FILES)
    print cmd
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    result = process.communicate()
    print("Updated CTAGS %s : %s" % (ctag_file, result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser('XiVO dev toolkit')
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")
    parser.add_argument("-t", "--tags", help="update CTAGS",
                        action="store_true")
    parser.add_argument("-p", "--pull", help="git pull repositories",
                        action="store_true")
    parser.add_argument("-l", "--list", help="list all repositories and their current branch",
                        action="store_true")
    parser.add_argument("-r", "--rsync", help='sync repos on given IP or domain')

    args = parser.parse_args()

    if args.rsync:
        #DEV_HOST = DEV_HOST % (args.host)
        #sync_all()
        pass

    if args.list:
        list_repositories_with_branch()

    if args.tags:
        update_ctags()
