#!/usr/bin/env python3

import argparse
import os
from datetime import datetime

from util.argurl import URLcheck
from util.db import DBLite
from util.wpjson import WP

me = os.path.realpath(__file__)
dr = os.path.dirname(me)


def parse(o):
    d = {k: v for k, v in o.items() if k in (
        "id", "type", "date", "link", "author")}
    d["content"] = o["content"]["rendered"].strip()
    d["title"] = o["title"]["rendered"].strip()
    d["date"] = datetime.strptime(d["date"], '%Y-%m-%dT%H:%M:%S')
    return d


parser = argparse.ArgumentParser(
    description='Crea una base de datos sqlite con el contendio de un wordpress')
parser.add_argument('url', type=URLcheck(), help='url del wordpress')

schema = dr+"/util/schema.sql"
arg = parser.parse_args()
wp = WP(arg.url, progress=" {}: {}")
print(wp.info.name)
print("%5s posts" % len(wp.posts))
print("%5s pages" % len(wp.pages))
objects = sorted(wp.posts + wp.pages, key=lambda x: x["id"])
users = set([p["author"] for p in objects])
users = [i for i in wp.users if i["id"] in users]
print("%5s users" % len(wp.users))
print("%5s tags" % len(wp.tags))
print("%5s categories" % len(wp.categories))
tags = {i["id"]: i["name"].strip() for i in wp.tags}
categories = {i["id"]: i["name"].strip() for i in wp.categories}
total = len(objects) + len(users)
count = 0
name = wp.info.name.lower().replace(" ", "_")+".db"
db = DBLite(name)
db.execute(schema)

for u in users:
    avatar = max(u["avatar_urls"].keys())
    u["avatar"] = u["avatar_urls"][avatar]
    db.insert("users", **u)
    count = count + 1
    print("Creando sqlite {0:.0f}%".format(count*100/total), end="\r")

for p in objects:
    db.insert("posts", **parse(p))
    for c in set([tags[c] for c in p.get("tags", [])]):
        db.insert("tags", type="tag", tag=c, post=p["id"])
    for c in set([categories[c] for c in p.get("categories", [])]):
        db.insert("tags", type="category", tag=c, post=p["id"])
    count = count + 1
    print("Creando sqlite {0:.0f}%".format(count*100/total), end="\r")

print("Creando sqlite 100%")
db.close()
print("Tamaño: "+db.size())
