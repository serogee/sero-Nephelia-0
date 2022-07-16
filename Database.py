import os
import json

class DB_dict(object):

    _control = dict()

    def __new__(cls, parent, key, value, autoupdate=True):
        ppath = parent.path
        if ppath.endswith(".json"):
            try:
                if key in cls._control[ppath]:
                    return cls._control[ppath][key]
            except KeyError:
                pass
        return super(DB_dict, cls).__new__(cls)

    def __init__(self, parent, key, value, autoupdate=True):
        ppath = parent.path
        if ppath.endswith(".json"):
            try:
                self._control[ppath][key] = self
            except KeyError:
                self._control[ppath] = {key: self}
        self.parent = parent
        self.autoupdate = autoupdate
        self.key = key
        self.value: dict = value

    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key, value):
        self.value.__setitem__(key, value)
        if self.autoupdate:
            self._update()

    def __delitem__(self, key):
        del self.value[key]
        if self.autoupdate:
            self.update()

    def __len__(self):
        return self.value.__len__()

    def __iter__(self):
        return self.value__iter__()
    
    def __contains__(self, key):
        return self.value.__contains__()

    def __str__(self):
        return self.key
        
    def __repr__(self):
        return f"<{type(self).__qualname__} parent: {self.parent}, key: {self.key}, cached: {self.cached}>"

    def pop(self, key):
        value = self.value.pop(key)
        if self.autoupdate:
            self._update()
        return value

    def pop_items(self, keys):
        for key in keys:
            try:
                yield self.value.pop(key)
            except KeyError:
                yield None
        if self.autoupdate:
            self._update()

    def update(self, update):
        self.value.__update__(update)
        if self.autoupdate:
            self._update()

    def copy(self):
        return self.value

    def items(self):
        return self.value.items()

    def dump(self, value):
        self.parent.__setitem__(self.key, value)
        self.value = value

    def _update(self):
        self.parent.__setitem__(self.key, self.value)
        
    def forget(self):
        del self._control[self.path]

class DB_json(object):

    _control = dict()
    
    def __new__(cls, path, cached=False):
        if path in cls._control:
            item = cls._control[path]
            if item.cached is cached:
                return item
            elif item.cached:
                return item
            elif cached:
                try:
                    with open(item.path, "r") as f:
                        item.data: dict = json.load(f)
                except OSError:
                    item.data = {}
                return item
        else:
            return super(DB_json, cls).__new__(cls)

    def __init__(self, path, cached=False):
        self._control[path] = self
        if cached:
            try:
                with open(path, "r") as f:
                    self.data: dict = json.load(f)
            except OSError:
                self.data = {}
        self.cached = cached
        self.path = path

    def __getitem__(self, key):
        if self.cached:
            value = self.data.__getitem__(key)
        else:
            try:
                with open(self.path, "r") as f:
                    value = json.load(f).__getitem__(key)
            except OSError:
                raise KeyError(f"Path {self.path} not found")
        if type(value) is dict:
            return DB_dict(self, key, value)
        return value

    def __setitem__(self, key, value):
        if self.cached:
            self.data.__setitem__(key, value)
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

    def __delitem__(self, key):
        if self.cached:
            self.data.__delitem__(key)
        try:
            with open(self.path, "r") as f:
                load = json.load(f)
                load.__delitem__(key)
            with open(self.path, "w") as f:
                json.dump(
                    load,
                    f,
                    indent=4
                )
            if load == {}:
                os.remove(self.path)
        except OSError:
            raise KeyError(f"Path {self.path} not found")

    def __contains__(self, key):
        if self.cached:
            return self.data.__contains__(key)
        with open(self.path, "r") as f:
            return json.load(f).__contains__(key)

    def __iter__(self):
        if self.cached:
            return self.data.__iter__()
        with open(self.path, "r") as f:
            return json.load(f).__iter__()

    def __len__(self):
        if self.cached:
            return self.cached.__len__()
        with open(self.path, "r") as f:
            return json.load(f).__len__()

    def __str__(self):
        return self.path
        
    def __repr__(self):
        return f"<{type(self).__qualname__} path: {self.path}, cached: {self.cached}>"

    def pop(self, key):
        if self.cached:
            load = self.data
            value = self.data.pop(key)
        else:
            with open(self.path, "r") as f:
                load = json.load(f)
                value = load.pop(key)
        with open(self.path, "w") as f:
            json.dump(
                load,
                f,
                indent=4
            )
        if load == {}:
            os.remove(self.path)
        if type(value) is dict:
            return DB_dict(self, key, value)
        return value
                
    def pop_items(self, keys):
        """Deletes keys from an iterable and yields their values"""
        if self.cached:
            load = self.data
        else:
            with open(self.path, "r") as f:
                load = json.load(f)
        for key in keys:
            try:
                value = load.pop(key)
                if type(value) is dict:
                    yield DB_dict(self, key, value)
                else:
                    yield value
            except KeyError:
                yield None
        with open(self.path, "w") as f:
            json.dump(
                load,
                f,
                indent=4
            )
        if load == {}:
            os.remove(self.path)
        if self.cached:
            self.data = load

    def get_items(self, keys):
        """Yields the values of keys in an iterable"""
        if self.cached:
            for key in keys:
                yield key, self.cached.__getitem__(key)
        else:
            with open(self.path, "r") as f:
                load: dict = json.load(f)
                for key in keys:
                    try:
                        value = load.__getitem__(key)
                        if type(value) is dict:
                            yield key, DB_dict(self, key, value)
                        else:
                            yield key, value
                    except KeyError:
                        yield key, None

    def update(self, items: dict):
        if self.cached:
            load = self.data
        else:
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
            self.data = load

    def items(self):
        if self.cached:
            return self.data.items()

    def copy(self):
        if self.cached:
            return self.data.copy()
        with open(self.path, "r") as f:
            return json.load(f)

    def dump(self, load):
        try:
            with open(self.path, "w") as f:
                json.dump(
                    load,
                    f,
                    indent=4
                )
        except OSError:
            os.makedirs(os.path.dirname(self.key))
            with open(self.path, "w") as f:
                json.dump(
                    load, 
                    f, 
                    indent=4
                )
        if self.cached:
            self.data = load

    def delete(self):
        os.remove(self.path)

    def forget(self):
        del self._control[self.path]

class DB(object):

    _control = dict()

    def __new__(cls, path, cached, cached_children=False):
        if path in cls._control:
            item = cls._control[path]
            if item.cached is cached:
                return item
            if item.cached:
                return item
            elif cached:
                item.cached = True
                item.data = {key: item for key, item in item.items()}
                return item
        else:
            return super(DB, cls).__new__(cls)
            

    def __init__(self, path, cached, cached_children=False):
        self.path = path
        self.cached_children = cached_children
        self.cached = cached
        if cached:
            self.data = {key: item for key, item in self.items()}
        self._control[path] = self
    
    def __getitem__(self, key):
        if self.cached:
            if key not in self.data: 
                self.data[key] = DB_json(f"{self.path}/{key}.json", self.cached_children)
            return self.data[key]
        return DB_json(f"{self.path}/{key}.json", self.cached_children)

    def __setitem__(self, key, value):
        while True:
            try:
                with open(f"{self.path}/{key}.json", "w") as f:
                    json.dump(
                        value,
                        f,
                        indent=4
                    )
                break
            except OSError:
                os.makedirs(os.path.dirname(f"{self.path}/{key}.json"))
        if self.cached and key not in self.data:
            self.data[key] = DB_json(f"{self.path}/{key}.json", self.cached_children)

    def __delitem__(self, key):
        try:
            if self.cached:
                del self.data[key]
            os.remove(f"{self.path}/{key}.json")
        except OSError:
            raise KeyError(f"File {key} not found")
    
    def __contains__(self, key):
        if self.cached:
            return key in self.data
        try:
            return key in os.listdir(self.path)
        except OSError:
            return False

    def __len__(self):
        if self.cached:
            return len(self.data)
        try:
            return len(os.listdir(self.path))
        except OSError:
            return 0

    def __iter__(self):
        if self.cached:
            return iter(self.data)
        for file in os.listdir(self.path):
            yield file[:-5]

    def __repr__(self):
        return f"<{type(self).__qualname__} path: {self.path}, cached: {self.cached}>"

    def keys(self):
        return [file[:-5] for file in os.listdir(self.path)]

    def items(self):
        for file in os.listdir(self.path):
            yield file[:-5], DB_json(f"{self.path}/{file}", self.cached_children)

    def raw_items(self):
        for file in os.listdir(self.path):
            with open(f"{self.path}/{file}", "w") as f:
                yield file[:-5], json.load(f)

    def forget(self):
        del self._control[self.path]