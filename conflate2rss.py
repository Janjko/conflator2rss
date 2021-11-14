#!/usr/bin/python

from datetime import datetime, tzinfo
import os
import shutil
import argparse
import json
import jsondiff as jd
from jsondiff import diff
from feedgen.feed import FeedGenerator
from enum import Enum


class change_status(str, Enum):
    CREATE_NONE = 'CREATE_NONE'
    MODIFY_NONE = 'MODIFY_NONE'
    CREATE_MODIFY = 'CREATE_MODIFY'
    MODIFY_CREATE = 'MODIFY_CREATE'
    NONE_CREATE = 'NONE_CREATE'
    NONE_MODIFY = 'NONE_MODIFY'


CHANGE_STATUS = 'change_status'
ELEMENT_REF = 'element_ref'
OSM_ID = 'osm_id'

RSS_RAW_FILENAME = "rss_raw.json"
#RSS_FILENAME = "rss.xml"

fg = FeedGenerator()
fg.id('http://lernfunk.de/media/654321')
fg.title('Some Testfeed')
fg.author({'name': 'John Doe', 'email': 'john@example.de'})
fg.link(href='http://example.com', rel='alternate')
fg.logo('http://ex.com/logo.jpg')
fg.subtitle('This is a cool feed!')
fg.link(href='http://larskiesow.de/test.atom', rel='self')
fg.language('en')

# Dictionary that holds the raw rss data, from which the rss is created
rss_raw = {}

TITLE = "OSM Garden"
parser = argparse.ArgumentParser(
    description='''{}.
        Reads a profile with source data and conflates it with OpenStreetMap data.
        Produces an JOSM XML file ready to be uploaded.'''.format(TITLE))

parser.add_argument('-n', '--new', type=argparse.FileType('r',
                    encoding='utf-8'), help='New file')
parser.add_argument('-i', '--inspected', type=argparse.FileType('r',
                    encoding='utf-8'), help='Output OSM XML file name')
parser.add_argument(
    '-r', '--rss', type=argparse.FileType('w'), help='RSS XML file')

#options = parser.parse_args(["-n", "C:\\Users\\Janko\\source\\garden\\jsons\\current\\changes.json", "-i",
#                           "C:\\Users\\Janko\\source\\garden\\jsons\\inspected\\changes.json", "-r", "C:\\Users\\Janko\\source\\garden\\jsons\\current\\rss.xml"])

options = parser.parse_args()

n = 1

try:
    with open(RSS_RAW_FILENAME, 'r') as json_file:
        rss_raw = json.load(json_file)
        numbers = rss_raw.keys()
        if len(numbers) > 0:
            n = int(max(numbers))+1
except IOError:
    with open(RSS_RAW_FILENAME, 'w') as json_file:
        json.dump(rss_raw, json_file)

oldJson = json.load(options.inspected)
newJson = json.load(options.new)

for element in oldJson['features']:
    matches = list(filter(lambda x: (
        x['properties']['ref_id'] == element['properties']['ref_id']), newJson['features']))
    if len(matches) == 0:
        if element['properties']['action'] == 'create':
            rss_raw.update({n: {CHANGE_STATUS: change_status.CREATE_NONE,
                                ELEMENT_REF: element['properties']['ref_id']}})
            n += 1
        if element['properties']['action'] == 'modify':
            rss_raw.update({n: {CHANGE_STATUS: change_status.MODIFY_NONE,
                                ELEMENT_REF: element['properties']['ref_id'], OSM_ID: element['properties']['osm_id']}})
            n += 1

    for matched_element in matches:
        if element['properties']['action'] == 'create' and matched_element['properties']['action'] == 'modify':
            rss_raw.update({n: {CHANGE_STATUS: change_status.CREATE_MODIFY,
                                ELEMENT_REF: element['properties']['ref_id']}})
            n += 1

        if element['properties']['action'] == 'modify' and matched_element['properties']['action'] == 'create':
            rss_raw.update({n: {CHANGE_STATUS: change_status.MODIFY_CREATE,
                                ELEMENT_REF: element['properties']['ref_id']}})
            n += 1

for element in newJson['features']:
    if not any(x['properties']['ref_id'] == element['properties']['ref_id'] for x in oldJson['features']):
        if element['properties']['action'] == 'create':
            rss_raw.update({n: {CHANGE_STATUS: change_status.NONE_CREATE,
                           ELEMENT_REF: element['properties']['ref_id']}})
            n += 1
        if element['properties']['action'] == 'modify':
            rss_raw.update({n: {CHANGE_STATUS: change_status.NONE_MODIFY,
                           ELEMENT_REF: element['properties']['ref_id']}})
            n += 1


with open(RSS_RAW_FILENAME, 'w') as fp:
    json.dump(rss_raw, fp)

for entry in rss_raw:
    fe = fg.add_entry()
    if rss_raw[entry][CHANGE_STATUS] == change_status.CREATE_NONE or rss_raw[entry][CHANGE_STATUS] == change_status.MODIFY_NONE:
        fe.title("Element ispravno ucrtan.")
        fe.description('Ispravno ucrtan element ' +
                       element['properties']['ref_id'])
    if rss_raw[entry][CHANGE_STATUS] == change_status.NONE_CREATE or rss_raw[entry][CHANGE_STATUS] == change_status.MODIFY_CREATE:
        fe.title("Element obrisan!")
        fe.description('Element ' +
                       element['properties']['ref_id'] + ' obrisan, ili je izgubio osnovne tagove.')
    if rss_raw[entry][CHANGE_STATUS] == change_status.NONE_MODIFY:
        fe.title("Elementu pokvareni tagovi.")
        fe.description('Elementu ' +
                       element['properties']['ref_id'] + ' pokvareni tagovi.')
    if rss_raw[entry][CHANGE_STATUS] == change_status.CREATE_MODIFY:
        fe.title("Element ucrtan, ali sa lošim tagovima.")
        fe.description('Element ' +
                       element['properties']['ref_id'] + ' ucrtan, ali sa lošim tagovima.')


fg.rss_file(options.rss.name)
