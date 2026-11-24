#!/usr/bin/env bash
# Regenerate local V2/V4 geometry with the pinned author's Puffer_dense input.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
revision=123e2440f46720b5f993c91d1705aff838aa55fb
repo=${1:-"$root/cloth-fit"}
out=${2:-"$root/local-inputs/rebuilt"}
blender_bin=${BLENDER:-blender}
python_bin=${PYTHON:-python3}
if [[ -e "$out" ]]; then
    printf 'Output exists; choose a new directory: %s\n' "$out" >&2
    exit 2
fi
if [[ "$(git -C "$repo" rev-parse HEAD)" != "$revision" ]]; then
    printf 'Expected Cloth-fit at %s\n' "$revision" >&2
    exit 2
fi
repo=$(cd "$repo" && pwd)
puffer="$repo/garment-data/assets/garments/Puffer_dense"
test -f "$puffer/garment.obj" && test -f "$puffer/skeleton.obj" || {
    echo 'Signed-off local upstream Puffer_dense OBJ input is required.' >&2
    exit 2
}
mkdir -p "$out/v2"
out=$(cd "$out" && pwd)
CLOTH_FIT_PUFFER="$puffer" CLOUD_COAT_OUT="$out/v2" COAT_HEM=-.72 \
    "$blender_bin" --factory-startup -b -t 2 --python-exit-code 1 -P "$root/source/base/build_coat.py"
structured="$root/source/structured"
"$blender_bin" --factory-startup -b -t 2 --python-exit-code 1 -P "$structured/structure_coat.py" -- --base "$out/v2" --out "$out/v4"
if [[ "${CONTROLS:-0}" == 1 ]]; then
    for key in chest waist abdomen sleeve hem structure; do
        "$blender_bin" --factory-startup -b -t 2 --python-exit-code 1 \
            -P "$structured/structure_coat.py" -- --base "$out/v2" --out "$out/variants/$key" "--$key" 0
    done
    # The original delta generator reads/writes beside itself. Stage it only
    # within locally generated outputs, never in the versioned source tree.
    cp "$structured/make_structured_control_data.py" "$out/v4/"
    "$python_bin" "$out/v4/make_structured_control_data.py" "$out/variants"
    "$blender_bin" --factory-startup -b -t 2 --python-exit-code 1 \
        -P "$structured/add_structured_controls.py" -- "$out/v4/cloud_coat.blend" \
        "$out/v4/CloudCoat_Structured.blend" --data "$out/v4/structured_controls.json"
fi
printf '\nGarment source, solver OBJ/skeleton/mask and mesh diagnostics: %s\n' "$out/v4"
