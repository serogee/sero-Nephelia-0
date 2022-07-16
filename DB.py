import os
import json

mypath = os.getcwd()

class DB_skeleton(object):

    _control = dict()
    def __getitem__(self, key): pass
    def __setitem__(self, key, value): pass
    def __delitem__(self, key): pass
    def __len__(self): pass
    def __iter__(self): pass
    def __contains__(self): pass
    def __repr__(self): pass
    def __hash__(self): pass
    def __eq__(self): pass
    def __ne__(self): pass
    def update(self, items): pass
    def items(self): pass
    def values(self): pass
    def keys(self): pass
    def load(Self): pass
    def dump(self, value): pass
    def forget(self): pass

class DB_dict(DB_skeleton):

    def __init__(self, parent, key, value, infile_autosave=True):
        pass

class DB_json(DB_skeleton):

    #__setitem__: if key not in parent.data: parent.data[key] = self
    #__delitem__: if key in parent.data: del parent.data[key]

    def __init__(self, path, key, parent=None, cached_json=False, **kwargs):
        self.path = path
        self.key = key
        self.parent = parent
        if cached_json:
            self.preload()
        else:
            self.cached = False
        self.kwargs = kwargs

    def preload(self):
        self.cached = True
        try:
            with open(path, "r") as f:
                load = json.load(f)
            temp = {}
            for key, value in load:
                if type(value) is dict: temp[key] = DB_dict(parent=self, key=key, value=value)
                else: temp[key] = value
            self.data = temp
        except OSError:
            self.data = {}

    def unload(self):
        self.cached = False
        del self.data

    def __getitem__(self, key):
        if self.cached:
            value = self.data[key]
        else:
            try:
                with open(self.path, "r") as f:
                    value = json.load(f)[key]
            except OSError:
                raise KeyError(f"Path {self.path} not found")
        if type(value) is dict:
            return DB_dict(self, key, value) ####
        return value

    def __setitem__(self, item, value):
        if self.cached:
            self.data[item] = value
        while True:
            try:
                with open(self.path, "r") as f:
                    load = json.load(f)
                    load.__setitem__(key, value)
                with open(self.path, "w") as f:
                    json.dump(
                        load, 
                        f, 
                        indent=4
                    )
                break
            except OSError:
                os.makedirs(os.path.dirname(self.path))
        if self.parent.cached:
            if self.key not in self.parent.data:
                self.parent.data[self.key] = self

    def __delitem__(self, key):
        if self.cached:
            del self.data[key]
        try:
            with open(self.path, "r") as f:
                load = json.load(f)
                del load[key]
            with open(self.path, "w") as f:
                json.dump(
                    load,
                    f,
                    indent=4
                )
            if not load:
                del self.parent[self.key]
        except OSError:
            raise KeyError(f"Path {self.path} not found")
        
    def __contains__(self, key):
        if self.cached:
            return key in self.data
        with open(self.path, "r") as f:
            return key in json.load(f)

    def __iter__(self, key):
        if self.cached:
            iter(self.data)
        with open(self.path, "r") as f:
            return iter(json.load(f))
        

class DB_dirs(DB_skeleton):

    def __init__(self, path, key, parent=None, cached_dir=False, **kwargs):
        self.path = path
        self.key = key
        if cached_dir:
            self.data = {}
        if "/" in key:
            dirs = key.split("/", 1)
            key = dirs.pop(0)
            self.__getitem__(dirs.join("/"))
        self.cached = cached_dir
        self.kwargs = kwargs
        self.parent = parent

    def __getitem__(self, key):
        if self.cached:
            if key in self.data: return self.data[key]
        if key.endswith(".json"):
            return DB_json(f"{self.path}/{key}", key, self, **self.kwargs)
        return DB_dirs(f"{self.path}/{key}", key, self, self.cached, **self.kwargs)

    def __setitem__(self, key, value):
        if key.endswith(".json")
            while True:
                try:
                    with open(f"{self.path}/{key}", "w") as f:
                        json.dump(
                            value,
                            f,
                            indent=4
                        )
                    break
                except OSError:
                    os.makedirs(os.path.dirname(f"{self.path}/{key}.json"))
            if self.cached and key not in self.data:
                self.data[key] = DB_json(f"{self.path}/{key}.json")
        else:
            for k, v in value:
                

class DB:

    tree = dict()

    cache_info = dict()

    @classmethod
    def cache(cls, cached_dir=None, cached_json=None, infile_autosave=None):
        if cached_dir is bool:
            cls.cache_info["cached_dir"] = cached_dir
        if cached_json is bool:
            cls.cache_info["cached_json"] = cached_json
        if infile_autosave is bool:
            cls.cache_info["infile_autosave"] = infile_autosave

    @classmethod
    def access(cls, path):
        dirs = path.split("/", 1)
        root = dirs.pop(0)
        if root not in cls.tree:
            cls.tree[root] = DB_dirs(root, "/".join(dirs), **cls.cache_info)
        DB_object = cls.tree[root]
        for dir in dirs:
            DB_object = DB_object[dir]
        return DB_object