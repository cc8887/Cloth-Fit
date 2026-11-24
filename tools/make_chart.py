#!/usr/bin/env python3
"""Regenerate the SVG from the recorded numerical outputs; no model geometry."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
stats = json.loads((root / "results" / "structured.json").read_text())["cases"]
out = ['''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="430" viewBox="0 0 860 430" role="img" aria-labelledby="title desc">
<title id="title">Cloth-fit: measured garment clearance, V3 vs V4</title><desc id="desc">V4 increased chest and abdomen clearance on both avatars. FoxGirl waist and hem clearances decreased. These are normalized units, not centimeters.</desc>
<rect x="1" y="1" width="858" height="428" rx="18" fill="#171a22" stroke="#363d49"/>
<g font-family="Arial, sans-serif" fill="#f5f4ef">
<text x="36" y="46" font-size="27" font-weight="700">Chest-first ease, measured</text>
<text x="36" y="72" font-size="15" fill="#b8c0d0">Median gap to body · % of longest normalized skeleton span · not cm</text>
<rect x="38" y="96" width="12" height="12" rx="3" fill="#9faec8"/><text x="57" y="107" font-size="13">V3 loose</text>
<rect x="138" y="96" width="12" height="12" rx="3" fill="#ffa783"/><text x="157" y="107" font-size="13">V4 structured</text>''']
for i, row in enumerate(stats):
    x = 36 + i * 415
    out.append(f'<text x="{x}" y="145" font-size="19" font-weight="700">{row["case"]}</text>')
    for j, name in enumerate(("chest", "waist", "abdomen", "hem")):
        y = 171 + j * 54
        z = row["zones"][name]
        out.append(f'<text x="{x}" y="{y + 17}" font-size="14" fill="#cdd4e0">{name.title()}</text>')
        for k, (value, color) in enumerate(((z["median_gap_v3"], "#9faec8"), (z["median_gap_v4"], "#ffa783"))):
            bar_y = y + k * 15
            length = value * 41
            out.append(f'<rect x="{x + 72}" y="{bar_y}" width="{length:.2f}" height="9" rx="3" fill="{color}"/>'
                       f'<text x="{x + 79 + length:.2f}" y="{bar_y + 8}" font-size="11" fill="{color}">{value:.2f}</text>')
out.append('<path d="M36 394H824" stroke="#363d49"/><text x="36" y="415" font-size="13" fill="#b8c0d0">Static mesh check only. No test of motion, physical stiffness, or all paper figures.</text></g></svg>')
(root / "figures" / "clearance-v3-v4.svg").write_text("\n".join(out) + "\n")
