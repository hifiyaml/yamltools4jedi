#!/bin/bash
# use the "ytp" script to test the yamltools4jedi based on the PyYAML backend
# ytp = YamlTools_on_Pyyaml

rm -rf tmp
mkdir -p tmp

ytp demo.yaml glance  > tmp/level1.txt
ytp demo.yaml glance "cost function" > tmp/level2.txt
ytp demo.yaml glance "cost function/observations" > tmp/level3.txt


ytp demo.yaml traverse "cost function/observations/observers/0/obs filters/0"  > tmp/filter0.txt


export YT_DUMPER="format1"
ytp demo.yaml dump "test" > tmp/ctest.yaml

ytp demo.yaml drop "cost function/observations" > tmp/no_obs.yaml

ytp demo.yaml set_value "output/filename" "ana.nc"  > tmp/ana.yaml
ytp demo.yaml set_value "variational/iterations/0" geometry.yaml  > tmp/new_geometry.yaml


export YT_DUMPER="format1"
export YT_SPLIT_LEVEL="1"
ytp demo.yaml split
mv split.demo.yaml tmp/split.format1


export YT_DUMPER=""
export YT_SPLIT_LEVEL="1"
ytp demo.yaml split
mv split.demo.yaml tmp/split.default


export YT_DUMPER="format1"
export YT_SPLIT_LEVEL="2"
ytp demo.yaml split
mv split.demo.yaml tmp/split.format1.lvl2


export YT_DUMPER=""
ytp demo.yaml dump > tmp/org.yaml
ytp tmp/split.default  pack  tmp/pack.yaml
diff tmp/org.yaml tmp/pack.yaml
if (( $? == 0 )); then
  echo "GOOD: split and re-pack generate the identical YAML file"
else
  echo "FATAL: pack.yaml is different from org.yaml"
fi


export YT_DUMPER="format1"
ytp demo.yaml dump > tmp/org2.yaml
ytp tmp/split.format1.lvl2  pack  tmp/pack2.yaml
diff tmp/org2.yaml tmp/pack2.yaml
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
