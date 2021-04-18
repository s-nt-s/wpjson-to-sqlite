from functools import lru_cache

import requests
from bunch import Bunch
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlencode
from simplejson.errors import JSONDecodeError
import json
import time

default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0',
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Expires": "Thu, 01 Jan 1970 00:00:00 GMT",
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def myex(e, msg):
    largs = list(e.args)
    if len(largs)==1 and isinstance(largs, str):
        largs[0]= largs[0]+' '+msg
    else:
        largs.append(msg)
    e.args = tuple(largs)
    return e


def get_requests(url, verify=False, intentos=3):
    try:
        return requests.get(url, verify=verify, headers=default_headers)
    except Exception as e:
        if intentos>0:
            time.sleep(15)
            return get_requests(url, verify=verify, intentos=intentos-1)
        raise myex(e, 'in request.get("%s")' % url)

def get_targets(url, html):
    if html and html.strip():
        soup = BeautifulSoup(html, 'html.parser')
        for n in soup.findAll(["img", "iframe", "a"]):
            attr = "href" if n.name == "a" else "src"
            href = n.attrs.get(attr)
            if href and not href.startswith("#"):
                try:
                    yield urljoin(url, href)
                except ValueError:
                    pass

def get_dom(url):
    p = urlparse(url)
    dom = p.netloc
    if dom.startswith("www."):
        dom=dom[4:]
    return dom

def secureWP(dom, http="http", **kargv):
    slp = dom.split("://", 1)
    if len(slp)==2:
        pro = slp[0].lower()
        url = slp[1]
        return secureWP(url, http=pro, **kargv)
    if http not in ("http", "https"):
        raise Exception("Protocolo no admitido "+http)
    try:
        return WP(http + "://" + dom, **kargv)
    except Exception as e:
        pass
    if not dom.startswith("www."):
        try:
            return WP(http + "://www." + dom, **kargv)
        except Exception as e:
            pass
    if http != "https":
        return secureWP(dom, http="https", **kargv)
    return None

class WP:
    def __init__(self, url, progress=None):
        self.last_url = None
        self.url = url.rstrip("/")
        self.id = self.url.split("://", 1)[1]
        self.rest_route = self.url + "/?rest_route="
        self.info = Bunch(**self.get("/"))
        self.progress = progress
        self.dom = get_dom(self.last_url or self.url)
        self.excluir = None

    def _json(self, url, intentos=3):
        r = get_requests(url)
        self.last_url = r.url
        try:
            js = r.json()
            return js
        except JSONDecodeError as e:
            if r.text and "[" in r.text and not r.text.strip().startswith("["):
                error, js = r.text.split("[", 1)
                try:
                    js = json.loads("["+js.strip())
                    return js
                except:
                    pass
            if intentos>0:
                time.sleep(15)
                return self._json(url, intentos=intentos-1)
            raise myex(e, 'in request.get("%s").json()' % url)
        except Exception as e:
            if intentos>0:
                time.sleep(15)
                return self._json(url, intentos=intentos-1)
            raise myex(e, 'in request.get("%s").json()' % url)

    def get(self, path):
        url = self.rest_route+path
        js = self._json(url)
        return js

    def get_object(self, tp, size=100, page=1, **kargv):
        url = "/wp/v2/{}/&per_page={}&page={}".format(tp, size, page)
        if "offset" in kargv and kargv["offset"] in (None, 0):
            del kargv["offset"]
        if kargv:
            url = url + "&" + urlencode(kargv, doseq=True)
        return self.get(url)

    def get_objects(self, tp, *ids):
        r = []
        for id in ids:
            url = "/wp/v2/{}/{}".format(tp, id)
            js = self.get(url)
            r.append(js)
        return r

    def safe_get_object(self, tp, size=100, page=1, **kargv):
        try:
            return self.get_object(tp, size=size, page=page, orderby='id', order='asc', **kargv)
        except JSONDecodeError:
            offset = max(((size)*(page-1)-1), 0)
            rs=[]
            for p in range(1, size+3):
                try:
                    r = self.get_object(tp, size=1, page=p, offset=offset, orderby='id', order='asc', **kargv)
                    if isinstance(r, list) and len(r) > 0:
                        rs.extend(r)
                    else:
                        return rs
                except JSONDecodeError:
                    pass
            return rs

    def get_all_objects(self, tp, size=100, **kargv):
        if tp in ("pages", "posts") and self.excluir:
            key = "exclude" if len(self.excluir)==1 else "exclude[]"
            kargv[key]=self.excluir
        rs = {}
        page = 0
        while True:
            page = page + 1
            r = self.safe_get_object(tp, size=size, page=page, **kargv)
            if isinstance(r, list) and len(r) > 0:
                for i in r:
                    rs[i["id"]] = i
                if self.progress:
                    print(self.progress.format(tp, len(rs)), end="\r")
            else:
                return sorted(rs.values(), key=lambda x: x["id"])

    @property
    @lru_cache(maxsize=None)
    def targets(self):
        targets=set()
        for p in self.posts + self.pages:
            for target in get_targets(p["link"], p["content"]["rendered"]):
                targets.add(target)
        return sorted(targets)

    @property
    @lru_cache(maxsize=None)
    def dom_targets(self):
        doms=set()
        for t in self.targets:
            doms.add(get_dom(t))
        return sorted(doms)

    @property
    @lru_cache(maxsize=None)
    def error(self):
        js = self.get_object("posts", size=1)
        if "code" in js:
            return js["code"] + " " + self.last_url
        return None

    @property
    @lru_cache(maxsize=None)
    def posts(self):
        return self.get_all_objects("posts")

    @property
    @lru_cache(maxsize=None)
    def pages(self):
        return self.get_all_objects("pages")

    @property
    @lru_cache(maxsize=None)
    def media(self):
        return self.get_all_objects("media")

    @property
    @lru_cache(maxsize=None)
    def comments(self):
        return self.get_all_objects("comments")

    @property
    @lru_cache(maxsize=None)
    def users(self):
        return self.get_all_objects("users")

    @property
    @lru_cache(maxsize=None)
    def tags(self):
        return self.get_all_objects("tags")

    @property
    @lru_cache(maxsize=None)
    def categories(self):
        return self.get_all_objects("categories")
