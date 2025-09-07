#!/usr/bin/env python
import os
import sys
import hifiyaml as hy

# for yamltools tests, we use the packages in this repo
#   instead of the installed ones
here = os.path.dirname(__file__)
yamltools_path = os.path.join(here, "..")
if yamltools_path not in sys.path:
    sys.path.insert(0, yamltools_path)
import yamltools4jedi.backend_hifyaml as yt  # noqa: E402

args = sys.argv
nargs = len(args) - 1
if nargs < 2:
    print(f"{os.path.basename(args[0])} <file> <dump|drop|modify|split|pack> <querystr> [newblock_str]")
    exit()

dedent = os.getenv("YAMLTOOLS_DEDENT", "False").upper() == "TRUE"
split_level = int(os.getenv("YAMLTOOLS_SPLIT_LEVEL", "1"))
clean_extra_indentations = os.getenv("CLEAN_EXTRA_INDENTATIONS", "False").upper() == "TRUE"
listIndent = os.getenv("LIST_INDENT", "False").upper() == "TRUE"
plainpack = os.getenv("PLAINPACK", "False").upper() == "TRUE"

newblock_str, querystr = "", ""

yfile = args[1]
operator = args[2]
if nargs > 2:
    querystr = args[3]

if operator == "modify":
    if nargs > 3:
        newblock_str = args[4]
    if not newblock_str:
        print("newblock_str cannot be empty for the modify operator")
    if not querystr:
        print("querystr cannot be empty for the modify operator")
elif operator == "pack":  # pack operator
    dirname = yfile
    if nargs > 2:
        fpath = args[3]
    if not dirname or not fpath:
        print("need dirname and fpath for the pack operator")

if operator != "pack":
    data = hy.load(yfile)

if operator == "dump":
    hy.dump(data, querystr, do_dedent=dedent)

elif operator == "drop":
    hy.drop(data, querystr)
    hy.dump(data, do_dedent=dedent)

elif operator == "modify":
    newblock = hy.load(newblock_str)
    hy.modify(data, querystr, newblock)
    hy.dump(data, do_dedent=dedent)

elif operator == "split":
    yt.split(yfile, level=split_level, clean_extra_indentations=clean_extra_indentations)

elif operator == "pack":
    yt.pack(dirname, fpath, listIndent=listIndent, plainpack=plainpack)

else:
    hy.printd(f"unknown operator: {operator}")
