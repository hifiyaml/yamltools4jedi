import yaml
import os
import sys
import shutil
from datetime import datetime


# Custom Dumper class to tweak list formatting
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


# load YAML data from a string, a file or stdin(for pipe operations)
def load(astring):
    if astring == "pipe":
        yfile = sys.stdin
    elif os.path.exists(astring):  # a file name
        yfile = open(astring, 'r')
    else:  # a string
        yfile = astring
    return yaml.safe_load(yfile)


# print information for debugging purpose
def printd(*parms):
    msg = " ".join(str(p) for p in parms)
    sys.stderr.write(msg + "\n")


# tweak the dump format
def get_my_dumper():
    MyDumper.add_representer(list, MyDumper.represent_list)
    MyDumper.add_representer(datetime, MyDumper.represent_datetime)
    return MyDumper


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
                if key == "filter":
                    print(f"{' '*(n-1)*2}{key}: {value}")
                elif key == "obs space":
                    print(f"{' '*(n-1)*2}{key}: # name={value['name']}")
                else:
                    print(f"{' '*(n-1)*2}{key}:")

            traverse(value, n)
    elif isinstance(data, list):
        print(f"{' '*n*2}[a list of {len(data)} item(s)]")
        for i, element in enumerate(data):
            traverse(element, n, after_list=True, list_index=i)


# get the YAML block specified by querystr
#   the returned data is a reference to a sub-item of the original data
def get(data, querystr):
    if querystr:  # not empty
        query_list = querystr.strip("/").split("/")
        if isinstance(data, dict):
            data = data[query_list.pop(0)]
        elif isinstance(data, list):
            index = int(query_list.pop(0))
            if index < 0:
                index = 0
            elif index >= len(data):
                index = len(data)-1
            data = data[index]
        querystr = "/".join(query_list)
        return get(data, querystr)
    else:
        return data


# set (in-place) the value of a list element or a dict key referred to by a querystr to newblock
def set_value(data, querystr, newblock):
    query_list = querystr.strip("/").split("/")
    subdata = data
    last_pos = len(query_list) - 1
    for i, s in enumerate(query_list):
        if i < last_pos:
            if s.isdigit():  # a list
                subdata = subdata[int(s)]
            elif s in subdata.keys():  # a dict
                subdata = subdata[s]
            else:
                printd(f"{s}/ does not exist")
                sys.exit(1)

    s = query_list[last_pos]
    if s.isdigit():
        subdata[int(s)] = newblock
    else:
        subdata[s] = newblock


# dump a YAML block referred to by a querystr
def dump(data, querystr="", fpath="", dumper="", default_flow_style=False, sort_keys=False):
    data = get(data, querystr)
    if fpath == "":
        yfile = sys.stdout
    else:
        yfile = open(fpath, 'w')
    if dumper == "":
        dumper = yaml.Dumper
    else:
        dumper = get_my_dumper()
    yaml.dump(data, yfile, Dumper=dumper, default_flow_style=False, sort_keys=False)


# append a dict/list item, TODO
def append(data, query_list, edit):
    if query_list:  # not empty, desend to the target
        if isinstance(data, dict):
            key = query_list.pop(0)
            if not query_list:  # append new items to the dict
                data2 = load(edit)
                data.update(data2)
            else:
                append(data[key], query_list, edit)
        elif isinstance(data, list):
            index = int(query_list.pop(0))
            if index < 0:
                index = 0
            elif index >= len(data):
                index = len(data)-1
            if not query_list:  # append new items to the lsit
                data2 = load(edit)
                data.extend(data2)
            else:
                append(data[index], query_list, edit)


# drop a YAML block referred to by a querystr
def drop(data, querystr):
    query_list = querystr.strip("/").split("/")
    subdata = data
    last_pos = len(query_list) - 1
    for i, s in enumerate(query_list):
        if i < last_pos:
            if s.isdigit():  # a list
                subdata = subdata[int(s)]
            elif s in subdata.keys():  # a dict
                subdata = subdata[s]
            else:
                printd(f"{s}/ does not exist")
                sys.exit(1)

    s = query_list[last_pos]
    if s.isdigit():
        del subdata[int(s)]
    else:
        del subdata[s]


# write_out_filters
def write_out_filters(key, obs, obspath, dumper, filterlist):
    if f"obs {key}" in obs.keys():
        for i, flt in enumerate(obs[f"obs {key}"]):
            category = flt["filter"].replace(' ', '_')
            prefix = key.replace(' ', '')[:-1]
            fpath = f"{obspath}/{prefix}_{i:02}_{category}.yaml"
            filterlist.append(f"{prefix}_{i:02}_{category}.yaml")
            dump(flt, fpath=fpath, dumper=dumper)


# split JEDI super YAML files into individual observers and/or filters
def split(fpath, level=1, dirname=".", dumper=""):
    data = load(fpath)
    basename = os.path.basename(fpath)
    # dirname is the top level of the split results, default to current directory
    dirname.rsplit("/")  # remove trailing /  if any
    toppath = f"{dirname}/split.{basename}"

    # if the dir exists, find an available dir name to backup old files first
    if os.path.exists(toppath):
        knt = 1
        savedir = f'{toppath}_old{knt:04}'
        while os.path.exists(savedir):
            knt += 1
            savedir = f'{toppath}_old{knt:04}'
        shutil.move(toppath, savedir)
    os.makedirs(toppath, exist_ok=True)

    # deal with observers
    obslist = data["cost function"]["observations"]["observers"]
    with open(f"{toppath}/obslist.txt", 'w') as outfile:
        for obs in obslist:
            outfile.write(obs["obs space"]["name"] + "\n")

    if level == 1:  # split to individual observers (filters kept intact)
        for obs in obslist:
            fpath = f'{toppath}/{obs["obs space"]["name"]}.yaml'
            dump(obs, fpath=fpath, dumper=dumper)

    elif level == 2:  # split to individual observers and filters
        for obs in obslist:
            obspath = f'{toppath}/{obs["obs space"]["name"]}'
            os.makedirs(obspath, exist_ok=True)

            # write out filters
            filterlist = []
            write_out_filters("filters", obs, obspath, dumper, filterlist)
            write_out_filters("pre filters", obs, obspath, dumper, filterlist)
            write_out_filters("prior filters", obs, obspath, dumper, filterlist)
            write_out_filters("post filters", obs, obspath, dumper, filterlist)
            # write out filterlist.txt
            with open(f"{obspath}/filterlist.txt", 'w') as outfile:
                for item in filterlist:
                    outfile.write(f"{item}\n")

            if "obs filters" in obs.keys():
                obs["obs filters"] = []
            if "obs pre filters" in obs.keys():
                obs["obs pre filters"] = []
            if "obs prior filters" in obs.keys():
                obs["obs prior filters"] = []
            if "obs post filters" in obs.keys():
                obs["obs post filters"] = []
            fpath = f'{obspath}/obsmain.yaml'
            dump(obs, fpath=fpath, dumper=dumper)

    # write main.yaml
    data["cost function"]["observations"]["observers"] = []
    dump(data, fpath=f'{toppath}/main.yaml', dumper=dumper)


# pack individual observers, filters into one super YAML file
def pack(dirname, fpath, dumper=""):
    obslist = []
    with open(os.path.join(dirname, "obslist.txt"), 'r') as infile:
        for line in infile:
            if line.strip():
                obslist.append(line.strip())

    # check it is level1 or level2 split
    if os.path.isfile(os.path.join(dirname, f"{obslist[0]}.yaml")):
        level = 1
    elif os.path.isdir(os.path.join(dirname, f"{obslist[0]}")):
        level = 2
    else:
        print(f"Neither {obslist[0]}.yaml nor {obslist[0]}/ found")
        return

    data = load(os.path.join(dirname, "main.yaml"))
    if level == 1:
        observers = []
        for obsname in obslist:
            obs = load(os.path.join(dirname, f"{obsname}.yaml"))
            observers.append(obs)

    elif level == 2:
        observers = []
        for obsname in obslist:
            obs = load(os.path.join(dirname, f"{obsname}/obsmain.yaml"))

            filter_type = {
                "filter": "obs filters",
                "prefilter":  "obs pre filters",
                "priorfilter":  "obs prior filters",
                "postfilter":  "obs post filters",
            }
            # read filterlist
            filterlist = []
            with open(os.path.join(dirname, f"{obsname}/filterlist.txt"), 'r') as infile:
                for line in infile:
                    if line.strip():
                        filterlist.append(line.strip())
            # assemble individual filters
            for fltfile in filterlist:
                flt_block = load(os.path.join(dirname, f"{obsname}/{fltfile}"))
                prefix = fltfile.split("_")[0]
                obs[filter_type[prefix]].append(flt_block)
            # append obs to observers
            observers.append(obs)

    data["cost function"]["observations"]["observers"] = observers
    dump(data, fpath=fpath, dumper=dumper)
