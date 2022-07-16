import json
import os


class DB:

    def __init__(self, path: str):
        self.path = path

    def __len__(self):
        return len(os.listdir(self.path))

    def __contains__(self, item):
        try:
            return item in os.listdir(self.path)
        except OSError:
            return False

    def __iter__(self):
        return iter(os.listdir(self.path))

    def __setitem__(self, key, item):
        try:
            with open(f"{self.path}/{key}", "w") as f:
                json.dump(item, f, indent=4)
        except OSError:
            os.makedirs(os.path.dirname(f"{self.path}/{key}"))
            with open(f"{self.path}/{key}", "w") as f:
                json.dump(item, f, indent=4)

    def __getitem__(self, key):
        try:
            with open(f"{self.path}/{key}", "r") as f:
                return json.load(f)
        except OSError:
            return {}

    def __delitem__(self, key):
        try:
            os.remove(f"{self.path}/{key}")
        except OSError:
            raise KeyError(f"File {key} not found")

    def keys(self):
        return os.listdir(self.path)

    def to_dict(self):
        dtr = {}
        for key in os.listdir(self.path):
            with open(f"{self.path}/{key}", "r") as f:
                dtr[key] = json.load(key)



class db:

    def __init__(self, user: str, key="Global_c"):
        self.db = DB(f"db/Users/{user}/Notes")
        self.key = f"{key}.json"

    def set_note(self, items:list, note):
        load = self.db[self.key]
        for item in items:
            load[item] = note
        self.db[self.key] = load

    def my_notes(self):
        load = self.db[self.key]
        if len(load): 
            for item, note in load.items():
                yield item, note
        else:
            raise KeyError

    def notenote(self, notes, new, exact=True):
        if not exact:
            def check(noted):
                for note in notes:
                    if note in noted:
                        return True
                return False
        else:
            def check(noted):
                for note in notes:
                    if note == noted:
                        return True
                return False
        load = self.db[self.key]
        for item, note in load.items():
            if check(note):
                load[item] = new
        self.db[self.key] = load
        
    def delnote(self, notes, exact=True):
        if not exact:
            def check(noted):
                for note in notes:
                    if note in noted:
                        return True
                return False
        else:
            def check(noted):
                for note in notes:
                    if note == noted:
                        return True
                return False
        load = self.db[self.key]
        for item, note in load.copy().items():
            if check(note):
                del load[item]
        self.db[self.key] = load

        
    def delitems(self, items, exact=True):
        if not exact:
            def check(item):
                for i in items:
                    if i.lower() in item.lower():
                        return True
                return False
        else:
            def check(item):
                for i in items:
                    if i.lower() == item.lower():
                        return True
                return False
        load = self.db[self.key]
        for item, note in load.copy().items():
            if check(item):
                del load[item]
                items.remove(item)
        self.db[self.key] = load
                

    def get_notes(self, notes, exact=False):
        print(notes)
        if not exact:
            def check(noted):
                for note in notes:
                    if note in noted:
                        return True
                return False
        else:
            def check(noted):
                for note in notes:
                    if note == noted:
                        return True
                return False
        load = self.db[self.key]
        for item, noted in load.items():
            if check(noted):
                print(item, ":", noted)
                yield item, noted

    def get_items(self, items, exact=False):
        print(items)
        if not exact:
            def check(item):
                for i in items:
                    if i.lower() in item.lower():
                        return True
                return False
        else:
            def check(item):
                for i in items:
                    if i.lower() == item.lower():
                        return True
                return False
        load = self.db[self.key]
        for item, note in load.items():
            if check(item):
                print(item)
                yield item, note

    def clean(self):
        del self.db[self.key]


    def sort_note(self, notes_sort, pos=None):
        load = self.db[self.key]

        #Searches for items with given notes
        l = {note:[] for note in notes_sort}
        for item, note in load.items():
            if note in l and item != pos:
                l[note].append(item)

        #Making a copy to know where items were
        loadc = load.copy()
                
        #Reinserting given ordered notes's items to the end
        for noted, listed in l.items():
            for i in listed:
                load[i] = load.pop(i)
                
        #Reinsering other items to restore order
        for item, note in loadc.items():
            
            #Actually reinserting items
            if not pos:
                #Ignore the notes that were already reinserted in prev loop
                if note not in notes_sort:
                    load[item] = load.pop(item)
                    
            #Finding where to start, if position of start is given
            elif item == pos:
                pos = None
                
        self.db[self.key] = load
                
                
    def sort_items(self, items_sort, findpos=False):
        load = self.db[self.key]
        
        #Making a copy to know where items were
        loadc = load.copy()

        #Reinserting given ordered items to the end
        for item in items_sort:
            load[item] = load.pop(item)

        #Reinsering other items to restore order
        for item, note in loadc.items():
            
            #Actually reinserting items
            if not findpos:
                #Ignore the items that were already reinserted in prev loop
                if item not in items_sort:
                    load[item] = load.pop(item)
                    
            #Finding where to start
            elif item == items_sort[0]:
                findpos = False
                
        self.db[self.key] = load

    def note_dict(self, itemnotes, replace=False):
        load = self.db[self.key]
        for item, note in itemnotes:
            if replace:
                load[item] = note
            else:
                if item not in load:
                    load[item] = note
                
        self.db[self.key] = load
        