from .db import DBLite, dict_factory
from os.path import realpath, dirname
import re

dr = dirname(realpath(__file__))
dr = dirname(dr)

def readfile(file):
    with open(file, "r") as f:
        return f.read().strip()

create_site = readfile(dr+"/sql/create-site.sql")
site_tables = re.findall(r"create\s+table\s+(\S+)\s*\(", create_site, flags=re.IGNORECASE)
site_tables = sorted(set(site_tables), key=lambda x:site_tables.index(x))
re_site_tables = re.compile(r"\b("+"|".join(site_tables)+r")\b", re.IGNORECASE)

def get_view(*args):
    for t in sorted(args):
        if not t.startswith("b") or "_" not in t:
            continue
        blog, tb = t.split("_", 1)
        blog = blog[1:]
        if not blog.isdigit():
            continue
        if tb in ("posts", "pages"):
            yield t, "objects", blog
        else:
            yield t, tb, blog

class DBwp(DBLite):
    def __init__(self, *args, **kargv):
        super().__init__(*args, **kargv)
        self.blog_id = None
        self.create_site = readfile(dr+"/sql/create-site.sql")
        self.site_tables = re.findall(r"create\s+table\s+(\S+)\s*\(", self.create_site, flags=re.IGNORECASE)
        self.site_tables = sorted(set(self.site_tables), key=lambda x:self.site_tables.index(x))
        self.re_site_tables = re.compile(r"\b("+"|".join(site_tables)+r")\b", re.IGNORECASE)
        for t in self.site_tables:
            self.create_site = "DROP TABLE IF EXISTS {};\n".format(t) + self.create_site

        if "blogs" not in self.tables:
            self.execute(readfile(dr+"/sql/create-ms.sql"))

    def mk_blog(self, wp):
        self.blog_id = self.one("select id from blogs where url=?", wp.id)
        if self.blog_id is None:
            self.blog_id = self.one("select IFNULL(max(id),0)+1 from blogs")
        self.insert("blogs", id=self.blog_id, name=wp.info.name, url=wp.id)
        prefix = self.get_prefix()
        sql = self.re_site_tables.sub(prefix + r"\1", self.create_site)
        self.execute(sql)

    def rm_blog(self, blog_id=None):
        bk_blog_id = None
        if blog_id is not None:
            bk_blog_id = self.blog_id
            self.blog_id = blog_id
        if self.blog_id is None:
            raise Exception("blog_id is None")
        self.drop(*self.site_tables)
        self.execute("delete from blogs where ID="+str(self.blog_id))
        self.blog_id = bk_blog_id

    def get_prefix(self, blog_id=None):
        if blog_id is None:
            blog_id = self.blog_id
        if blog_id is None:
            raise Exception("blog_id is None")
        return "b%d_" % blog_id

    def parse_table(self, table, blog_id=None):
        if table in self.tables or table not in self.site_tables :
            return table
        if blog_id is None:
            blog_id = self.blog_id
        if blog_id is None:
            raise Exception("blog_id is None")
        prefix = self.get_prefix(blog_id)
        table = prefix+table
        return table

    def count_blog(self, blog_id=None):
        if blog_id is None:
            blog_id = self.blog_id
        if blog_id is None:
            raise Exception("blog_id is None")
        self.load_tables()
        tbs={}
        for t in self.site_tables:
            t = self.parse_table(t, blog_id)
            if t in self.tables:
                tbs[t]=self.one("select count(*) from "+t)
        return tbs

    def insert(self, table, *args, insert_or="replace", **kargv):
        super().insert(self.parse_table(table), *args, insert_or=insert_or, **kargv)

    def drop(self, *tables):
        tables = (self.parse_table(t) for t in tables)
        super().drop(*tables)

    def rm_views(self):
        for v in self.to_list("SELECT name FROM sqlite_master WHERE type='view'"):
            self.execute("DROP VIEW "+v)


    def set_view(self):
        self.blog_id = None
        self.rm_views()
        views={}
        for t, tb, blog in get_view(*self.tables.keys()):
            view = views.get(tb, "CREATE VIEW {0} AS".format(tb))
            views[tb]=view+("\nselect {1} blog, {0}.* from {0} union".format(t, blog))
        for view in views.values():
            view=view[:-6]+";"
            self.execute(view)

    def minimize(self):
        self.blog_id = None
        for r in self.select("select * from blogs", row_factory=dict_factory):
            ct_blog = sum(self.count_blog(r["ID"]).values())
            if ct_blog == 0:
                print("Blog {url} vacio será borrado".format(**r))
                self.rm_blog(r["ID"])

        ct_blog = self.one("select count(*) from blogs")
        if ct_blog==1:
            self.rm_views()
            blog_id = self.one("select ID from blogs")
            prefix = self.get_prefix(blog_id)
            self.execute(self.create_site)
            for t in site_tables:
                self.execute("insert into {0} select * from {1}{0}".format(t, prefix))
            for t in self.site_tables:
                self.drop(prefix+t)
                count = self.one("select count(*) from "+t)
                if count == 0:
                    print("Tabla {} vacia será borrada".format(t))
                    self.drop(t)
        ct_blog = self.one("select count(*) from blogs")
        if ct_blog<2:
            self.drop("blogs")
        self.set_view()
