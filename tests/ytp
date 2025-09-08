#!/usr/bin/env python
import os
import sys

# for yamltools tests, we use the packages in this repo
#   instead of the installed ones
here = os.path.dirname(__file__)
yamltools_path = os.path.join(here, "..")
if yamltools_path not in sys.path:
    sys.path.insert(0, yamltools_path)
import yamltools4jedi.backend_pyyaml as yt  # noqa: E402

args = sys.argv
nargs = len(args) - 1
if nargs < 2:
    print(f"{os.path.basename(args[0])} <file> <check|glance|traverse|dump|drop|set_value|append|split|pack> <querystr> [newblock_str]")
    exit()

dumper_str = os.getenv("YAMLTOOLS_DUMPER", "")   # empty string, or mydumper, etc
newblock_str, querystr = "", ""

yfile = args[1]
operator = args[2]
if nargs > 2:
    querystr = args[3]

if operator == "set_value":
    if nargs > 3:
        newblock_str = args[4]
    if not newblock_str:
        print("newblock_str cannot be empty for the set_value operator")
    if not querystr:
        print("querystr cannot be empty for the set_value operator")
elif operator == "pack":  # pack operator
    dirname = yfile
    if nargs > 2:
        fpath = args[3]
    if not dirname or not fpath:
        print("need dirname and fpath for the pack operator")

if operator != "pack":
    data = yt.load(yfile)

if operator == "check":
    yt.printd(f"check passed: {yfile} sucessfully loaded")

elif operator == "glance":
    subdata = yt.get(data, querystr)
    yt.glance(subdata)

elif operator == "traverse":
    subdata = yt.get(data, querystr)
    yt.traverse(subdata)

elif operator == "dump":
    subdata = yt.get(data, querystr)
    yt.dump(subdata, dumper=dumper_str)

elif operator == "drop":
    yt.drop(data, querystr)
    yt.dump(data, dumper=dumper_str)

elif operator == "set_value":
    newblock = yt.load(newblock_str)
    yt.set_value(data, querystr, newblock)
    yt.dump(data, dumper=dumper_str)

elif operator == "split":
    yt.split(yfile, dumper=dumper_str)

elif operator == "pack":
    yt.pack(dirname, fpath, dumper=dumper_str)

else:
    yt.printd(f"unknown operator: {operator}")
