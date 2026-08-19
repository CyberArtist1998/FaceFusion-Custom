#!/usr/bin/env python3
"""
Batch swap + SCORE + auto-select.  One martyr -> every target poster.

This is the piece the MANUAL was missing. The manual's Step 4A/4B ran one fixed
command and produced a single final.png with no evidence behind it. This script
instead renders several candidates per poster, measures every one against the real
face, writes the numbers to disk, and picks the winner from the measurements.

Everything it decides is auditable:

  <out>/<target>/scores.txt        human-readable table for that poster
  <out>/<target>/scores.json       same data, machine-readable
  <out>/<target>/_sheet.png        contact sheet, settings + score on every tile
  <out>/<target>/FINAL_<name>.png  the winner, chosen by score
  <out>/SCORES_MASTER.txt          every poster, every candidate, ranked
  <out>/SCORES_MASTER.csv          the same for a spreadsheet
  <out>/REPORT.md                  summary + anything that needs your eyes

Why the candidates are what they are (measured on 4 posters, see REPORT.md):
  * inswapper_128 won every time; hyperswap_1a_256 (FaceFusion's default) transferred
    almost nothing (0.077-0.42).
  * weight 0.5-0.65 is the peak; higher makes it worse.
  * mask blur 0.15 wins on photoreal, 0.0 on stylized; the 0.3 default loses ~0.01.
  * the face enhancer is destructive at its default blend of 80. Only gpen_bfr_1024
    at <=60 is free, so that is the single enhancer candidate.

SAFETY RAIL — why ghost/blendswap are excluded by default:
  On profile/angled posters the Ghost models score WELL by rotating the face toward
  the camera, which wrecks the composition. ArcFace rewards that because the reference
  photo is frontal. Auto-selection cannot see it, so those models are off unless you
  pass --include-risky, and any candidate from them that wins is flagged REVIEW.

Usage:
    python ff_batch.py --source "پهپاد - امیردریادار - حسین دانا"
    python ff_batch.py --source <folder> --kinds Real
    python ff_batch.py --source <folder> --limit 3          # quick trial
    python ff_batch.py --list-sources
"""

import argparse
import csv
import json
import pathlib
import subprocess
import sys

# The martyr folders are named in Persian; the Windows console defaults to cp1252
# and would crash on them. Force UTF-8 on the streams before anything prints.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

FF_DIR = pathlib.Path(r"D:\MyWorld-Sync\011-AI\FaceFusion")
PYTHON = FF_DIR / "venv_311" / "Scripts" / "python.exe"
FF = "facefusion.py"

PROJECT = pathlib.Path(r"D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters")
SOURCES = PROJECT / "SourcePictures"
TARGETS = PROJECT / "TargetPictures"
OUT_ROOT = PROJECT / "Finial"

# Settings held constant for every candidate.
BASE = {
    "face-selector-mode": "one",
    "face-detector-model": "yolo_face",
    "face-detector-size": "640x640",
    "face-detector-score": "0.5",
    "face-mask-types": ["box"],
    "face-mask-padding": ["0", "0", "0", "0"],
    "output-image-quality": "100",
}

# name -> the settings that differ. Blur differs by poster kind, so it is filled in
# per-kind below rather than hardcoded here.
def candidates(kind, include_risky):
    blur = "0.15" if kind == "Real" else "0.0"
    out = [
        (f"inswapper_w050_b{blur}", {
            "processors": ["face_swapper"], "face-swapper-model": "inswapper_128",
            "face-swapper-pixel-boost": "512x512", "face-swapper-weight": "0.5",
            "face-mask-blur": blur}),
        (f"inswapper_w065_b{blur}", {
            "processors": ["face_swapper"], "face-swapper-model": "inswapper_128",
            "face-swapper-pixel-boost": "512x512", "face-swapper-weight": "0.65",
            "face-mask-blur": blur}),
        # the alternate blur, in case this poster disagrees with the general rule
        (f"inswapper_w065_b{'0.0' if kind == 'Real' else '0.15'}", {
            "processors": ["face_swapper"], "face-swapper-model": "inswapper_128",
            "face-swapper-pixel-boost": "512x512", "face-swapper-weight": "0.65",
            "face-mask-blur": "0.0" if kind == "Real" else "0.15"}),
        # the one enhancer that measured free
        (f"inswapper_w065_b{blur}_gpen60", {
            "processors": ["face_swapper", "face_enhancer"],
            "face-swapper-model": "inswapper_128",
            "face-swapper-pixel-boost": "512x512", "face-swapper-weight": "0.65",
            "face-mask-blur": blur,
            "face-enhancer-model": "gpen_bfr_1024", "face-enhancer-blend": "60"}),
    ]
    if include_risky:
        for m in ("ghost_1_256", "ghost_2_256"):
            out.append((f"RISKY_{m}_w065_b{blur}", {
                "processors": ["face_swapper"], "face-swapper-model": m,
                "face-swapper-pixel-boost": "512x512", "face-swapper-weight": "0.65",
                "face-mask-blur": blur}))
    return out


def flatten(key, value):
    return [f"--{key}"] + ([str(v) for v in value] if isinstance(value, list) else [str(value)])


def find_source_face(folder):
    """Prefer an existing Source_face.jpg; never guess at a full poster."""
    direct = folder / "Source_face.jpg"
    if direct.exists():
        return direct
    hits = sorted(folder.rglob("Source_face.jpg"))
    return hits[0] if hits else None


def collect_targets(kinds, limit):
    jobs = []
    for kind in kinds:
        d = TARGETS / kind
        if not d.is_dir():
            print(f"WARNING: {d} missing, skipping", file=sys.stderr)
            continue
        files = sorted(p for p in d.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
        if limit:
            files = files[:limit]
        jobs += [(kind, f) for f in files]
    return jobs


def render_all(source_face, jobs, out_root, include_risky, provider):
    """One FaceFusion job holds every render, so each model loads exactly once."""
    job_id = "ff_batch"
    subprocess.run([str(PYTHON), FF, "job-delete", job_id], cwd=FF_DIR, capture_output=True)
    cmds = [[str(PYTHON), FF, "job-create", job_id]]
    plan = []

    for kind, target in jobs:
        outdir = out_root / target.stem
        outdir.mkdir(parents=True, exist_ok=True)
        for name, extra in candidates(kind, include_risky):
            dst = outdir / f"{name}.png"
            merged = {**BASE, **extra}
            cmd = [str(PYTHON), FF, "job-add-step", job_id,
                   "-s", str(source_face), "-t", str(target), "-o", str(dst)]
            for k, v in merged.items():
                cmd += flatten(k, v)
            cmds.append(cmd)
            plan.append({"kind": kind, "target": target, "outdir": outdir,
                         "candidate": name, "path": dst, "settings": merged})

    cmds.append([str(PYTHON), FF, "job-submit", job_id])
    cmds.append([str(PYTHON), FF, "job-run", job_id,
                 "--execution-providers", *provider,
                 "--execution-thread-count", "4",
                 "--log-level", "error"])

    print(f"rendering {len(plan)} candidates across {len(jobs)} posters ...")
    for i, c in enumerate(cmds, 1):
        if subprocess.run(c, cwd=FF_DIR).returncode != 0:
            print(f"WARNING: step {i} failed; continuing", file=sys.stderr)
    return plan


def write_target_report(outdir, target, kind, baseline, rows, winner):
    lines = [
        f"POSTER : {target.name}",
        f"KIND   : {kind}",
        f"BASELINE (untouched poster vs real face): {fmt(baseline)}",
        "",
        f"{'score':>8}  {'candidate':<38} settings",
        "-" * 100,
    ]
    for r in rows:
        s = r["settings"]
        desc = (f"model={s.get('face-swapper-model')} w={s.get('face-swapper-weight')} "
                f"blur={s.get('face-mask-blur')} "
                f"enh={s.get('face-enhancer-model', 'none')}"
                f"{'/' + s['face-enhancer-blend'] if s.get('face-enhancer-model') else ''}")
        mark = " <== CHOSEN" if winner and r["candidate"] == winner["candidate"] else ""
        lines += [f"{fmt(r['score']):>8}  {r['candidate']:<38} {desc}{mark}"]
    lines += ["", "Higher = closer to the real person. An untouched AI poster typically",
              "scores 0.05-0.20, so anything near 0.85+ is a strong swap.", ""]
    if winner and winner["candidate"].startswith("RISKY_"):
        lines += ["!! REVIEW: the winner is a Ghost model. On angled/profile posters these",
                  "!! score high by rotating the face toward the camera, which looks wrong.",
                  "!! Check the picture before using it.", ""]
    (outdir / "scores.txt").write_text("\n".join(lines), encoding="utf-8")
    (outdir / "scores.json").write_text(json.dumps(
        {"target": target.name, "kind": kind, "baseline": baseline,
         "winner": winner["candidate"] if winner else None,
         "candidates": [{"candidate": r["candidate"], "score": r["score"],
                         "settings": r["settings"]} for r in rows]},
        indent=2, ensure_ascii=False), encoding="utf-8")


def fmt(v):
    return "n/a" if v is None else f"{v:.4f}"


def sheet(outdir, rows, baseline_path, crop=None, cols=3, thumb=420):
    from PIL import Image, ImageDraw
    tiles = []
    for r in [{"candidate": "TEMPLATE (no swap)", "path": baseline_path, "score": None}] + rows:
        try:
            im = Image.open(r["path"]).convert("RGB")
        except Exception:
            continue
        if crop:
            x, y, w, h = crop
            im = im.crop((x, y, min(x + w, im.width), min(y + h, im.height)))
        im.thumbnail((thumb, thumb), Image.LANCZOS)
        tiles.append((f"{r['candidate']}  {fmt(r['score'])}", im))
    if not tiles:
        return
    tw = max(i.width for _, i in tiles); th = max(i.height for _, i in tiles) + 18
    rows_n = (len(tiles) + cols - 1) // cols
    s = Image.new("RGB", (cols * tw, rows_n * th), "black")
    d = ImageDraw.Draw(s)
    for i, (lab, im) in enumerate(tiles):
        cx, cy = (i % cols) * tw, (i // cols) * th
        s.paste(im, (cx, cy)); d.text((cx + 3, cy + im.height + 3), lab[:60], fill="white")
    s.save(outdir / "_sheet.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", help="folder name under SourcePictures (or a full path)")
    ap.add_argument("--list-sources", action="store_true")
    ap.add_argument("--kinds", default="Real,Stylized")
    ap.add_argument("--limit", type=int, help="only the first N posters per kind")
    ap.add_argument("--include-risky", action="store_true",
                    help="also try ghost models (see the safety note above)")
    ap.add_argument("--out", help="output root (default: Finial/<source folder>)")
    ap.add_argument("--sheet-crop", help="x,y,w,h to zoom contact sheets onto the face")
    ap.add_argument("--provider", nargs="*", default=None)
    args = ap.parse_args()

    if args.list_sources:
        for d in sorted(p for p in SOURCES.iterdir() if p.is_dir()):
            face = find_source_face(d)
            print(f"  {'OK ' if face else '-- '} {d.name}")
        return

    if not args.source:
        sys.exit("need --source (or --list-sources)")

    folder = pathlib.Path(args.source)
    if not folder.is_absolute():
        folder = SOURCES / args.source
    if not folder.is_dir():
        sys.exit(f"ERROR: source folder not found: {folder}")

    source_face = find_source_face(folder)
    if not source_face:
        sys.exit(f"ERROR: no Source_face.jpg in {folder}\n"
                 f"       Run ff_prep_source.py first — FaceFusion averages every face it\n"
                 f"       finds in the source, so it must be cropped to exactly one.")

    provider = args.provider
    if not provider:
        try:
            import onnxruntime
            names = {p.replace("ExecutionProvider", "").lower() for p in onnxruntime.get_available_providers()}
            provider = ["cuda"] if "cuda" in names else ["cpu"]
        except Exception:
            provider = ["cpu"]

    kinds = [k.strip() for k in args.kinds.split(",") if k.strip()]
    jobs = collect_targets(kinds, args.limit)
    if not jobs:
        sys.exit("ERROR: no target posters found")

    out_root = pathlib.Path(args.out) if args.out else OUT_ROOT / folder.name
    out_root.mkdir(parents=True, exist_ok=True)
    crop = tuple(int(v) for v in args.sheet_crop.split(",")) if args.sheet_crop else None

    print(f"source : {source_face}")
    print(f"posters: {len(jobs)}  ({', '.join(kinds)})")
    print(f"output : {out_root}\n")

    plan = render_all(source_face, jobs, out_root, args.include_risky, provider)

    # ---- score everything in ONE pass so the models load once ----
    print("\nscoring ...")
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import ff_identity

    to_score = [p["path"] for p in plan if p["path"].exists()]
    to_score += [t for _, t in jobs]                      # untouched posters = baselines
    scores = ff_identity.score_paths(source_face, to_score)

    def look(p):
        """Scores are keyed by resolved absolute path — candidate FILENAMES repeat
        across poster folders, so a name lookup would collide."""
        return scores.get(str(pathlib.Path(p).resolve()))

    master, summary = [], []
    for kind, target in jobs:
        outdir = out_root / target.stem
        baseline = look(target)
        rows = [{"candidate": p["candidate"], "score": look(p["path"]),
                 "settings": p["settings"], "path": p["path"]}
                for p in plan if p["target"] == target and p["path"].exists()]
        rows.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))

        winner = next((r for r in rows if r["score"] is not None), None)
        if winner:
            dst = outdir / f"FINAL_{target.stem}.png"
            dst.write_bytes(winner["path"].read_bytes())

        write_target_report(outdir, target, kind, baseline, rows, winner)
        sheet(outdir, rows, target, crop)

        for r in rows:
            master.append({"poster": target.name, "kind": kind,
                           "baseline": baseline, "candidate": r["candidate"],
                           "score": r["score"],
                           "chosen": bool(winner and r["candidate"] == winner["candidate"])})
        summary.append((target.name, kind, baseline, winner))

    # ---- master outputs ----
    with (out_root / "SCORES_MASTER.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["poster", "kind", "baseline", "candidate", "score", "chosen"])
        w.writeheader(); w.writerows(master)

    lines = [f"BATCH SCORES — source: {folder.name}", f"reference face: {source_face.name}",
             f"posters: {len(jobs)}   candidates each: {len(candidates('Real', args.include_risky))}", ""]
    for name, kind, baseline, winner in summary:
        lines.append(f"{name}  [{kind}]   baseline {fmt(baseline)}")
        lines.append(f"    WINNER: {winner['candidate'] if winner else 'NONE'}  {fmt(winner['score']) if winner else ''}")
    weak = [s for s in summary if s[3] and s[3]["score"] is not None and s[3]["score"] < 0.60]
    if weak:
        lines += ["", "NEEDS ATTENTION (winner below 0.60 — likely a bad swap):"]
        lines += [f"    {s[0]}  {fmt(s[3]['score'])}" for s in weak]
    (out_root / "SCORES_MASTER.txt").write_text("\n".join(lines), encoding="utf-8")

    print("\n" + "\n".join(lines[-40:]))
    print(f"\nwrote {out_root / 'SCORES_MASTER.txt'}")
    print(f"      {out_root / 'SCORES_MASTER.csv'}")
    print(f"      per-poster scores.txt / scores.json / _sheet.png / FINAL_*.png")


if __name__ == "__main__":
    main()
