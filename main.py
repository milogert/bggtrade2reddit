#!/usr/bin/env python


try:
    import requests
except ImportError:
    print("Failed to import requests")

try:
    from icecream import ic
except ImportError:
    ic = lambda *a: None if not a else (a[0] if len(a) == 1 else a)

import sys
from pprint import pprint
import re
import json
import xml.etree.ElementTree as ET


GAME_URL = "https://boardgamegeek.com/boardgame/{id}/"

if len(sys.argv) < 2:
    print(f"Need a username, found {sys.argv}")
    sys.exit(2)

username = sys.argv[1]

url = f"https://boardgamegeek.com//xmlapi2/collection?username={username}&trade=1"


def do_get(req_url):
    resp = requests.get(req_url)
    if resp.status_code != 200:
        ic("trying another request")
        import time

        time.sleep(1)
        return do_get(req_url)

    return resp.text


parsed = ET.fromstring(do_get(url))


def extract_link(item) -> str:
    name = item[0].text
    attrs = item.attrib
    url = GAME_URL.format(id=attrs["objectid"])
    return f"[{name}]({url})"


def parse_metadata(item) -> dict:
    name = item[0].text
    conditiontext = item.find("conditiontext")
    if conditiontext is not None:
        jsonstring = re.search(r"bggtrade2reddit:(.*)", conditiontext.text)
        if jsonstring:
            metadata = jsonstring.group(1)
            return json.loads(metadata)

    return {}


def should_ignore(item) -> bool:
    return parse_metadata(item).get("ignore", False)


def get_condition(item) -> int:
    metadata = parse_metadata(item)
    if "condition" in metadata:
        return metadata["condition"]

    return -1


def get_price(item) -> str:
    metadata = parse_metadata(item)
    if "price" in metadata:
        price = metadata["price"]
        if type(price) is int:
            return f"${price}"
        else:
            return price

    return "PRICE HERE"


def get_extras(item) -> str:
    metadata = parse_metadata(item)
    if "extras" in metadata:
        return metadata["extras"]

    return ""


def to_game_dict(item) -> dict:
    if should_ignore(item):
        return None

    name = item[0].text
    attrs = item.attrib
    url = GAME_URL.format(id=attrs["objectid"])
    return {
        "name": item[0].text,
        "link": extract_link(item),
        "condition": get_condition(item),
        "price": get_price(item),
        "extras": get_extras(item),
        "notes": [],
    }


def dict_to_table_row(row: dict) -> dict:
    if len(row["notes"]) > 0:
        row["link"] = row["link"] + " Bundle"
        row["notes"] = "Bundle includes: " + ", ".join(row["notes"])
    else:
        row["notes"] = ""

    row["notes"] = row["extras"] + " " + row["notes"]
    return row


gamerow = {}

for item in parsed:
    name = item[0].text
    expansion = [x for x in gamerow.keys() if name.startswith(x)]
    if len(expansion) > 0:
        gamerow[expansion[0]]["notes"].append(extract_link(item))
    else:
        game_dict = to_game_dict(item)
        if not game_dict:
            continue
        gamerow[name] = game_dict


print("\n\n---- Generating table below -----------------\n")

print("Game|Condition|Price (OBO)|Notes")
print(":--|:--|:--|:--")
[
    print("{link}|{condition}|{price}|{notes}".format(**dict_to_table_row(v)))
    for k, v in gamerow.items()
]

print("\n---- Done generating table --------------------")
