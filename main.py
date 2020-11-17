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
import pickle
import os.path
import getpass


GAME_URL = "https://boardgamegeek.com/boardgame/{id}/"
username = None

if len(sys.argv) < 2:
    username = input("Enter your username: ")
else:
    username = sys.argv[1]

url = f"https://boardgamegeek.com/xmlapi2/collection?username={username}&trade=1&showprivate=1&version=1"

r = requests.Session()

cookie_loaded = False
if os.path.exists(".cookie"):
    with open(".cookie", "rb") as f:
        r.cookies.update(pickle.load(f))
        cookie_loaded = True

if not cookie_loaded:
    password = getpass.getpass(prompt="Enter your password: ")


def login(session, username, password):
    login_resp = session.post(
        "http://boardgamegeek.com/login",
        data={"username": username, "password": password},
    )
    if login_resp.cookies.get("bggpassword") is None:
        print("Failed to log in!")
        sys.exit(1)


def do_get(session, req_url):
    resp = session.get(req_url)
    if resp.status_code != 200:
        ic("trying another request")
        import time

        time.sleep(1)
        return do_get(session, req_url)

    return resp.text


if not cookie_loaded:
    login(r, username, password)

    cookie_save_response = input("Do you want to stay logged in? (y/n) ")
    if cookie_save_response == "y":
        with open(".cookie", "wb") as f:
            pickle.dump(r.cookies, f)
            print("Saved your session in a file named .cookie")

parsed = ET.fromstring(do_get(r, url))


def extract_link(item) -> str:
    name = item[0].text
    attrs = item.attrib
    url = GAME_URL.format(id=attrs["objectid"])
    return f"[{name}]({url})"


def extract_version(item) -> str:
    try:
        return item.find('version').find('item').find('name').get('value')
    except:
        return "Not specified"


def extract_image(item) -> str:
    try:
        return item.find('version').find('item').find('image').text
    except:
        return None


def parse_metadata(item) -> dict:
    name = item[0].text
    private_info = item.find("privateinfo")
    ic(item.getchildren())
    if private_info is not None:
        private_comment = private_info.find("privatecomment").text
        if private_comment is not None:
            jsonstring = re.search(r"bggtrade2reddit:(.*)", private_comment)
            ic(jsonstring)
            if jsonstring:
                metadata = jsonstring.group(1)
                return json.loads(metadata)

    return {}


def should_ignore(metadata) -> bool:
    return metadata.get("ignore", False)


def get_condition(metadata) -> int:
    if "condition" in metadata:
        return metadata["condition"]

    return -1


def get_price(metadata) -> str:
    if "price" in metadata:
        price = metadata["price"]
        if type(price) is int:
            return f"${price}"
        else:
            return price

    return "PRICE HERE"


def get_extras(metadata) -> str:
    if "extras" in metadata:
        return metadata["extras"]

    return ""


def to_game_dict(item) -> dict:
    if should_ignore(item):
        return None

    name = item[0].text
    attrs = item.attrib
    url = GAME_URL.format(id=attrs["objectid"])
    metadata = parse_metadata(item)
    return {
        "name": item[0].text,
        "link": extract_link(item),
        "version": extract_version(item),
        "image_link": extract_image(item),
        "condition": get_condition(metadata),
        "price": get_price(metadata),
        "extras": get_extras(metadata),
        "notes": [],
    }


def dict_to_table_row(row: dict) -> dict:
    if len(row["notes"]) > 0:
        row["link"] = row["link"] + " Bundle"
        row["notes"] = "Bundle includes: " + ", ".join(row["notes"])
    else:
        row["notes"] = ""

    row["notes"] = row["extras"] + " " + row["notes"]

    if row['image_link']:
        row["version"] = "[" + row['version'] + "](" + row['image_link'] + ")"

    return row


gamerow = {}

limit = 0

for item in parsed:
    if False and limit == 5:
        break
    name = item[0].text
    expansion = [x for x in gamerow.keys() if name.startswith(x)]
    if len(expansion) > 0:
        gamerow[expansion[0]]["notes"].append(extract_link(item))
    else:
        game_dict = to_game_dict(item)
        if not game_dict:
            continue
        gamerow[name] = game_dict
        limit = limit + 1


print("\n\n---- Generating table below -----------------\n")

print("Game|Condition|Price (OBO)|Notes")
print(":--|:--|:--|:--")
[
    print("{link} ({version})|{condition}|{price}|{notes}".format(**dict_to_table_row(v)))
    for k, v in gamerow.items()
]

print("\n---- Done generating table --------------------")
