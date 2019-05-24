#!/usr/bin/env python

import sys
from pprint import pprint

try:
    import requests
except ImportError:
    print("Failed to import requests")
    sys.exit(1)


if len(sys.argv) < 2:
    print(f"Need a username, found {sys.argv}")
    sys.exit(2)

username = sys.argv[1]

url = f"https://boardgamegeek.com//xmlapi2/collection?username={username}&trade=1"

def tryforrequest(req_url):
    resp = requests.get(req_url)
    if resp.status_code != 200:
        import time
        time.sleep(1)
        return tryforrequest(req_url)

    return resp.text

out = tryforrequest(url)

import xml.etree.ElementTree as ET

parsed = ET.fromstring(out)

formaturl = 'https://boardgamegeek.com/boardgame/{id}/'
formatlink = '[{name}]({url})'
formatrow = '{link}|{condition}|{price}|{notes}'

gamerow = {}


def getlink(item):
    name = item[0].text
    attrs = item.attrib
    url = formaturl.format(id=attrs["objectid"])
    return formatlink.format(name=name,
                             url=url)


def parse_metadata(item) -> dict:
    name = item[0].text
    conditiontext = item.find('conditiontext')
    if conditiontext is not None:
        import re
        jsonstring = re.search(r'bggtrade2reddit:(.*)', conditiontext.text)
        if jsonstring:
            metadata = jsonstring.group(1)
            import json
            return json.loads(metadata)

    return {}
    

def should_ignore(item) -> bool:
    return parse_metadata(item).get('ignore', False)


def getcondition(item):
    metadata = parse_metadata(item)
    if 'condition' in metadata:
        return metadata['condition']

    return -1


def get_price(item) -> str:
    metadata = parse_metadata(item)
    if 'price' in metadata:
        return metadata['price']

    return -1


def get_extras(item) -> str:
    metadata = parse_metadata(item)
    if 'extras' in metadata:
        return metadata['extras']

    return ''


def to_game_dict(item):
    if should_ignore(item):
        return None

    name = item[0].text
    attrs = item.attrib
    url = formaturl.format(id=attrs["objectid"])
    return {'name': item[0].text,
            'link': getlink(item),
            'condition': getcondition(item),
            'price': f'${get_price(item)}',
            'extras': get_extras(item),
            'notes': []}


def transformrow(row):
    if len(row['notes']) > 0:
        row['link'] = row['link'] + " Bundle"
        row['notes'] = 'Bundle includes: ' + ', '.join(row['notes'])
    else:
        row['notes'] = ""

    row['notes'] = row['extras'] + ' ' + row['notes']
    return row


for item in parsed:
    name = item[0].text
    expansion = [ x for x in gamerow.keys() if name.startswith(x) ]
    if len(expansion) > 0:
        gamerow[expansion[0]]['notes'].append(getlink(item))
    else:
        game_dict = to_game_dict(item)
        if not game_dict:
            continue
        gamerow[name] = game_dict


print('\n\n---- Generating table below -----------------\n')

print("Game|Condition|Price (OBO)|Notes")
print(":--|:--|:--|:--")
for r in [ formatrow.format(**transformrow(v)) for k, v in gamerow.items() ]:
    print(r)

print('\n---- Done generating table --------------------')





