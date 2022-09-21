#!/usr/bin/env python3

from glob import glob
import os
from datetime import date
from os.path import dirname, expanduser, join, realpath
from sys import argv, stderr

import yaml
from github import Github

import submission_process

try:
    issue_number = int(argv[1])
except:
    print('需要指定Issue！', file=stderr)
    exit(1)

if 'GITHUB_TOKEN' in os.environ:
    gh = Github(os.environ['GITHUB_TOKEN'])
else:
    with open(expanduser('~/.config/gh/hosts.yml')) as f:
        hosts = yaml.load(f, Loader=yaml.SafeLoader)
        gh = Github(hosts['github.com']['oauth_token'])

issue = gh.get_repo('daijia-database/data').get_issue(number=int(argv[1]))


def parse_issue(i):
    result = submission_process.parse(i.body)
    result['issue'] = i.number
    return result


def delete_old_yaml(i):
    datadir = realpath(join(dirname(__file__), '..', 'yaml'))
    for p in glob(f'{datadir}/**/*.yml', recursive=True):
        with open(p) as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
            if data.get('issue', None) == i.number:
                os.unlink(p)
                return
        

parsed = parse_issue(issue)
delete_old_yaml(issue)
submission_process.save_yaml(parsed, issue.title)
