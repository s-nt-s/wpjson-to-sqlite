#!/usr/bin/env python3

import argparse
import os
from datetime import datetime, date
import re
import sys
from shutil import copyfile
import urllib3
from os.path import basename, dirname, join

from util.argwp import WPcheck
from util.dbwp import DBwp
from util.wpjson import WP, secureWP

urllib3.disable_warnings()

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
        d["post"] = o.get("post")
        d["parent"] = o.get("parent")
        if "title" in o:
            d["title"] = o["title"]["rendered"].strip()
    return d

def main(arg):
    if arg.url:
        arg.url = [WP(url, progress="{}: {}") for url in arg.url]

    if arg.out is None:
        arg.out = arg.url[0].info.name.lower().replace(" ", "_")+".db"
    print(">>>", arg.out)

    db = DBwp(arg.out)
    if not arg.url:
        arg.url = [secureWP(url, progress="{}: {}") for url in db.to_list("select url from blogs order by id")]
        arg.url = [wp for wp in arg.url if wp is not None]
        if not arg.url:
            sys.exit(arg.out+" no contiene blogs")

    visto=set()
    wp_error=[]
    main_dom = '.'+arg.url[0].dom
    while arg.url:
        wp = arg.url.pop(0)
        wp.excluir = arg.excluir.get(wp.id)
        visto.add(wp.dom)

        db.mk_blog(wp)

        if wp.error:
            wp_error.append(wp)
            continue

        print("")
        print(wp.id)
        print("{:>5} posts ".format(len(wp.posts)))
        print("{:>5} pages ".format(len(wp.pages)))
        #print("%5s media" % len(wp.media))
        objects = sorted(wp.posts + wp.pages, key=lambda x: x["id"])
        users = set([p["author"] for p in objects])
        users = [i for i in wp.users if i["id"] in users]
        print("{:>5} users ".format(len(wp.users)))
        if arg.tags:
            print("{:>5} tags ".format(len(wp.tags)))
            tags = {i["id"]: i["name"].strip() for i in wp.tags}
        else:
            db.drop("tags")
        print("{:>5} categories ".format(len(wp.categories)))
        total = len(objects) + len(users) + len(wp.categories)
        if arg.media:
            print("{:>5} media ".format(len(wp.media)))
            total = total + len(wp.media)
        else:
            db.drop("media")
        if arg.comments:
            print("{:>5} comments ".format(len(wp.comments)))
            total = total + len(wp.comments)
        else:
            db.drop("comments")
        count = 0

        for u in users:
            if "avatar_urls" in u:
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
        if arg.comments:
            for m in wp.comments:
                db.insert("comments", **parse(m))
                count = count + 1
                print("Creando sqlite {0:.0f}%".format(count*100/total), end="\r")

        db.commit()
        print("Creando sqlite 100%")
        if arg.subdom:
            for target in wp.dom_targets:
                if target not in visto and target not in arg.excluir_dom and target.endswith(main_dom):
                    target = secureWP(target, progress="{}: {}")
                    if target and target.dom not in visto and target.dom not in arg.excluir_dom:
                        visto.add(target.dom)
                        arg.url.append(target)

    for wp in wp_error:
        print("")
        print(wp.id)
        print(" ", wp.error)

    db.set_view()
    db.commit()
    db.close()

    print("")
    print("Tamaño: "+db.size())

    if arg.zip:
        new_out = join(dirname(arg.out), date.today().strftime("%Y.%m.%d")+"_"+basename(arg.out))
        zip = arg.out.rsplit(".", 1)[0]+".7z"
        copyfile(arg.out, new_out)
        db = DBwp(new_out)
        db.minimize()
        db.close()
        print("Tamaño comprimido: "+db.zip(zip=zip))
        os.remove(new_out)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Crea una base de datos sqlite con el contendio de un wordpress')
    parser.add_argument('--out', type=str, help='Fichero de salida')
    parser.add_argument('--subdom', action='store_true', help='Cargar tambien subdominos')
    parser.add_argument('--tags', action='store_true', help='Guardar tags')
    parser.add_argument('--media', action='store_true', help='Guardar media')
    parser.add_argument('--comments', action='store_true', help='Guardar comentarios')
    parser.add_argument('--excluir', nargs='*', help='Excluir post/page de algún dominio. Formato web:id1,id2 o web si se excluye por completo', default=[])
    parser.add_argument('--zip', action='store_true', help='Crea una versión reducida y hace un 7z de ella')
    parser.add_argument('url', nargs='*', type=WPcheck(), help='URL del wordpress')

    arg = parser.parse_args()
    _excluir = {}
    _excluir_dom=set()
    for no in arg.excluir:
        if ":" not in no:
            _excluir_dom.add(no)
        dom, ids = no.split(":")
        ids = [int(i) for i in ids.split(",")]
        _excluir[dom]=ids
    arg.excluir = _excluir
    arg.excluir_dom = _excluir_dom
    if not arg.out and not arg.url:
        sys.exit("Ha de rellenara al menos uno de estos parametros: --out, url")
    main(arg)
