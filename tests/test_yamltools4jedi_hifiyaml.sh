#!/bin/bash
# use the "yj" and "yjx" scripts to test the yamltools4jedi based on the hifiyaml backend
# yj = YamlTools (on hifiyaml)
# yjx = yj_eXtended

rm -rf tmp
mkdir -p tmp

export YJ_DEDENT=true
./yj dump demo.yaml "cost function/observations/observers/0/obs space" > tmp/ctest1.yaml
export YJ_DEDENT=fase
./yj dump demo.yaml "cost function/observations/observers/0/obs space" > tmp/ctest2.yaml

./yj drop demo.yaml "cost function/observations/observers" > tmp/no_obs.yaml

./yj modify demo.yaml "output/filename" "filename: ana.nc"  > tmp/ana.yaml
./yj modify demo.yaml "cost function/background error/components/0/covariance" bec_bump.yaml > tmp/becbump.yaml

export YJ_DEDENT=true
export YJ_SPLIT_LEVEL=1
./yj split demo.yaml
mv split1.demo.yaml tmp/split.default_1.0

export YJ_DEDENT=fase
export YJ_SPLIT_LEVEL=1
./yj split demo.yaml
mv split1.demo.yaml tmp/split.default_1.1

export YJ_DEDENT=fase
export YJ_SPLIT_LEVEL=2
./yj split demo.yaml
mv split2.demo.yaml tmp/split.default_2

export YJ_LIST_INDENT=false
export YJ_PLAIN_PACK=true
./yj pack tmp/split.default_1.1/  tmp/pack1.1.yaml
diff tmp/pack1.1.yaml demo.yaml
if (( $? == 0 )); then
  echo "GOOD: split and re-pack generate the identical YAML file"
else
  echo "FATAL: pack1.1.yaml is different from demo.yaml"
fi

export YJ_DEDENT=fase
export YJ_PLAIN_PACK=true
./yj pack tmp/split.default_2  tmp/pack2.yaml
diff tmp/pack2.yaml demo.yaml
if (( $? == 0 )); then
  echo "GOOD: split and re-pack generate the identical YAML file"
else
  echo "FATAL: pack2.yaml is different from demo.yaml"
fi

export YJ_USE_CONV_SAT_INFO=false
export YJ_YTYPE="getkf"
export YJ_GETKF_TYPE="solver"
./yjx getkf.yaml > tmp/solver.yaml

export YJ_USE_CONV_SAT_INFO=false
export YJ_YTYPE="getkf"
export YJ_GETKF_TYPE="post"
./yjx getkf.yaml > tmp/post.yaml

export YJ_USE_CONV_SAT_INFO=true
export YJ_YTYPE="jedivar"
./yjx demo.yaml > tmp/conv_sat_info.yaml

diff -rf tmp ref_hifiyaml 1>/dev/null 2>/dev/null
if (( $? == 0 )); then
  echo "test passed, identical results."
else
  echo "test failed, different results from 'diff -r tmp ref_hifiyaml'!"
fi
