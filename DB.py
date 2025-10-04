import os
import json
import shutil

mypath = os.getcwd()

class DB_skeleton(object):

    _control = dict()
    def __getitem__(self, key): pass
    def __setitem__(self, key, value): pass
    def __delitem__(self, key): pass
    def __len__(self): pass
    def __iter__(self): pass
    def __contains__(self): pass
    def __repr__(self): pass #
    def __hash__(self): pass
    def __eq__(self): pass
    def __ne__(self): pass
    def update(self, items): pass
    def items(self): pass #
    def values(self): pass #
    def keys(self): pass
    def load(self): pass 
    def dump(self, value): pass 

class DB_dict(DB_skeleton):

    def __init__(self, parent, key):
        self.parent = parent
        self.key = key

    def _value(self):
        return self.parent._getitem(self.key)

    def _getitem(self, key):
        return self.value()[key]

    def update(self, items):
        load = self.value()
        load.update(items)
        self.parent[self.key] = load

    def load(self):
        return self._value()

    def dump(self, content):
        self.parent[self.key] = content

    def __getitem__(self, key):
        value = self.value()[key]
        if type(value) is dict:
            return DB_dict(self, key)

    def __setitem__(self, key, value):
        load = self._value()
        load[key] = value
        self.parent[self.key] = load

    def __delitem__(self, key):
        load = self._value()
        del load[key]
        if not load:
            del self.parent[self.key]
        else:
            self.parent[self.key] = load
            
    def __contains__(self, key):
        return key in self.value()

    def __iter__(self, key):
        return iter(self.value())

    def __len__(self):
        return len(self._value())

    def __eq__(self, other):
        return self.key == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.key)

class DB_json(DB_skeleton):

    def __init__(self, path, key, parent, cached_json=False, autosave_mutable_items=False, autoclean=True):
        self.path = path
        self.key= key
        self.parent = parent
        if cached_json:
            self.preload()
        else:
            self.cached = False
        self.autosave = autosave_mutable_items
            
    def _getitem(self, key):
        if self.cached:
            return self.data[key]
        else:
            try:
                with open(self.path, "r") as f:
                    return json.load(f)[key]
            except OSError:
                raise KeyError(f"Path {self.path} not found")

    def update(self, items):
        with open(self.path, "r") as f:
            load = json.load(f)
        load.update(items)
        with open(self.path, "w") as f:
            json.dump(
                load,
                f,
                indent=4
            )
        if self.cached:
            self.preload()

    def preload(self):
        self.cached = True
        try:
            with open(self.path, "r") as f:
                self.data = json.load(f)
        except OSError:
            self.data = {}

    def forget(self):
        self.cached = False
        del self.data

    def load(self):
        with open(self.path, "r") as f:
            return json.load(f)

    def dump(self, content):
        try:
            with open(self.path, "w") as f:
                json.dump(
                    content,
                    f,
                    indent=4
                )
            if self.cached:
                self.data = content
        except OSError:
            os.makedirs(os.path.dirname(self.path))
            with open(self.path, "w") as f:
                json.dump(
                    content,
                    f,
                    indent=4
                )
            if self.cached:
                self.data = content
            if self.parent.cached:
                if self.key not in self.parent.data:
                    self.parent.data[self.key] = self
            
    def delete(self):
        os.remove(self.path)

    def __getitem__(self, key):
        if self.cached:
            value = self.data[key]
        else:
            try:
                with open(self.path, "r") as f:
                    value = json.load(f)[key]
            except OSError:
                raise KeyError(f"Path {self.path} not found")
        if self.autosave:
            if type(value) is dict:
                return DB_dict(self, key) ####
        return value

    def __setitem__(self, key, value):
        if self.cached:
            self.data[key] = value
        while True:
            try:
                with open(self.path, "r") as f:
                    load = json.load(f)
                    load[key] = value
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
            if not load and self.autoclean:
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

    def __len__(self):
        if self.cached:
            return len(self.data)
        with open(self.path, "r") as f:
            return len(json.load(f))

    def __eq__(self, other):
        return self.key == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.key)

class DB_dirs(DB_skeleton):

    def __init__(self, path, key, parent=None, cached_dir=False, autoclean=True, **kwargs):
        self.path = path
        self.key = key
        self.parent = parent
        self.autoclean = autoclean
        self.kwargs = kwargs
        if cached_dir: self.preload()
        else: self.cached = cached_dir

    def preload(self):
        children = os.listdir(self.path)
        temp = dict()
        if self.cached:
            for item in children:
                if item in self.data:
                    continue
                elif item.endswith(".json"):
                    temp[item] = DB_json(f"{self.path}/{item}", item, self, autoclean=self.autoclean, **self.kwargs)
                else:
                    temp[item] = DB_dirs(f"{self.path}/{item}", item, self, cached_dir=self.cached, autoclean=self.autoclean, **self.kwargs)
                    
        else:
            for item in children:
                if item.endswith(".json"):
                    temp[item] = DB_json(f"{self.path}/{item}", item, self, autoclean=self.autoclean, **self.kwargs)
                else:
                    temp[item] = DB_dirs(f"{self.path}/{item}", item, self, cached_dir=self.cached, autoclean=self.autoclean, **self.kwargs)
            self.cached = True
        self.data = temp

    def forget(self):
        self.cached = False
        del self.data

    def delete(self):
        if self.parent: del self.parent[self.key]
        else: os.remove(self.path)

    def __getitem__(self, key):
        if self.cached and key in self.data:
            return self.data[key]
        if key.endswith(".json"):
            return DB_json(f"{self.path}/{key}", key, self, autoclean=self.autoclean, **self.kwargs)
        return DB_dirs(f"{self.path}/{key}", key, self, cached_dir=self.cached, autoclean=self.autoclean, **self.kwargs)

    def __setitem__(self, key, value): #Might need an update for setting dir keys as well
        if self.cached:
            if key in self.data: self.data[key].dump(value)
            elif key.endswith(".json"):
                database = DB_json(f"{self.path}/{key}", key, self, autoclean=self.autoclean, **self.kwargs)
                database.dump(value)
                self.data[key] = database
            else: raise TypeError(f"Couldn't dump value to non-json directory {self.path}/{key}") 
        else:
            if key.endswith(".json"):
                with open(f"{self.path}/{key}", "w") as f:
                    json.dump(
                        value,
                        f,
                        indent=4
                    )
            else: raise TypeError(f"Couldn't dump value to non-json directory {self.path}/{key}")

    def __delitem__(self, key):
        if self.cached:
            del self.data[key]
        path = f"{self.path}/{key}"
        try: os.remove(path)
        except:
            shutil.rmtree(path)
        if self.autoclean:
            if not self.__len__():
                self.delete()
        
    def __contains__(self, key):
        if self.cached:
            return key in self.data
        return key in os.listdir(self.path)

    def __iter__(self, key):
        if self.cached:
            iter(self.data)
        return iter(os.listdir(self.path))

    def __len__(self):
        if self.cached:
            return len(self.data)
        return len(os.listdir(self.path))

    def __eq__(self, other):
        return self.key == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.key)

            

class DB:

    tree = dict()

    cache_info = dict()

    @classmethod
    def cache(cls, cached_dir=None, cached_json=None, autosave_mutable_items=None, autoclean=None):
        if type(cached_dir) is bool:
            cls.cache_info["cached_dir"] = cached_dir
        if type(cached_json) is bool:
            cls.cache_info["cached_json"] = cached_json
        if type(autosave_mutable_items) is bool:
            cls.cache_info["autosave_mutable_items"] = autosave_mutable_items
        if type(autoclean) is bool:
            cls.cache_info["autoclean"] = autoclean

    @classmethod
    def access(cls, path):
        dirs = path.split("/", 1)
        root = dirs.pop(0)
        if root not in cls.tree:
            cls.tree[root] = DB_dirs(root, root, **cls.cache_info)
        DB_object = cls.tree[root]
        for dir in dirs:
            DB_object = DB_object[dir]
        return DB_object