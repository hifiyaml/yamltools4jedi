"""Pytest-based tests for yamltools4jedi (hifiyaml backend)."""
import os
import sys
import copy
import filecmp

import pytest

# Use packages from the repo
here = os.path.dirname(__file__)
yamltools_path = os.path.join(here, "..")
if yamltools_path not in sys.path:
    sys.path.insert(0, yamltools_path)

import hifiyaml as hy  # noqa: E402
import yamltools4jedi.backend_hifiyaml as yj  # noqa: E402


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def demo_data():
    return hy.load(os.path.join(here, "demo.yaml"))


@pytest.fixture
def getkf_data():
    return hy.load(os.path.join(here, "getkf.yaml"))


# ============================================================
# Tests: dump / get
# ============================================================

class TestDump:
    def test_dump_dedent(self, demo_data):
        """Dump with dedent should match ref/ctest1.yaml."""
        block = hy.get(demo_data, "cost function/observations/observers/0/obs space", do_dedent=True)
        ref_path = os.path.join(here, "ref_hifiyaml", "ctest1.yaml")
        with open(ref_path, 'r') as f:
            ref_lines = [line.rstrip('\n') for line in f.readlines()]
        assert block == ref_lines

    def test_dump_no_dedent(self, demo_data):
        """Dump without dedent should match ref/ctest2.yaml."""
        block = hy.get(demo_data, "cost function/observations/observers/0/obs space", do_dedent=False)
        ref_path = os.path.join(here, "ref_hifiyaml", "ctest2.yaml")
        with open(ref_path, 'r') as f:
            ref_lines = [line.rstrip('\n') for line in f.readlines()]
        assert block == ref_lines


# ============================================================
# Tests: drop
# ============================================================

class TestDrop:
    def test_drop_observers(self, demo_data):
        """Drop observers should match ref/no_obs.yaml."""
        data = copy.copy(demo_data)
        hy.drop(data, "cost function/observations/observers")
        ref_path = os.path.join(here, "ref_hifiyaml", "no_obs.yaml")
        with open(ref_path, 'r') as f:
            ref_lines = [line.rstrip('\n') for line in f.readlines()]
        assert data == ref_lines


# ============================================================
# Tests: modify
# ============================================================

class TestModify:
    def test_modify_single_value(self, demo_data):
        """Modify a single value should match ref/ana.yaml."""
        data = copy.copy(demo_data)
        hy.modify(data, "output/filename", "filename: ana.nc")
        ref_path = os.path.join(here, "ref_hifiyaml", "ana.yaml")
        with open(ref_path, 'r') as f:
            ref_lines = [line.rstrip('\n') for line in f.readlines()]
        assert data == ref_lines

    def test_modify_with_file(self, demo_data):
        """Modify with a block from file should match ref/becbump.yaml."""
        data = copy.copy(demo_data)
        newblock = hy.load(os.path.join(here, "bec_bump.yaml"))
        hy.modify(data, "cost function/background error/components/0/covariance", newblock)
        ref_path = os.path.join(here, "ref_hifiyaml", "becbump.yaml")
        with open(ref_path, 'r') as f:
            ref_lines = [line.rstrip('\n') for line in f.readlines()]
        assert data == ref_lines


# ============================================================
# Tests: get_all_obs
# ============================================================

class TestGetAllObs:
    def test_finds_all_observers(self, demo_data):
        """Should find all observers in demo.yaml."""
        dcObs = yj.get_all_obs(demo_data)
        assert len(dcObs) == 3
        names = list(dcObs.keys())
        assert "adpsfc_t181" in names[0]

    def test_shallow_mode(self, demo_data):
        """Shallow mode should not populate block."""
        dcObs = yj.get_all_obs(demo_data, shallow=True)
        for name, obs in dcObs.items():
            assert obs["block"] == []

    def test_deep_mode_has_blocks(self, demo_data):
        """Deep mode should populate block and filters."""
        dcObs = yj.get_all_obs(demo_data, shallow=False)
        for name, obs in dcObs.items():
            assert len(obs["block"]) > 0

    def test_handles_comment_before_name(self):
        """get_all_obs should handle comments between '- obs space:' and 'name:'."""
        yaml_text = """\
observers:
  - obs space:
      # this is a comment
      name: test_observer
      type: H5File
"""
        data = hy.text_to_yblock(yaml_text)
        dcObs = yj.get_all_obs(data)
        assert "test_observer" in dcObs


# ============================================================
# Tests: split and pack (round-trip)
# ============================================================

class TestSplitPack:
    def test_split_level1_pack_roundtrip(self, tmp_path):
        """Split level 1 (no dedent) then pack should reproduce the original."""
        demo_path = os.path.join(here, "demo.yaml")
        split_dir = str(tmp_path / "split1.demo.yaml")
        yj.split(demo_path, level=1, dirname=split_dir, do_dedent=False)

        pack_path = str(tmp_path / "packed.yaml")
        yj.pack(split_dir, pack_path, plain_pack=True)

        # Compare with original
        original = hy.load(demo_path)
        packed = hy.load(pack_path)
        assert original == packed

    def test_split_level2_pack_roundtrip(self, tmp_path):
        """Split level 2 (no dedent) then pack should reproduce the original."""
        demo_path = os.path.join(here, "demo.yaml")
        split_dir = str(tmp_path / "split2.demo.yaml")
        yj.split(demo_path, level=2, dirname=split_dir, do_dedent=False)

        pack_path = str(tmp_path / "packed.yaml")
        yj.pack(split_dir, pack_path, plain_pack=True)

        # Compare with original
        original = hy.load(demo_path)
        packed = hy.load(pack_path)
        assert original == packed

    def test_split_level1_dedent(self, tmp_path):
        """Split level 1 with dedent should match ref."""
        demo_path = os.path.join(here, "demo.yaml")
        split_dir = str(tmp_path / "split1.demo.yaml")
        yj.split(demo_path, level=1, dirname=split_dir, do_dedent=True)

        ref_dir = os.path.join(here, "ref_hifiyaml", "split.default_1.0")
        assert filecmp.cmp(
            os.path.join(split_dir, "obslist.txt"),
            os.path.join(ref_dir, "obslist.txt"),
        )


# ============================================================
# Tests: getkf_observer_tweak
# ============================================================

class TestGetkfTweak:
    def test_solver_replaces_roundrobin(self, getkf_data):
        """Solver mode should replace RoundRobin with Halo."""
        dcObs = yj.get_all_obs(getkf_data, shallow=True)
        # Test on the first observer that has RoundRobin
        for name, obs in dcObs.items():
            block = getkf_data[obs["pos1"]:obs["pos2"]]
            if any("RoundRobin" in line for line in block):
                yj.getkf_observer_tweak(block, "solver")
                assert not any("RoundRobin" in line for line in block)
                break

    def test_post_removes_temporal_thinning(self, getkf_data):
        """Post mode should remove Temporal Thinning filter."""
        dcObs = yj.get_all_obs(getkf_data, shallow=True)
        # Test on the first observer that has Temporal Thinning
        for name, obs in dcObs.items():
            block = getkf_data[obs["pos1"]:obs["pos2"]]
            if any("Temporal Thinning" in line for line in block):
                yj.getkf_observer_tweak(block, "post")
                assert not any("Temporal Thinning" in line for line in block)
                break

    def test_post_removes_reduce_obs_space(self, getkf_data):
        """Post mode should remove 'reduce obs space' actions."""
        dcObs = yj.get_all_obs(getkf_data, shallow=True)
        # Test on the first observer that has reduce obs space
        for name, obs in dcObs.items():
            block = getkf_data[obs["pos1"]:obs["pos2"]]
            if any("reduce obs space" in line for line in block):
                yj.getkf_observer_tweak(block, "post")
                assert not any("reduce obs space" in line for line in block)
                break


# ============================================================
# Tests: load_convinfo / load_satinfo
# ============================================================

class TestInfoFiles:
    def test_load_convinfo(self):
        """Should parse convinfo correctly."""
        orig_dir = os.getcwd()
        os.chdir(here)
        try:
            dc = yj.load_convinfo()
            assert len(dc) > 0
            # t181 has iuse=1
            assert "t181" in dc
            assert dc["t181"]["iuse"] == "1"
            # t183 has iuse=-1 (monitor)
            assert "t183" in dc
            assert dc["t183"]["iuse"] == "-1"
        finally:
            os.chdir(orig_dir)

    def test_load_satinfo(self):
        """Should parse satinfo correctly."""
        orig_dir = os.getcwd()
        os.chdir(here)
        try:
            dc = yj.load_satinfo()
            assert len(dc) > 0
            assert "amsua_n15" in dc
            assert len(dc["amsua_n15"]["channels"]) > 0
        finally:
            os.chdir(orig_dir)


# ============================================================
# Tests: update_sat_anchors
# ============================================================

class TestUpdateSatAnchors:
    def test_regex_extracts_sis(self):
        """Regex should correctly extract SIS from anchor line."""
        yaml_text = """\
observers:
  - obs space:
      name: amsua_n15
      _anchor_channels: &amsua_n15_channels
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
        11, 12, 13, 14, 15
      _anchor_use_flag: &amsua_n15_use_flag [
        1, 1, 1, 1, 1, -1, 1, 1, 1, 1,
        -1, 1, -1, -1, -1]
"""
        data = hy.text_to_yblock(yaml_text)
        orig_dir = os.getcwd()
        os.chdir(here)
        try:
            dcSatInfo = yj.load_satinfo()
            yj.update_sat_anchors(data, dcSatInfo)
            # After update, anchor line should still reference amsua_n15
            found = False
            for line in data:
                if "&amsua_n15_channels" in line:
                    found = True
                    break
            assert found, "Anchor &amsua_n15_channels should be preserved"
        finally:
            os.chdir(orig_dir)

    def test_no_anchor_is_noop(self):
        """If no _anchor_ lines exist, update_sat_anchors should be a no-op."""
        yaml_text = """\
observers:
  - obs space:
      name: test_obs
      obsdatain:
        engine:
          type: H5File
"""
        data = hy.text_to_yblock(yaml_text)
        original = list(data)
        yj.update_sat_anchors(data, {})
        assert data == original


# ============================================================
# Tests: get_all_filters
# ============================================================

class TestGetAllFilters:
    def test_finds_filters(self, demo_data):
        """Should find filters in the first observer."""
        dcObs = yj.get_all_obs(demo_data, shallow=False)
        first_obs = list(dcObs.values())[0]
        # The first observer should have obs filters
        filters = first_obs["filters"]
        assert len(filters) > 0
        # Each filter should have a category
        for f in filters:
            assert f["category"] != ""
            assert len(f["block"]) > 0


# ============================================================
# Tests: split1 and split2 (explicit level operators)
# ============================================================

class TestSplit1Split2:
    def test_split1_matches_reference(self, tmp_path):
        """split1 should produce output identical to ref split.default_1.1."""
        demo_path = os.path.join(here, "demo.yaml")
        split_dir = str(tmp_path / "split1.demo.yaml")
        yj.split(demo_path, level=1, dirname=split_dir, do_dedent=False)

        ref_dir = os.path.join(here, "ref_hifiyaml", "split.default_1.1")
        # Compare obslist.txt
        assert filecmp.cmp(
            os.path.join(split_dir, "obslist.txt"),
            os.path.join(ref_dir, "obslist.txt"),
            shallow=False,
        )
        # Compare main.yaml
        assert filecmp.cmp(
            os.path.join(split_dir, "main.yaml"),
            os.path.join(ref_dir, "main.yaml"),
            shallow=False,
        )
        # Compare each observer file
        with open(os.path.join(ref_dir, "obslist.txt")) as f:
            for obs_name in f.read().splitlines():
                assert filecmp.cmp(
                    os.path.join(split_dir, f"{obs_name}.yaml"),
                    os.path.join(ref_dir, f"{obs_name}.yaml"),
                    shallow=False,
                )

    def test_split2_matches_reference(self, tmp_path):
        """split2 should produce output identical to ref split.default_2."""
        demo_path = os.path.join(here, "demo.yaml")
        split_dir = str(tmp_path / "split2.demo.yaml")
        yj.split(demo_path, level=2, dirname=split_dir, do_dedent=False)

        ref_dir = os.path.join(here, "ref_hifiyaml", "split.default_2")
        # Compare obslist.txt
        assert filecmp.cmp(
            os.path.join(split_dir, "obslist.txt"),
            os.path.join(ref_dir, "obslist.txt"),
            shallow=False,
        )
        # Compare main.yaml
        assert filecmp.cmp(
            os.path.join(split_dir, "main.yaml"),
            os.path.join(ref_dir, "main.yaml"),
            shallow=False,
        )
        # Compare each observer directory (including filter YAML files)
        with open(os.path.join(ref_dir, "obslist.txt")) as f:
            for obs_name in f.read().splitlines():
                ref_obs_dir = os.path.join(ref_dir, obs_name)
                split_obs_dir = os.path.join(split_dir, obs_name)
                assert os.path.isdir(split_obs_dir), f"{obs_name}/ directory should exist"
                assert filecmp.cmp(
                    os.path.join(split_obs_dir, "obsmain.yaml"),
                    os.path.join(ref_obs_dir, "obsmain.yaml"),
                    shallow=False,
                )
                assert filecmp.cmp(
                    os.path.join(split_obs_dir, "filterlist.txt"),
                    os.path.join(ref_obs_dir, "filterlist.txt"),
                    shallow=False,
                )
                with open(os.path.join(ref_obs_dir, "filterlist.txt")) as fl:
                    for flt in fl.read().splitlines():
                        assert filecmp.cmp(
                            os.path.join(split_obs_dir, flt),
                            os.path.join(ref_obs_dir, flt),
                            shallow=False,
                        )

    def test_split1_pack_roundtrip(self, tmp_path):
        """split1 then pack should reproduce the original."""
        demo_path = os.path.join(here, "demo.yaml")
        split_dir = str(tmp_path / "split1.demo.yaml")
        yj.split(demo_path, level=1, dirname=split_dir, do_dedent=False)

        pack_path = str(tmp_path / "packed.yaml")
        yj.pack(split_dir, pack_path, plain_pack=True)

        original = hy.load(demo_path)
        packed = hy.load(pack_path)
        assert original == packed

    def test_split2_pack_roundtrip(self, tmp_path):
        """split2 then pack should reproduce the original."""
        demo_path = os.path.join(here, "demo.yaml")
        split_dir = str(tmp_path / "split2.demo.yaml")
        yj.split(demo_path, level=2, dirname=split_dir, do_dedent=False)

        pack_path = str(tmp_path / "packed.yaml")
        yj.pack(split_dir, pack_path, plain_pack=True)

        original = hy.load(demo_path)
        packed = hy.load(pack_path)
        assert original == packed


# ============================================================
# Tests: listobs
# ============================================================

class TestListObs:
    def test_listobs_finds_all_observers(self, demo_data):
        """listobs should find all 3 observers with correct short names."""
        dcObs = yj.get_all_obs(demo_data, shallow=False)
        snames = [obs["sname"] for obs in dcObs.values()]
        assert len(dcObs) == 3
        assert "t181" in snames
        assert "t183" in snames
        assert "t187" in snames

    def test_listobs_reports_filter_counts(self, demo_data):
        """listobs should report non-zero filter counts for each observer."""
        dcObs = yj.get_all_obs(demo_data, shallow=False)
        for name, observer in dcObs.items():
            filter_knt = (len(observer['pre filters']) + len(observer['filters']) +
                          len(observer['prior filters']) + len(observer['post filters']))
            assert filter_knt > 0


# ============================================================
# Tests: removeobs
# ============================================================

class TestRemoveObs:
    def test_removeobs_single(self, demo_data):
        """removeobs with one observer should reduce count by 1."""
        data = copy.copy(demo_data)
        dcObs = yj.get_all_obs(data, shallow=True)
        pos1, _ = hy.get_start_pos(data, "observations/observers")
        pos2 = hy.next_pos(data, pos1)
        output = data[0:pos1 + 1]
        obs_list = ["t181"]
        for _, observer in dcObs.items():
            sname = observer["sname"]
            keep = sname not in obs_list
            if keep:
                output.extend(data[observer["pos1"]:observer["pos2"]])
        output.extend(data[pos2:])
        # Verify one observer was removed
        remaining = yj.get_all_obs(output, shallow=True)
        assert len(remaining) == 2
        remaining_snames = [obs["sname"] for obs in remaining.values()]
        assert "t181" not in remaining_snames
        assert "t183" in remaining_snames
        assert "t187" in remaining_snames

    def test_removeobs_multiple(self, demo_data):
        """removeobs with two observers should reduce count by 2."""
        data = copy.copy(demo_data)
        dcObs = yj.get_all_obs(data, shallow=True)
        pos1, _ = hy.get_start_pos(data, "observations/observers")
        pos2 = hy.next_pos(data, pos1)
        output = data[0:pos1 + 1]
        obs_list = ["t181", "t183"]
        for _, observer in dcObs.items():
            sname = observer["sname"]
            keep = sname not in obs_list
            if keep:
                output.extend(data[observer["pos1"]:observer["pos2"]])
        output.extend(data[pos2:])
        remaining = yj.get_all_obs(output, shallow=True)
        assert len(remaining) == 1
        remaining_snames = [obs["sname"] for obs in remaining.values()]
        assert "t187" in remaining_snames

    def test_removeobs_matches_reference(self, demo_data):
        """removeobs t183 should match ref/removeobs.yaml."""
        data = copy.copy(demo_data)
        dcObs = yj.get_all_obs(data, shallow=True)
        pos1, _ = hy.get_start_pos(data, "observations/observers")
        pos2 = hy.next_pos(data, pos1)
        output = data[0:pos1 + 1]
        obs_list = ["t183"]
        for _, observer in dcObs.items():
            sname = observer["sname"]
            keep = sname not in obs_list
            if keep:
                output.extend(data[observer["pos1"]:observer["pos2"]])
        output.extend(data[pos2:])
        ref_path = os.path.join(here, "ref_hifiyaml", "removeobs.yaml")
        with open(ref_path, 'r') as f:
            ref_lines = [line.rstrip('\n') for line in f.readlines()]
        assert output == ref_lines


# ============================================================
# Tests: keepobs
# ============================================================

class TestKeepObs:
    def test_keepobs_single(self, demo_data):
        """keepobs with one observer should keep only that one."""
        data = copy.copy(demo_data)
        dcObs = yj.get_all_obs(data, shallow=True)
        pos1, _ = hy.get_start_pos(data, "observations/observers")
        pos2 = hy.next_pos(data, pos1)
        output = data[0:pos1 + 1]
        obs_list = ["t181"]
        for _, observer in dcObs.items():
            sname = observer["sname"]
            keep = sname in obs_list
            if keep:
                output.extend(data[observer["pos1"]:observer["pos2"]])
        output.extend(data[pos2:])
        remaining = yj.get_all_obs(output, shallow=True)
        assert len(remaining) == 1
        remaining_snames = [obs["sname"] for obs in remaining.values()]
        assert "t181" in remaining_snames

    def test_keepobs_multiple(self, demo_data):
        """keepobs with two observers should keep only those two."""
        data = copy.copy(demo_data)
        dcObs = yj.get_all_obs(data, shallow=True)
        pos1, _ = hy.get_start_pos(data, "observations/observers")
        pos2 = hy.next_pos(data, pos1)
        output = data[0:pos1 + 1]
        obs_list = ["t181", "t183"]
        for _, observer in dcObs.items():
            sname = observer["sname"]
            keep = sname in obs_list
            if keep:
                output.extend(data[observer["pos1"]:observer["pos2"]])
        output.extend(data[pos2:])
        remaining = yj.get_all_obs(output, shallow=True)
        assert len(remaining) == 2
        remaining_snames = [obs["sname"] for obs in remaining.values()]
        assert "t181" in remaining_snames
        assert "t183" in remaining_snames

    def test_keepobs_matches_reference(self, demo_data):
        """keepobs t183 should match ref/keepobs.yaml."""
        data = copy.copy(demo_data)
        dcObs = yj.get_all_obs(data, shallow=True)
        pos1, _ = hy.get_start_pos(data, "observations/observers")
        pos2 = hy.next_pos(data, pos1)
        output = data[0:pos1 + 1]
        obs_list = ["t183"]
        for _, observer in dcObs.items():
            sname = observer["sname"]
            keep = sname in obs_list
            if keep:
                output.extend(data[observer["pos1"]:observer["pos2"]])
        output.extend(data[pos2:])
        ref_path = os.path.join(here, "ref_hifiyaml", "keepobs.yaml")
        with open(ref_path, 'r') as f:
            ref_lines = [line.rstrip('\n') for line in f.readlines()]
        assert output == ref_lines
