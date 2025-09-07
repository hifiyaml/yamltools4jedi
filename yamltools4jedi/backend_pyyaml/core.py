import yaml
import sys
from datetime import datetime


# Custom Dumper class to modify list formatting
class MyDumper(yaml.Dumper):
    def represent_datetime(self, data):
        return self.represent_scalar('tag:yaml.org,2002:timestamp', data.strftime('%Y-%m-%dT%H:%M:%SZ'))

    def represent_list(self, data):
        # Check if the list contains only simple literals (strings, numbers, booleans)
        if all(isinstance(item, (str, int, float, bool)) for item in data):
            # Use compact flow style ([])
            return self.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)
        else:
            # Use block style (-)
            return self.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=False)


# load YAML data from a file or stdin(for pipe operations)
def load(fname):
    if fname == "pipe":
        yfile = sys.stdin
    else:
        yfile = open(fname, 'r')
    return yaml.safe_load(yfile)


# glance the YAML data with "max_depth=1"
def glance(data):
    if isinstance(data, dict):
        for key in data.keys():
            print(f"{key}:")
    elif isinstance(data, list):
        print(f'[a list of {len(data)} item(s)]')
    else:
        print(data)


# traverse the yaml data until reaching leaves
def traverse(data, n=None, after_list=False, list_index=None):
    if n is None:
        n = 0
    if isinstance(data, dict):
        n += 1
        if after_list:
            n += 1
        for i, (key, value) in enumerate(data.items()):
            if after_list and i == 0:
                if key == "filter":
                    print(f"{' '*(n-2)*2}- {key}: {value}  #{list_index}")
                elif key == "obs space":
                    print(f"{' '*(n-2)*2}- {key}:  #{list_index}, name={value['name']}")
                else:
                    print(f"{' '*(n-2)*2}- {key}:  #{list_index}")
            elif after_list and i > 0:
                print(f"{' '*(n-1)*2}{key}:")
            else:
                print(f"{' '*(n-1)*2}{key}:")
            traverse(value, n)
    elif isinstance(data, list):
        print(f"{' '*n*2}[a list of {len(data)} item(s)]")
        for i, element in enumerate(data):
            traverse(element, n, after_list=True, list_index=i)


# get the value at the hirearchy query string level
def getFinalValue(data, keytree):
    if keytree:  # not empty
        if isinstance(data, dict):
            data = data[keytree.pop(0)]
        elif isinstance(data, list):
            index = int(keytree.pop(0))
            if index < 0:
                index = 0
            elif index >= len(data):
                index = len(data)-1
            data = data[index]
        return getFinalValue(data, keytree)
    else:
        return data


# edit the value referred to by a querystr
def editValue(data, keytree, edit, prevKey=""):
    if keytree:  # not empty, desend to the target
        if isinstance(data, dict):
            key = keytree.pop(0)
            data[key] = editValue(data[key], keytree, edit, prevKey=key)
        elif isinstance(data, list):
            index = int(keytree.pop(0))
            if index < 0:
                index = 0
            elif index >= len(data):
                index = len(data)-1
            data[index] = editValue(data[index], keytree, edit)
        return data
    else:  # empty, modify the target accordingly
        if isinstance(data, dict):
            data2 = load(edit)
            if prevKey in data2:
                return data2[prevKey]
            else:
                # print(f'** No "{prevKey}" key in {edit} and no edits made **', sys.stderr)
                return data
        elif isinstance(data, list):
            return load(edit)
        elif isinstance(data, bool):  # bool is a subclass of int, so we should check bool first
            if edit.lower() == 'true':
                return True
            elif edit.lower() == 'false':
                return False
        elif isinstance(data, int):
            return int(edit)
        else:
            return edit


# append a dict/list item
def append(data, keytree, edit):
    if keytree:  # not empty, desend to the target
        if isinstance(data, dict):
            key = keytree.pop(0)
            if not keytree:  # append new items to the dict
                data2 = load(edit)
                data.update(data2)
            else:
                append(data[key], keytree, edit)
        elif isinstance(data, list):
            index = int(keytree.pop(0))
            if index < 0:
                index = 0
            elif index >= len(data):
                index = len(data)-1
            if not keytree:  # append new items to the lsit
                data2 = load(edit)
                data.extend(data2)
            else:
                append(data[index], keytree, edit)


# delete a dict/list item
def deleteItem(data, keytree):
    if keytree:  # not empty, desend to the target
        if isinstance(data, dict):
            key = keytree.pop(0)
            if not keytree:  # delete the key
                data.pop(key, None)
            else:
                deleteItem(data[key], keytree)
        elif isinstance(data, list):
            index = int(keytree.pop(0))
            if not keytree:  # delete the item
                data.pop(index)
            else:
                deleteItem(data[index], keytree, edit)


# tweak the dump format
def set_new_dumper():
    MyDumper.add_representer(list, MyDumper.represent_list)
    MyDumper.add_representer(datetime, MyDumper.represent_datetime)
