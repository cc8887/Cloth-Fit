import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "source" / "structured"


class StructuredSpecTest(unittest.TestCase):
    def test_specs_are_index_subsets_not_mesh_records(self):
        facts = json.loads((ROOT / "geometry.json").read_text())
        mask = (ROOT / "no-fit.txt").read_text()
        self.assertRegex(mask, re.compile(r"\A[0-9\s]+\Z"))
        mask = [int(x) for x in mask.split()]
        zones = json.loads((ROOT / "zone_indices.json").read_text())["indices"]
        self.assertEqual(facts["vertices"], 3472)
        self.assertEqual(facts["faces"], 6840)
        self.assertEqual(len(mask), facts["no_fit_vertex_count"])
        self.assertEqual(facts["no_fit_face_count"], 4232)
        self.assertEqual({name: len(values) for name, values in zones.items()},
                         {"collar": 268, "shoulders": 175, "chest": 208, "waist": 337,
                          "abdomen": 162, "sleeves": 756, "hem": 108})
        self.assertEqual(len(set(sum(zones.values(), []))), sum(map(len, zones.values())))
        for values in [mask, *zones.values()]:
            self.assertEqual(len(values), len(set(values)))
            self.assertTrue(all(type(x) is int and 0 <= x < facts["vertices"] for x in values))

    def test_embedded_specs_match_recorded_rebuild_hashes(self):
        expected = dict(line.strip().split()[::-1] for line in (ROOT / "input.sha256").read_text().splitlines())
        for name in ("geometry.json", "zone_indices.json", "no-fit.txt"):
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected[name])


if __name__ == "__main__":
    unittest.main()
