#!/usr/bin/env python3
"""
FaceFusion 3.6.1 staged parameter sweep — martyr memorial posters.

Verified against the local install at "D:\\Softwares\\FaceFusion - Copy"
(facefusion/metadata.py -> version 3.6.1):

  * job_id is POSITIONAL on job-create / job-add-step / job-submit / job-run
  * every axis swept here is a STEP key (program.py:107-192, face_swapper/core.py:521,
    face_enhancer/core.py:298) -> one job holds all variants and each model loads once
  * execution + memory settings are JOB keys (program.py:240,249) -> they go on job-run
  * pixel-boost values are validated per model against face_swapper_set

Stages (run one at a time, judge, then move on):
  models    13 swapper models, everything else fixed        -> the decisive stage
  boost     pixel-boost ladder on the models you shortlist
  weight    identity-strength ladder (see note below)
  enhancer  9 enhancer models, then a blend ladder
  mask      mask type / blur / padding
  detector  detector model + rotation angles

NOTE on --face-swapper-weight (face_swapper/core.py:701-709):

    w = numpy.interp(weight, [0, 1], [0.35, -0.35])
    source_embedding = source_embedding * (1 - w) + target_embedding * w

  0.5 -> pure source identity. Below 0.5 blends the TARGET's identity in
  (this is the "looks like a cousin" failure). Above 0.5 the coefficient goes
  negative and extrapolates AWAY from the target. Sweep 0.5..1.0; values under
  0.5 are included in the `weight` stage only to make the effect visible.

Usage:
    python ff_sweep.py --stage models --list
    python ff_sweep.py --stage models --execute
    python ff_sweep.py --stage models --sheet
    python ff_sweep.py --stage boost --models hyperswap_1a_256 ghost_2_256 --execute
"""

import argparse
import itertools
import pathlib
import shutil
import subprocess
import sys

# ---------------------------------------------------------------------------
# PATHS - edit these if anything moves
# ---------------------------------------------------------------------------
FF_DIR  = pathlib.Path(r"D:\Softwares\FaceFusion - Copy")
PYTHON  = FF_DIR / "venv" / "Scripts" / "python.exe"
FF      = "facefusion.py"
MODELS_DIR = FF_DIR / ".assets" / "models"

PROJECT = pathlib.Path(r"D:\01-AI\002-MertydomPosters")

# Set by --sweep-dir so one script serves every subject folder (sweep, sweep-02, ...).
SWEEP   = PROJECT / "sweep"
TARGET  = SWEEP / "Target.png"


def use_sweep_dir(name):
    """Repoint every path at a different subject folder."""
    global SWEEP, TARGET, SOURCE_CROPPED, SOURCE_FULL, OUT_ROOT
    SWEEP = PROJECT / name
    TARGET = SWEEP / "Target.png"
    SOURCE_CROPPED = SWEEP / "Source_face.jpg"
    OUT_ROOT = SWEEP / "out"

    # The raw source is whatever image isn't the target or the crop - filenames vary
    # per subject (Source.jpg, 1902095171.jpg, ...), so discover it instead of assuming.
    cands = [p for p in sorted(SWEEP.glob("*"))
             if p.suffix.lower() in (".jpg", ".jpeg", ".png")
             and p.name not in (TARGET.name, SOURCE_CROPPED.name)]
    SOURCE_FULL = cands[0] if cands else SWEEP / "Source.jpg"

# Prefer the cropped face. FaceFusion AVERAGES every face it detects across the
# source images (face_swapper/core.py:757 -> get_average_face), so feeding it the
# full poster risks blending in the partial second photo at the right edge.
SOURCE_CROPPED = SWEEP / "Source_face.jpg"
SOURCE_FULL    = SWEEP / "Source.jpg"

OUT_ROOT = SWEEP / "out"

# ---------------------------------------------------------------------------
# EXECUTION (job-level -> passed to job-run)
# ---------------------------------------------------------------------------
# NOTE: this venv currently has CPU-only onnxruntime, so 'cpu' is the only legal
# choice. That is fine for stills - a 1856x2304 swap takes ~8s. Switch to 'cuda'
# only after running:  python install.py --onnxruntime cuda
EXECUTION_THREAD_COUNT = "4"
VIDEO_MEMORY_STRATEGY  = "strict"   # 8GB card: strict unloads aggressively
LOG_LEVEL              = "info"


def available_providers():
    """Ask onnxruntime what it can actually do, so we never build an illegal command."""
    try:
        import onnxruntime
        names = {p.replace("ExecutionProvider", "").lower() for p in onnxruntime.get_available_providers()}
        return ["cuda"] if "cuda" in names else ["cpu"]
    except Exception:
        return ["cpu"]

# ---------------------------------------------------------------------------
# MODEL / OPTION TABLES - copied verbatim from the 3.6.1 source
# ---------------------------------------------------------------------------
FACE_SWAPPER_SET = {
    "blendswap_256":           ["256x256", "384x384", "512x512", "768x768", "1024x1024"],
    "ghost_1_256":             ["256x256", "512x512", "768x768", "1024x1024"],
    "ghost_2_256":             ["256x256", "512x512", "768x768", "1024x1024"],
    "ghost_3_256":             ["256x256", "512x512", "768x768", "1024x1024"],
    "hififace_unofficial_256": ["256x256", "512x512", "768x768", "1024x1024"],
    "hyperswap_1a_256":        ["256x256", "512x512", "768x768", "1024x1024"],
    "hyperswap_1b_256":        ["256x256", "512x512", "768x768", "1024x1024"],
    "hyperswap_1c_256":        ["256x256", "512x512", "768x768", "1024x1024"],
    "inswapper_128":           ["128x128", "256x256", "384x384", "512x512", "768x768", "1024x1024"],
    "inswapper_128_fp16":      ["128x128", "256x256", "384x384", "512x512", "768x768", "1024x1024"],
    "simswap_256":             ["256x256", "512x512", "768x768", "1024x1024"],
    "simswap_unofficial_512":  ["512x512", "768x768", "1024x1024"],
    "uniface_256":             ["256x256", "512x512", "768x768", "1024x1024"],
}
ALL_SWAPPERS = list(FACE_SWAPPER_SET)

# face_enhancer/types.py:15
ENHANCERS = [
    "codeformer", "gfpgan_1.2", "gfpgan_1.3", "gfpgan_1.4",
    "gpen_bfr_256", "gpen_bfr_512", "gpen_bfr_1024", "gpen_bfr_2048",
    "restoreformer_plus_plus",
]

# choices.py:7 - only these models accept a size other than 640x640
DETECTORS = ["retinaface", "scrfd", "yolo_face", "yunet", "many"]

# 512x512 is the one pixel-boost value legal for ALL 13 swappers -> use it as the
# constant in the `models` stage so the comparison is apples-to-apples.
COMMON_BOOST = "512x512"

# Baseline held fixed while one axis varies.
BASE = {
    "face-selector-mode": "one",      # single face in both images; avoids needing a reference
    "face-detector-model": "yolo_face",
    "face-detector-size": "640x640",
    "face-detector-score": "0.5",
    "face-mask-types": ["box"],
    "face-mask-blur": "0.3",
    "face-mask-padding": ["0", "0", "0", "0"],
    "output-image-quality": "100",
}


# ---------------------------------------------------------------------------
# STAGES  -> each returns a list of (output_name, {step args})
# ---------------------------------------------------------------------------
def stage_models(args):
    """All 13 swappers at a common pixel boost, no enhancer. The decisive test."""
    out = []
    for model in args.models or ALL_SWAPPERS:
        boost = COMMON_BOOST if COMMON_BOOST in FACE_SWAPPER_SET[model] else FACE_SWAPPER_SET[model][0]
        out.append((
            f"{model}",
            {"processors": ["face_swapper"],
             "face-swapper-model": model,
             "face-swapper-pixel-boost": boost,
             "face-swapper-weight": "0.5"},
        ))
    return out


def stage_boost(args):
    """Pixel-boost ladder. Shortlist models first with --models."""
    models = args.models or ["hyperswap_1a_256", "simswap_unofficial_512"]
    out = []
    for model, boost in itertools.product(models, ["256x256", "512x512", "768x768", "1024x1024"]):
        if boost not in FACE_SWAPPER_SET[model]:
            continue
        out.append((
            f"{model}__pb{boost.split('x')[0]}",
            {"processors": ["face_swapper"],
             "face-swapper-model": model,
             "face-swapper-pixel-boost": boost,
             "face-swapper-weight": "0.5"},
        ))
    return out


def stage_weight(args):
    """Identity-strength ladder. 0.0-0.4 included only to show the averaging failure."""
    models = args.models or ["hyperswap_1a_256"]
    out = []
    for model, w in itertools.product(models, ["0.0", "0.25", "0.5", "0.65", "0.8", "0.9", "1.0"]):
        boost = COMMON_BOOST if COMMON_BOOST in FACE_SWAPPER_SET[model] else FACE_SWAPPER_SET[model][0]
        out.append((
            f"{model}__w{w.replace('.', '')}",
            {"processors": ["face_swapper"],
             "face-swapper-model": model,
             "face-swapper-pixel-boost": boost,
             "face-swapper-weight": w},
        ))
    return out


def stage_enhancer(args):
    """All 9 enhancers at blend 80, then a blend ladder on gfpgan_1.4 and codeformer.

    Enhancer blend is the most over-cranked setting in FaceFusion. At 100 the
    enhancer's own face prior overwrites the identity that was just transferred.
    """
    model = (args.models or ["hyperswap_1a_256"])[0]
    boost = COMMON_BOOST if COMMON_BOOST in FACE_SWAPPER_SET[model] else FACE_SWAPPER_SET[model][0]
    swap = {"face-swapper-model": model,
            "face-swapper-pixel-boost": boost,
            "face-swapper-weight": "0.5"}

    # FaceFusion pre-checks and downloads EVERY step's model before processing any
    # of them, so a single unavailable model aborts the whole job and you get zero
    # renders. Drop anything that isn't on disk, and say so rather than silently
    # shrinking the sweep.
    wanted = args.enhancers or ENHANCERS
    enhancers = [e for e in wanted if (MODELS_DIR / f"{e}.onnx").exists()]
    missing = [e for e in wanted if e not in enhancers]
    if missing and not args.allow_download:
        print(f"# skipping {len(missing)} enhancer(s) not on disk: {', '.join(missing)}\n"
              f"#   (pass --allow-download to attempt them; one failure aborts the job)",
              file=sys.stderr)
    if args.allow_download:
        enhancers = wanted

    out = []
    for enh in enhancers:
        out.append((
            f"enh_{enh}__b80",
            {"processors": ["face_swapper", "face_enhancer"], **swap,
             "face-enhancer-model": enh, "face-enhancer-blend": "80"},
        ))
    for enh, blend in itertools.product(["gfpgan_1.4", "codeformer"], ["0", "25", "40", "60", "80", "100"]):
        out.append((
            f"blend_{enh}__b{blend}",
            {"processors": ["face_swapper", "face_enhancer"], **swap,
             "face-enhancer-model": enh, "face-enhancer-blend": blend},
        ))
    return out


def stage_mask(args):
    """Mask type / blur / padding. Matters at the jaw and where the cap meets the face."""
    model = (args.models or ["hyperswap_1a_256"])[0]
    boost = COMMON_BOOST if COMMON_BOOST in FACE_SWAPPER_SET[model] else FACE_SWAPPER_SET[model][0]
    swap = {"processors": ["face_swapper"],
            "face-swapper-model": model,
            "face-swapper-pixel-boost": boost,
            "face-swapper-weight": "0.5"}
    out = []
    for types in (["box"], ["box", "occlusion"], ["box", "occlusion", "region"], ["occlusion"]):
        out.append((f"mask_{'-'.join(types)}", {**swap, "face-mask-types": types}))
    for blur in ["0.0", "0.15", "0.3", "0.5", "0.7"]:
        out.append((f"blur_{blur.replace('.', '')}", {**swap, "face-mask-blur": blur}))
    for pad in (["0", "0", "0", "0"], ["8", "8", "8", "8"], ["16", "8", "8", "8"], ["0", "16", "16", "16"]):
        out.append((f"pad_{'-'.join(pad)}", {**swap, "face-mask-padding": pad}))
    return out


def stage_detector(args):
    """Detector model + rotation angles.

    The source portrait sits tilted inside the poster and the target head is
    turned ~30-40 degrees, so detection angle is a real variable here, not a detail.
    """
    model = (args.models or ["hyperswap_1a_256"])[0]
    boost = COMMON_BOOST if COMMON_BOOST in FACE_SWAPPER_SET[model] else FACE_SWAPPER_SET[model][0]
    swap = {"processors": ["face_swapper"],
            "face-swapper-model": model,
            "face-swapper-pixel-boost": boost,
            "face-swapper-weight": "0.5"}
    out = []
    for det in DETECTORS:
        out.append((f"det_{det}", {**swap, "face-detector-model": det, "face-detector-size": "640x640"}))
    for angles in (["0"], ["0", "90", "180", "270"]):
        out.append((f"angles_{'-'.join(angles)}", {**swap, "face-detector-angles": angles}))
    for score in ["0.3", "0.5", "0.7"]:
        out.append((f"score_{score.replace('.', '')}", {**swap, "face-detector-score": score}))
    return out


STAGES = {
    "models":   stage_models,
    "boost":    stage_boost,
    "weight":   stage_weight,
    "enhancer": stage_enhancer,
    "mask":     stage_mask,
    "detector": stage_detector,
}


# ---------------------------------------------------------------------------
# COMMAND BUILDING
# ---------------------------------------------------------------------------
def resolve_source():
    if SOURCE_CROPPED.exists():
        return SOURCE_CROPPED
    print(f"WARNING: {SOURCE_CROPPED.name} not found, falling back to {SOURCE_FULL.name}.\n"
          f"         FaceFusion averages every face it finds in the source - run\n"
          f"         ff_prep_source.py first or identity will be blended.\n", file=sys.stderr)
    return SOURCE_FULL


def flatten(key, value):
    return [f"--{key}"] + ([str(v) for v in value] if isinstance(value, list) else [str(value)])


def build(stage, args):
    steps = STAGES[stage](args)
    outdir = OUT_ROOT / stage
    source = resolve_source()
    job_id = f"sweep_{stage}"

    cmds = [[str(PYTHON), FF, "job-create", job_id]]
    names = []
    manifest = {}
    for name, step in steps:
        merged = {**BASE, **step}
        manifest[f"{name}.png"] = merged          # provenance for the sheet labels
        cmd = [str(PYTHON), FF, "job-add-step", job_id,
               "-s", str(source), "-t", str(TARGET),
               "-o", str(outdir / f"{name}.png")]
        for k, v in merged.items():
            cmd += flatten(k, v)
        cmds.append(cmd)
        names.append(name)

    cmds.append([str(PYTHON), FF, "job-submit", job_id])
    cmds.append([str(PYTHON), FF, "job-run", job_id,
                 "--execution-providers", *(args.provider or available_providers()),
                 "--execution-thread-count", EXECUTION_THREAD_COUNT,
                 "--video-memory-strategy", VIDEO_MEMORY_STRATEGY,
                 "--log-level", LOG_LEVEL])
    return cmds, names, outdir, job_id, manifest


def quote(tok):
    return f'"{tok}"' if " " in tok else tok


# ---------------------------------------------------------------------------
# CONTACT SHEET
# ---------------------------------------------------------------------------
def label_lines(fname, params, score):
    """Every parameter that produced this render, compressed to a few short lines.

    Only the enhancer/mask/detector lines that differ from a plain default are
    spelled out in full, so the tile stays readable at thumbnail size.
    """
    p = params or {}
    g = lambda k, d="": p.get(k, d)
    procs = g("processors", [])

    lines = []
    head = g("face-swapper-model", pathlib.Path(fname).stem)
    lines.append(f"{head}" + (f"   ID {score:.3f}" if isinstance(score, float) else "   ID  n/a"))
    lines.append(f"pb {g('face-swapper-pixel-boost', '-')}  w {g('face-swapper-weight', '-')}")

    if "face_enhancer" in procs:
        lines.append(f"enh {g('face-enhancer-model', '-')} b{g('face-enhancer-blend', '-')}")
    else:
        lines.append("enh none")

    mask = "+".join(g("face-mask-types", ["box"]))
    pad = ",".join(g("face-mask-padding", ["0"] * 4))
    lines.append(f"mask {mask} blur{g('face-mask-blur', '-')} pad{pad}")

    det = f"det {g('face-detector-model', '-')} {g('face-detector-size', '')} s{g('face-detector-score', '-')}"
    angles = g("face-detector-angles")
    if angles:
        det += " a" + "/".join(angles)
    lines.append(det)
    return lines


def contact_sheet(outdir, crop, cols, thumb, manifest=None, scores=None):
    """Grid every render, cropped to the face, with its full parameter set burned in.

    A 1856x2304 poster shrunk to a 320px thumbnail shows nothing useful, so the
    sheet crops to the face box before scaling.
    """
    from PIL import Image, ImageDraw

    files = sorted(p for p in outdir.glob("*.png") if not p.name.startswith("_sheet"))
    if not files:
        print(f"no renders in {outdir}", file=sys.stderr)
        return None

    # prefer the manifest written at execute time; fall back to the rebuilt one
    stored = outdir / "_manifest.json"
    if stored.exists():
        import json
        manifest = {**(json.loads(stored.read_text(encoding="utf-8"))), **(manifest or {})}
    manifest = manifest or {}
    scores = scores or {}

    tiles = []
    for f in files:
        im = Image.open(f).convert("RGB")
        if crop:
            x, y, w, h = crop
            im = im.crop((x, y, min(x + w, im.width), min(y + h, im.height)))
        im.thumbnail((thumb, thumb), Image.LANCZOS)
        tiles.append((f.name, im, label_lines(f.name, manifest.get(f.name), scores.get(f.name))))

    line_h, pad_y = 13, 6
    label_h = pad_y * 2 + line_h * max(len(l) for _, _, l in tiles)
    tw = max(im.width for _, im, _ in tiles)
    th = max(im.height for _, im, _ in tiles) + label_h
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (16, 16, 16))
    draw = ImageDraw.Draw(sheet)

    for i, (name, im, lines) in enumerate(tiles):
        cx, cy = (i % cols) * tw, (i // cols) * th
        sheet.paste(im, (cx, cy))
        ty = cy + im.height + pad_y
        for j, line in enumerate(lines):
            # first line carries the model + identity score -> make it stand out
            fill = (255, 235, 130) if j == 0 else (185, 185, 185)
            draw.text((cx + 4, ty + j * line_h), line[:52], fill=fill)

    path = outdir / f"_sheet_{outdir.name}.png"
    sheet.save(path)
    print(f"contact sheet -> {path}  ({len(tiles)} renders)")
    return path


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=list(STAGES), required=True)
    ap.add_argument("--sweep-dir", default="sweep",
                    help="subject folder under the project root (e.g. sweep-02)")
    ap.add_argument("--models", nargs="*", help="restrict/override the models for this stage")
    ap.add_argument("--provider", nargs="*", help="execution provider; default = whatever onnxruntime offers")
    ap.add_argument("--enhancers", nargs="*", help="restrict the enhancer stage to these models")
    ap.add_argument("--allow-download", action="store_true",
                    help="include enhancers missing from disk (risks aborting the whole job)")
    ap.add_argument("--list", action="store_true", help="print the commands and exit")
    ap.add_argument("--write", action="store_true", help="emit a .bat you can run later")
    ap.add_argument("--execute", action="store_true", help="run it now")
    ap.add_argument("--sheet", action="store_true", help="build the contact sheet from existing renders")
    ap.add_argument("--no-score", action="store_true", help="skip ArcFace identity scoring")
    ap.add_argument("--sheet-crop", default="520,340,460,480",
                    help="x,y,w,h face box in Target.png coords; 'none' for full frame")
    ap.add_argument("--sheet-cols", type=int, default=5)
    ap.add_argument("--sheet-thumb", type=int, default=320)
    args = ap.parse_args()
    use_sweep_dir(args.sweep_dir)

    for p, what in ((PYTHON, "FaceFusion venv python"), (TARGET, "target image")):
        if not p.exists():
            sys.exit(f"ERROR: {what} not found at {p}")

    cmds, names, outdir, job_id, manifest = build(args.stage, args)
    crop = None if args.sheet_crop.lower() == "none" else tuple(int(v) for v in args.sheet_crop.split(","))

    def sheet():
        scores = {}
        if not args.no_score:
            try:
                import ff_identity
                files = sorted(p for p in outdir.glob("*.png") if not p.name.startswith("_sheet"))
                scores = ff_identity.score_paths(resolve_source(), files)
                ranked = sorted((s, n) for n, s in scores.items() if s is not None)
                for s, n in reversed(ranked):
                    print(f"  ID {s:.4f}  {n}")
            except Exception as exc:
                print(f"identity scoring skipped: {exc}", file=sys.stderr)
        contact_sheet(outdir, crop, args.sheet_cols, args.sheet_thumb, manifest, scores)

    if args.sheet:
        sheet()
        return

    print(f"# stage '{args.stage}': {len(names)} renders -> {outdir}")
    print(f"# source: {resolve_source().name}   target: {TARGET.name}\n")

    lines = [" ".join(quote(t) for t in c) for c in cmds]

    if args.write:
        bat = PROJECT / "scripts" / f"run_{args.stage}.bat"
        bat.write_text(
            "@echo off\r\n"
            f'cd /d "{FF_DIR}"\r\n'
            f'if not exist "{outdir}" mkdir "{outdir}"\r\n'
            + "\r\n".join(l + "\r\nif errorlevel 1 exit /b 1" for l in lines) + "\r\n",
            encoding="utf-8")
        print(f"wrote {bat}")
    elif args.execute:
        import json
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        # a stale job of the same name would refuse to be created
        subprocess.run([str(PYTHON), FF, "job-delete", job_id], cwd=FF_DIR,
                       capture_output=True)
        for i, c in enumerate(cmds, 1):
            print(f"[{i}/{len(cmds)}] {' '.join(c[2:5])} ...")
            if subprocess.run(c, cwd=FF_DIR).returncode != 0:
                sys.exit(f"FAILED at step {i}: {' '.join(c)}")
        sheet()
    else:
        print("\n".join(lines))


if __name__ == "__main__":
    main()
