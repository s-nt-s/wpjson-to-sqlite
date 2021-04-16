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
        self.insert("blogs", insert_or="replace", id=self.blog_id, name=wp.info.name, url=wp.id)
        self.execute(self.create_blog)

    def rm_blog(self, blog_id):
        self.blog_id = blog_id
        self.drop(*self.site_tables)
        self.execute("delete from blogs where ID="+str(self.blog_id))
        self.blog_id = None

    @property
    def create_blog(self):
        if self.blog_id is None:
            raise Exception("blog_id is None")
        sql = self.re_site_tables.sub(self.prefix + r"\1", self.create_site)
        return sql

    @property
    def prefix(self):
        if self.blog_id is None:
            raise Exception("blog_id is None")
        return "b%d_" % self.blog_id

    def set_blod_id(self, id):
        if isinstance(id, str):
            self.blog_id = self.one("select id from blogs where url=?", wp.id)
        else:
            self.blog_id = id
        return self.blog_id

    def parse_table(self, table):
        if table!="blogs" and self.blog_id and not table.startswith(self.prefix):
            table = self.prefix+table
        return table

    def insert(self, table, *args, **kargv):
        super().insert(self.parse_table(table), *args, **kargv)

    def drop(self, *tables):
        tables = (self.parse_table(t) for t in tables)
        super().drop(*tables)

    def set_view(self):
        self.blog_id = None
        for v in self.to_list("SELECT name FROM sqlite_master WHERE type='view'"):
            self.drop(v)
        views={}
        for t, tb, blog in get_view(*self.tables.keys()):
            view = views.get(tb, "CREATE VIEW {0} AS".format(tb))
            views[tb]=view+("\nselect {1} blog, {0}.* from {0} union".format(t, blog))
        for view in views.values():
            view=view[:-6]+";"
            self.execute(view)

    def minimize(self):
        self.blog_id = None
        count_blog = ["select count(*) C from b{ID}_"+t for t in self.site_tables]
        count_blog = " union ".join(count_blog)
        count_blog = "select sum(C) from ("+count_blog+")"
        for r in self.select("select ID, name, url from blogs", row_factory=dict_factory):
            ct_blog = self.one(count_blog.format(**r))
            if ct_blog == 0:
                print("Blog {url} vacio será borrado".format(**r))
                self.rm_blog(r["ID"])

        ct_blog = self.one("select count(*) from blogs")
        if ct_blog==1:
            for v in self.to_list("SELECT name FROM sqlite_master WHERE type='view'"):
                self.drop(v)
            blog_id = self.one("select ID from blogs")
            prefix = "b%d_" % blog_id
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
