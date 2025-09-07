#!/usr/bin/env python
import os
import sys
import yaml

# for yamltools tests, we use the packages in this repo
#   instead of the installed ones
here = os.path.dirname(__file__)
yamltools_path = os.path.join(here, "..")
if yamltools_path not in sys.path:
    sys.path.insert(0, yamltools_path)
import yamltools4jedi.backend_pyyaml as ytpy  # noqa: E402

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
    data = ytpy.load(yfile)

if operator == "check":
    ytpy.printd(f"check passed: {yfile} sucessfully loaded")

elif operator == "glance":
    subdata = ytpy.get(data, querystr)
    ytpy.glance(subdata)

elif operator == "traverse":
    subdata = ytpy.get(data, querystr)
    ytpy.traverse(subdata)

elif operator == "dump":
    subdata = ytpy.get(data, querystr)
    ytpy.dump(subdata, dumper=dumper_str)

elif operator == "drop":
    ytpy.drop(data, querystr)
    ytpy.dump(data, dumper=dumper_str)

elif operator == "set_value":
    newblock = ytpy.load(newblock_str)
    ytpy.set_value(data, querystr, newblock)
    ytpy.dump(data, dumper=dumper_str)

elif operator == "split":
    ytpy.split(yfile, dumper=dumper_str)

elif operator == "pack":
    ytpy.pack(dirname, fpath, dumper=dumper_str)

else:
    ytpy.printd(f"unknown operator: {operator}")
