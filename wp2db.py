#!/usr/bin/env python3

import argparse
import os
from datetime import datetime
import re
import sys

from util.argwp import WPcheck
from util.db import DBLite
from util.wpjson import WP, secureWP

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

def readfile(file):
    with open(file, "r") as f:
        return f.read().strip()

create_site = readfile(dr+"/sql/create-site.sql")
re_site_tables = re.findall(r"create\s+table\s+(\S+)\s*\(", create_site, flags=re.IGNORECASE)
re_site_tables = sorted(set(re_site_tables))
re_site_tables = re.compile(r"\b("+"|".join(re_site_tables)+r")\b", re.IGNORECASE)

def get_create(blog_id):
    return re_site_tables.sub(("b%d_" % blog_id) + r"\1", create_site)

parser = argparse.ArgumentParser(
    description='Crea una base de datos sqlite con el contendio de un wordpress')
parser.add_argument('--out', type=str, help='Fichero de salida')
parser.add_argument('--subdom', action='store_true', help='Cargar tambien subdominos')
parser.add_argument('--tags', action='store_true', help='Guardar tags')
parser.add_argument('--media', action='store_true', help='Guardar media')
parser.add_argument('--excluir', nargs='*', help='Excluir algunos subdominios (cuano se usa --subdom)')
parser.add_argument('url', nargs='*', type=WPcheck(), help='URL del wordpress')

arg = parser.parse_args()

if not arg.out and not arg.url:
    sys.exit("Ha de rellenara al menos uno de estos parametros: --out, url")
if arg.url:
    arg.url = [WP(url, progress="{}: {}") for url in arg.url]

if arg.out is None:
    arg.out = arg.url[0].info.name.lower().replace(" ", "_")+".db"
print(">>>", arg.out)

db = DBLite(arg.out)
if "blogs" not in db.tables:
    db.execute(dr+"/sql/create-ms.sql")
if not arg.url:
    arg.url = [secureWP(url, progress="{}: {}") for url in db.select("select url from blogs order by id")]
    arg.url = [wp for wp in arg.url if wp is not None]
    if not arg.url:
        sys.exit(arg.out+" no contiene blogs")

visto=set()
wp_error=[]
main_dom = '.'+arg.url[0].dom
while arg.url:
    wp = arg.url.pop(0)
    visto.add(wp.dom)
    db.prefix=""

    blog_id = db.select("select id from blogs where url='%s'" % wp.url, to_one=True)
    if blog_id:
        db.prefix = "b%d_" % blog_id
        db.drop()
    else:
        blog_id = db.select("select IFNULL(max(id),0)+1 from blogs", to_one=True)
        db.insert("blogs", id=blog_id, name=wp.info.name, url=wp.url)
        db.prefix = "b%d_" % blog_id

    script = get_create(blog_id)
    db.execute(script)

    if wp.error:
        wp_error.append(wp)
        continue

    print("")
    print(wp.dom)
    print("%5s posts" % len(wp.posts))
    print("%5s pages" % len(wp.pages))
    #print("%5s media" % len(wp.media))
    objects = sorted(wp.posts + wp.pages, key=lambda x: x["id"])
    users = set([p["author"] for p in objects])
    users = [i for i in wp.users if i["id"] in users]
    print("%5s users" % len(wp.users))
    if arg.tags:
        print("%5s tags" % len(wp.tags))
        tags = {i["id"]: i["name"].strip() for i in wp.tags}
    else:
        db.drop("tags")
    print("%5s categories" % len(wp.categories))
    total = len(objects) + len(users) + len(wp.categories)
    if arg.media:
        print("%5s media" % len(wp.media))
        total = total + len(wp.media)
    else:
        db.drop("media")
    count = 0

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
        if arg.tags:
            for c in set([tags[c] for c in p.get("tags", [])]):
                db.insert("tags", tag=c, post=p["id"])
        for c in  p.get("categories", []):
            db.insert("post_category", category=c, post=p["id"])
        count = count + 1
        print("Creando sqlite {0:.0f}%".format(count*100/total), end="\r")

    if arg.media:
        for m in wp.media:
            db.insert("media", **parse(m, media=True))
            count = count + 1
            print("Creando sqlite {0:.0f}%".format(count*100/total), end="\r")

    db.commit()
    print("Creando sqlite 100%")
    if arg.subdom:
        for target in wp.dom_targets:
            if target not in visto and target not in arg.excluir and target.endswith(main_dom):
                target = secureWP(target, progress="{}: {}")
                if target and target.dom not in visto and target.dom not in arg.excluir:
                    visto.add(target.dom)
                    arg.url.append(target)


for wp in wp_error:
    print("")
    print(wp.dom)
    print(" ", wp.error)

view="DROP VIEW IF EXISTS objects;\nCREATE VIEW objects AS"
for t in sorted(db.tables.keys()):
    if t.endswith("_posts") or t.endswith("_pages"):
        view=view+"\nselect *  from "+t+" union"
view=view[:-6]+";"
db.execute(view);
db.commit()
db.close()

print("")
print("Tamaño: "+db.size())
