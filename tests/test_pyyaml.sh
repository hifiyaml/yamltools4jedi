#!/bin/bash

rm -rf tmp
mkdir -p tmp

op_pyyaml.py demo.yaml glance  > tmp/level1.txt
op_pyyaml.py demo.yaml glance "cost function" > tmp/level2.txt
op_pyyaml.py demo.yaml glance "cost function/observations" > tmp/level3.txt


op_pyyaml.py demo.yaml traverse "cost function/observations/observers/0/obs filters/0"  > tmp/filter0.txt


op_pyyaml.py demo.yaml dump "test" > tmp/ctest.yaml

op_pyyaml.py demo.yaml drop "cost function/observations" > tmp/no_obs.yaml

op_pyyaml.py demo.yaml set_value "output/filename" "ana.nc"  > tmp/ana.yaml
op_pyyaml.py demo.yaml set_value "variational/iterations/0" geometry.yaml  > tmp/new_geometry.yaml


export YAMLTOOLS_DUMPER="mydumper"
op_pyyaml.py demo.yaml split
mv split.demo.yaml tmp/split.mydumper


export YAMLTOOLS_DUMPER=""
op_pyyaml.py demo.yaml split
mv split.demo.yaml tmp/split.default


op_pyyaml.py demo.yaml dump > tmp/org.yaml
op_pyyaml.py tmp/split.default pack tmp/pack.yaml
diff tmp/org.yaml tmp/pack.yaml
if (( $? == 0 )); then
  echo "GOOD: split and re-pack generate the identical YAML file"
else
  echo "FATAL: pack.yaml is different from org.yaml"
fi

diff -rf tmp ref_pyyaml 1>/dev/null 2>/dev/null
if (( $? == 0 )); then
  echo "test passed, identical results."
else
  echo "test failed, different results from 'diff -r tmp ref_pyyaml'!"
fi
