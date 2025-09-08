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
import yamltools4jedi.backend_hifiyaml as yt  # noqa: E402

args = sys.argv
nargs = len(args) - 1
if nargs < 1:
    sys.stderr.write("op_info_getkf.py <file>\n")
    sys.exit(1)
yfile = args[1]
data = hy.load(yfile)

use_conv_sat_info = (os.getenv("YT_USE_CONV_SAT_INFO", "True").upper() != "FALSE")
GETKF_TYPE = os.getenv("YT_GETKF_TYPE", "observer")
ytype = os.getenv("YT_YTYPE", "jedivar")

# tweaks getkf.yaml from the observer mode to the solver mode
solver_driver_str = '''
driver:
  read HX from disk: true
  save posterior ensemble: true
  save prior mean: true
  save posterior mean: true
  do posterior observer: false
'''
if ytype == "getkf" and GETKF_TYPE == "solver":
    block = hy.text_to_yblock(solver_driver_str)
    hy.modify(data, "driver", block)

# keep/drop/passivate observations based on convifo/satinfo
if use_conv_sat_info:
    dcConvInfo = yt.load_convinfo()
    dcSatInfo = yt.load_satinfo()
    if not dcConvInfo:
        sys.stderr.write("INFO: no convinfo, or empty/corrupt convinfo\n")
    if not dcSatInfo:
        sys.stderr.write("INFO: no satinfo, or empty/corrupt satinfo\n")

# get the YAML head section
head_end, _ = hy.get_start_pos(data, "observations/observers")
output = data[0:head_end + 1]
# assemble observers
dcObs = yt.get_all_obs(data, shallow=True)
for name, observer in dcObs.items():
    sname = observer["sname"]
    tmp = data[observer["pos1"]:observer["pos2"]]  # a shallow copy when slicing
    if ytype == "getkf" and (GETKF_TYPE == "solver" or GETKF_TYPE == "post"):
        yt.getkf_observer_tweak(tmp, GETKF_TYPE)

    if use_conv_sat_info:
        if observer["is_sat_radiance"]:  # check against satinfo
            for sis, info in dcSatInfo.items():
                if sis == sname:
                    yt.update_sat_anchors(tmp, dcSatInfo)
                    output.extend(tmp)
                    break
        else:  # check against convinfo
            for iname, info in dcConvInfo.items():
                if iname == sname:
                    if info['iuse'] != "0":  # assimilate or monitor
                        if info['iuse'] == "-1":   # monitor, need to insert a passivate filter
                            for i in range(len(tmp)):
                                if "obs filters:" in tmp[i]:
                                    spaces = " " * (hy.strip_indentations(tmp[i])[0] + 2)  # default to 2 extra indentations
                                    passivate = [
                                        f"{spaces}- filter: Perform Action",
                                        f"{spaces}  action:",
                                        f"{spaces}    name: passivate",
                                        "",
                                    ]
                                    tmp[i + 1:i + 1] = passivate  # insert the passivate filter
                                    break
                        output.extend(tmp)
                    # ~~~~~~~
                    break

    else:  # skip convinfo/satinfo
        output.extend(tmp)

hy.dump(output)
