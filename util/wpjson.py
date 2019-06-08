from functools import lru_cache

import requests
from bunch import Bunch


class WP:
    def __init__(self, url, progress=None):
        self.url = url
        if url.endswith("/"):
            url = url[:1]
        self.rest_route = url + "/?rest_route="
        self.info = Bunch(**self.get("/"))
        self.progress = progress

    def get(self, path):
        r = requests.get(self.rest_route+path)
        return r.json()

    def get_object(self, tp, size=100, page=1):
        return self.get("/wp/v2/{}/&per_page={}&page={}".format(tp, size, page))

    def get_all_objects(self, tp, size=100):
        rs = []
        page = 0
        while True:
            page = page + 1
            r = self.get_object(tp, size=size, page=page)
            if isinstance(r, list) and len(r) > 0:
                rs.extend(r)
                if self.progress:
                    print(self.progress.format(tp, len(rs)), end="\r")
            else:
                return sorted(rs, key=lambda x: x["id"])

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
