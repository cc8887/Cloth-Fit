import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / "tools" / "reproduce.py"
spec = importlib.util.spec_from_file_location("reproduce", path)
reproduce = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reproduce)


class ReproduceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="cloth-fit-test-")
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.repo = self.temp / "upstream"
        original = self.repo / "garment-data" / "foxgirl_skirt"
        original.mkdir(parents=True)
        (original / "a.obj").write_text("fixture")
        (original / "setup.json").write_text(json.dumps({
            "avatar_mesh_path": "a.obj",
            "garment_mesh_path": "a.obj",
            "avatar_skin_weights_path": "missing-optional-skin.txt",
            "solver": {"max_threads": 16},
            "output": {"skip_frame": 6},
        }))
        self.binary = self.temp / "mock-solver"
        self.binary.write_text("""#!/bin/sh
set -eu
while [ "$#" -gt 0 ]; do
case "$1" in
  -o) shift; out="$1";;
esac
shift
done
touch "$out/step_garment_9.obj" "$out/step_garment_12.obj" "$out/step_garment_incomplete.obj"
printf 'Garment retargeting succeeded!\\n'
""")
        self.binary.chmod(0o700)
        git = patch.object(reproduce.subprocess, "check_output", return_value=reproduce.REVISION + "\n")
        git.start()
        self.addCleanup(git.stop)

    def invoke(self, case, output, *options):
        argv = [str(path), case, "--repo", str(self.repo), "--solver", str(self.binary),
                "--out", str(output), *options]
        with patch("sys.argv", argv), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return reproduce.main()

    def test_prepare_only_absolute_and_no_overwrite(self):
        out = self.temp / "dry"
        self.assertEqual(self.invoke("foxgirl_skirt", out, "--prepare-only", "--threads", "2"), 0)
        actual = json.loads((out / "setup.json").read_text())
        self.assertTrue(Path(actual["avatar_mesh_path"]).is_absolute())
        self.assertEqual(actual["solver"]["max_threads"], 2)
        self.assertEqual(Path(actual["avatar_skin_weights_path"]).name, "missing-optional-skin.txt")
        self.assertEqual(actual["output"]["skip_frame"], 1)
        self.assertFalse((out / "output").exists())
        with self.assertRaises(SystemExit) as exc:
            self.invoke("foxgirl_skirt", out, "--prepare-only")
        self.assertEqual(exc.exception.code, 2)
        self.assertEqual(json.loads((out / "setup.json").read_text()), actual)

    def test_v4_without_source_refuses_and_keeps_path_empty(self):
        out = self.temp / "would-create"
        with self.assertRaises(SystemExit) as exc:
            self.invoke("FoxGirl", out, "--prepare-only")
        self.assertEqual(exc.exception.code, 2)
        self.assertFalse(out.exists())

    def test_v4_local_sources_and_two_substeps(self):
        local = self.temp / "approved"
        local.mkdir()
        for filename in reproduce.STRUCTURED_INPUTS.values():
            (local / filename).touch()
        avatar = self.repo / "garment-data" / "assets" / "avatars" / "FoxGirl"
        avatar.mkdir(parents=True)
        for name in ("avatar.obj", "skeleton.obj"):
            (avatar / name).touch()
        out = self.temp / "structured"
        self.assertEqual(self.invoke("FoxGirl", out, "--prepare-only", "--structured-source", str(local)), 0)
        settings = json.loads((out / "setup.json").read_text())
        self.assertEqual(settings["fit_weight"], 1.4)
        self.assertEqual(settings["incremental_steps"], 2)
        self.assertEqual(settings["solver"]["max_threads"], 4)
        self.assertEqual(settings["avatar_skin_weights_path"], "")
        self.assertEqual(Path(settings["no_fit_spec_path"]).parent, local)

    def test_solve_does_not_claim_success_only_from_exit_code(self):
        out = self.temp / "success"
        self.assertEqual(self.invoke("foxgirl_skirt", out), 0)
        run = json.loads((out / "metrics.json").read_text())
        self.assertEqual(run["latest_saved_step"], 12)
        self.assertTrue(run["run_succeeded"])
        self.binary.write_text(self.binary.read_text().replace("Garment retargeting succeeded!", "Not converged"))
        out = self.temp / "failure"
        self.assertEqual(self.invoke("foxgirl_skirt", out), 1)
        self.assertFalse(json.loads((out / "metrics.json").read_text())["run_succeeded"])


if __name__ == "__main__":
    unittest.main()
