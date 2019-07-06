#!/usr/bin/env python3

import argparse
import os
from datetime import datetime

from util.argurl import URLcheck
from util.db import DBLite
from util.wpjson import WP

me = os.path.realpath(__file__)
dr = os.path.dirname(me)


def parse(o, media=False):
    d = {k: v for k, v in o.items() if k in (
        "id", "type", "date", "link", "author")}
    d["date"] = datetime.strptime(d["date"], '%Y-%m-%dT%H:%M:%S')
    if media:
        full = o.get("media_details", {}).get("sizes",{}).get("full")
        if full:
            d["link"] = full["source_url"]
            d["type"] = full["mime_type"]
        else:
            d["link"] = o["source_url"]
    else:
        d["content"] = o["content"]["rendered"].strip()
        d["title"] = o["title"]["rendered"].strip()
    return d


parser = argparse.ArgumentParser(
    description='Crea una base de datos sqlite con el contendio de un wordpress')
parser.add_argument('--out', type=str, help='Fichero de salida')
parser.add_argument('url', type=URLcheck(), help='URL del wordpress')

schema = dr+"/util/schema.sql"
arg = parser.parse_args()
wp = WP(arg.url, progress="{}: {}")
if arg.out is None:
    arg.out = wp.info.name.lower().replace(" ", "_")+".db"
print(wp.info.name, "---->", arg.out)
print("%5s posts" % len(wp.posts))
print("%5s pages" % len(wp.pages))
#print("%5s media" % len(wp.media))
objects = sorted(wp.posts + wp.pages, key=lambda x: x["id"])
users = set([p["author"] for p in objects])
users = [i for i in wp.users if i["id"] in users]
print("%5s users" % len(wp.users))
print("%5s tags" % len(wp.tags))
print("%5s categories" % len(wp.categories))
tags = {i["id"]: i["name"].strip() for i in wp.tags}
total = len(objects) + len(users) + len(wp.categories)
count = 0
db = DBLite(arg.out)
db.execute(schema)

for u in users:
    avatar = max(u["avatar_urls"].keys())
    u["avatar"] = u["avatar_urls"][avatar]
    db.insert("users", **u)
    count = count + 1
    print("Creando sqlite {0:.0f}%".format(count*100/total), end="\r")

for c in wp.categories:
    db.insert("categories", **c)
    count = count + 1
    print("Creando sqlite {0:.0f}%".format(count*100/total), end="\r")

for p in objects:
    db.insert("posts", **parse(p))
    for c in set([tags[c] for c in p.get("tags", [])]):
        db.insert("tags", tag=c, post=p["id"])
    for c in  p.get("categories", []):
        db.insert("post_category", category=c, post=p["id"])
    count = count + 1
    print("Creando sqlite {0:.0f}%".format(count*100/total), end="\r")

# for m in wp.media:
#     db.insert("media", **parse(m, media=True))
#     count = count + 1
#     print("Creando sqlite {0:.0f}%".format(count*100/total), end="\r")

print("Creando sqlite 100%")
db.close()
print("Tamaño: "+db.size())
