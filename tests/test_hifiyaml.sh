#!/bin/bash
# use the "yth" and "ythx" scripts to test the yamltools4jedi based on the hifiyaml backend
# yth = YamlTools_on_Hifiyaml
# ythx = yth_eXtended

rm -rf tmp
mkdir -p tmp

export YT_DEDENT=true
yth demo.yaml dump "cost function/observations/observers/0/obs space" > tmp/ctest1.yaml
export YT_DEDENT=fase
yth demo.yaml dump "cost function/observations/observers/0/obs space" > tmp/ctest2.yaml

yth demo.yaml drop "cost function/observations/observers" > tmp/no_obs.yaml

yth demo.yaml modify "output/filename" "filename: ana.nc"  > tmp/ana.yaml
yth demo.yaml modify "cost function/background error/components/0/covariance" bec_bump.yaml > tmp/becbump.yaml

export YT_DEDENT=true
export YT_SPLIT_LEVEL=1
yth demo.yaml split
mv split.demo.yaml tmp/split.default_1.0

export YT_DEDENT=fase
export YT_SPLIT_LEVEL=1
yth demo.yaml split
mv split.demo.yaml tmp/split.default_1.1

export YT_DEDENT=fase
export YT_SPLIT_LEVEL=2
yth demo.yaml split
mv split.demo.yaml tmp/split.default_2

export YT_LIST_INDENT=false
export YT_PLAIN_PACK=true
yth tmp/split.default_1.1 pack tmp/pack1.1.yaml
diff tmp/pack1.1.yaml demo.yaml
if (( $? == 0 )); then
  echo "GOOD: split and re-pack generate the identical YAML file"
else
  echo "FATAL: pack1.1.yaml is different from demo.yaml"
fi

export YT_USE_CONV_SAT_INFO=false
export YT_YTYPE="getkf"
export YT_GETKF_TYPE="solver"
ythx getkf.yaml > tmp/solver.yaml

export YT_USE_CONV_SAT_INFO=false
export YT_YTYPE="getkf"
export YT_GETKF_TYPE="post"
ythx getkf.yaml > tmp/post.yaml

export YT_USE_CONV_SAT_INFO=true
export YT_YTYPE="jedivar"
ythx demo.yaml > tmp/conv_sat_info.yaml

diff -rf tmp ref_hifiyaml 1>/dev/null 2>/dev/null
if (( $? == 0 )); then
  echo "test passed, identical results."
else
  echo "test failed, different results from 'diff -r tmp ref_hifiyaml'!"
fi
