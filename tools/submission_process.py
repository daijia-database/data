import datetime
import os
from inspect import isfunction
from os.path import dirname, join, realpath

import pandoc
import yaml
from pandoc.types import *

import cncities


def str_presenter(dumper, data):
    try:
        dlen = len(data.splitlines())
        if (dlen > 1):
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    except TypeError as ex:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, str_presenter)


def parse(text):
    doc = pandoc.read(text)

    def parse_place(v):
        province, city = cncities.parse(pandoc.write(v).strip())
        return {k: v for k, v in {'province': province, 'city': city}.items() if v}

    def parse_date(key):
        return lambda v: {key: datetime.date.fromisoformat(pandoc.write(v).strip())}

    def parse_int(key):
        return lambda v: {key: int(pandoc.write(v).strip())}

    keys_mapping = {
        '日期': parse_date('date'),
        '地点': parse_place,
        '死亡人数': parse_int('deaths'),
        '受伤人数': parse_int('injuries'),
        '受害人数': parse_int('victims'),
        '简短介绍': 'summary',
        '详细介绍': 'content',
    }

    h2 = None
    sections = {}
    for item in doc[1]:
        if isinstance(item, Header) and item[0] == 2:
            h2 = item[1][0]
        elif h2 and not isinstance(item, RawBlock):
            section = sections.get(h2, [])
            section.append(item)
            sections[h2] = section

    result = {}
    for h2 in sections:
        key = keys_mapping.get(h2, None)
        if not key:
            continue
        section = sections[h2]
        if isinstance(key, str):
            result[key] = pandoc.write(section).strip()
        elif isfunction(key):
            result.update(key(section))
    return result


def save_yaml(parsed, title):
    disallowed_char = '\/:*?"<>|'

    date: datetime.date = parsed['date']
    year = date.strftime('%Y')
    datadir = realpath(join(dirname(__file__), '..', 'yaml', year))
    if not os.path.exists(datadir):
        os.mkdir(datadir)
    for ch in disallowed_char:
        title = title.replace(ch, '-')
    with open(join(datadir, f'{date.strftime("%m-%d")} {title}.yml'), 'w') as f:
        yaml.dump(parsed, f, allow_unicode=True, sort_keys=False)
