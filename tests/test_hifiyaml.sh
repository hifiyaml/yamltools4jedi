#!/bin/bash

rm -rf tmp
mkdir -p tmp

export YT_DEDENT=true
op_hifiyaml.py demo.yaml dump "cost function/observations/observers/0/obs space" > tmp/ctest1.yaml
export YT_DEDENT=fase
op_hifiyaml.py demo.yaml dump "cost function/observations/observers/0/obs space" > tmp/ctest2.yaml

op_hifiyaml.py demo.yaml drop "cost function/observations/observers" > tmp/no_obs.yaml

op_hifiyaml.py demo.yaml modify "output/filename" "filename: ana.nc"  > tmp/ana.yaml
op_hifiyaml.py demo.yaml modify "cost function/background error/components/0/covariance" bec_bump.yaml > tmp/becbump.yaml

export YT_DEDENT=true
export YT_SPLIT_LEVEL=1
op_hifiyaml.py demo.yaml split
mv split.demo.yaml tmp/split.default_1.0

export YT_DEDENT=fase
export YT_SPLIT_LEVEL=1
op_hifiyaml.py demo.yaml split
mv split.demo.yaml tmp/split.default_1.1

export YT_DEDENT=fase
export YT_SPLIT_LEVEL=2
op_hifiyaml.py demo.yaml split
mv split.demo.yaml tmp/split.default_2

export YT_LIST_INDENT=false
export YT_PLAIN_PACK=true
op_hifiyaml.py tmp/split.default_1.1 pack tmp/pack1.1.yaml
diff tmp/pack1.1.yaml demo.yaml
if (( $? == 0 )); then
  echo "GOOD: split and re-pack generate the identical YAML file"
else
  echo "FATAL: pack1.1.yaml is different from demo.yaml"
fi




diff -rf tmp ref_hifiyaml 1>/dev/null 2>/dev/null
if (( $? == 0 )); then
  echo "test passed, identical results."
else
  echo "test failed, different results from 'diff -r tmp ref_hifiyaml'!"
fi
