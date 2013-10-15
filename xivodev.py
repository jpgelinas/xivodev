#!/usr/bin/env python2

import argparse

DEV_HOST = "root@%s"
SOURCE_DIRECTORY = "/home/jp/src/xivo"
#SOURCE_DIRECTORY_FILES = "$SOURCE_DIRECTORY/*"
UPDATE_TAGS = False
PULL = False
RSYNC = False
LIST_BRANCHES = False
VERBOSE = False

REPOS = {
    'xivo-agentd': ('xivo_agent', '/usr/lib/pymodules/python2.6/xivo_agent'),
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
#env.host_ip = '192.168.32.'


def sync_all():
    for name in REPOS.iterkeys():
        sync(name)

def sync(name):
    #$base_command $SOURCE_DIRECTORY/${sync_sources[$user_option]} $DEV_HOST:${sync_destinations[$user_option]}
    #final_command = "base_command $SOURCE_DIRECTORY/${sync_sources[$user_option]} $DEV_HOST:${sync_destinations[$user_option]}"
    cmd = "%s %s %s" % (base_command, local_path(name), remote_uri(name))
    #cmd = 'mount %s:%s %s' % (env.host_ip, local_path(name), remote_path(name))
    #run(cmd)
    print(cmd)


def local_path(name):
    #repo = REPOS[name]
    return '%s/%s' % (SOURCE_DIRECTORY, REPOS[name][0])
    #return '%s/%s/%s/%s' % (env.root, name, name, repo[0])


def remote_uri(name):
    #repo = REPOS[name]
    return '%s:%s' % (DEV_HOST, REPOS[name][1])
    #return repo[1]


if __name__ == "__main__":
    parser = argparse.ArgumentParser('XiVO dev toolkit')
    parser.add_argument('xivo_host', help='IP or domain of target XiVO installation')

    args = parser.parse_args()
    DEV_HOST = DEV_HOST % (args.xivo_host)

    sync_all()
