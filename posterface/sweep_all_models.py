#!/usr/bin/env python3
r"""
=============================================================================
 MARTYR POSTER PIPELINE  -  one file, does everything, picks the winner itself
=============================================================================

WHAT IT DOES
  1. Crops the martyr's face out of the source picture (one face only).
  2. Scores the untouched poster  -> your "before" baseline.
  3. Tries every face-swap model available.
  4. Takes the best safe model and tries every weight x mask-blur combination.
  5. Optionally repaints the face in the poster's art style (stylized posters).
  6. Scores EVERY image it made with ArcFace.
  7. Writes scores.txt (readable) and scores.json (machine readable).
  8. Picks the winner automatically and saves it as FINAL_<name>.png.
  9. Builds a contact sheet showing every candidate with its score.

HOW TO RUN
  Run it with FACEFUSION'S OWN PYTHON, because it borrows FaceFusion's face
  detector and ArcFace model to do the scoring:

      "<FaceFusion>\venv\Scripts\python.exe" ff_pipeline.py

  Either edit the CONFIG block below, or pass paths on the command line:

      ...python.exe ff_pipeline.py --source photo.jpg --target poster.png --out results

WHY IT SCORES INSTEAD OF GUESSING
  The number is cosine similarity between the real face and the rendered face,
  using the same ArcFace model FaceFusion swaps with. An untouched AI poster
  scores ~0.05-0.20. A good swap scores ~0.85-0.91. It turns "looks about right"
  into something you can rank and defend.

  IMPORTANT LIMIT: on posters showing the face from the SIDE, the score can be
  gamed. Some models (ghost_1/ghost_2) rotate the face toward the camera, which
  scores well against a front-facing reference photo but looks badly wrong on a
  profile poster. That is why auto-selection only picks from SAFE_MODELS. The
  other models are still measured and reported, just not allowed to win.
=============================================================================
"""

import argparse
import itertools
import json
import pathlib
import shutil
import subprocess
import sys

# ===========================================================================
#  CONFIG  -  EDIT THESE THREE, OR PASS THEM ON THE COMMAND LINE
# ===========================================================================

SOURCE = r"D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\SourcePictures\Temp\1.jpg"      # the real photo of the person
TARGET = r"D:\posters\Target.png"           # the AI poster to put the face on
OUTPUT_DIR = r"D:\posters\results"          # everything gets written here

# Leave "" to auto-detect. Set it if auto-detect fails.
FACEFUSION_DIR = r""

# "auto" reads it from the poster, or force "photoreal" / "stylized".
#   photoreal -> swap only.
#   stylized  -> swap, then repaint the face in the poster's style (needs ComfyUI).
STYLE = "auto"

# Crop box for the source face as (left, top, right, bottom).
# Leave None to auto-detect the face. Set it if the auto crop grabs the wrong face.
SOURCE_BOX = None

# ---- stylized-only settings (ignored for photoreal posters) ----
COMFY_URL = "http://127.0.0.1:8199"
COMFY_CHECKPOINT = "juggernautXL_ragnarok.safetensors"
STYLE_DENOISE = [0.15, 0.20, 0.25]
STYLE_POSITIVE = ("stylized painterly illustration portrait, soft brush strokes, "
                  "flat shading, poster art")
STYLE_NEGATIVE = ("photograph, photorealistic, 3d render, realistic skin pores, "
                  "blurry, deformed, extra faces, watermark")

# ---- what gets tried ----
# Only these may WIN. Others are measured and reported but cannot be selected,
# because they cheat the score on side-view posters (see docstring).
SAFE_MODELS = ["inswapper_128"]
WEIGHTS = ["0.5", "0.65", "0.8"]
BLURS = ["0.0", "0.15", "0.3"]
PIXEL_BOOST = "512x512"

# ===========================================================================
#  Everything below is the machinery. You should not need to edit it.
# ===========================================================================

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

FF_DIR = None
PY = None
MODELS_DIR = None
_BOOTED = False


def log(msg=""):
    print(msg, flush=True)


# --------------------------------------------------------------------------
#  locate FaceFusion
# --------------------------------------------------------------------------
def find_facefusion(explicit):
    candidates = []
    if explicit:
        candidates.append(pathlib.Path(explicit))
    # the interpreter running us is probably FaceFusion's own venv
    here = pathlib.Path(sys.executable).resolve()
    for parent in here.parents:
        if (parent / "facefusion.py").exists():
            candidates.append(parent)
    for drive in ("D:", "C:", "E:"):
        for name in ("FaceFusion - Copy", "FaceFusion", "facefusion"):
            candidates += [pathlib.Path(f"{drive}/{name}"),
                           pathlib.Path(f"{drive}/Softwares/{name}"),
                           pathlib.Path(f"{drive}/AI/{name}")]
    for c in candidates:
        try:
            if (c / "facefusion.py").exists():
                return c.resolve()
        except OSError:
            continue
    return None


def setup_paths(explicit):
    global FF_DIR, PY, MODELS_DIR
    FF_DIR = find_facefusion(explicit)
    if FF_DIR is None:
        sys.exit(
            "ERROR: could not find FaceFusion.\n"
            "       Set FACEFUSION_DIR at the top of this file, or pass --facefusion <path>.\n"
            "       It must be the folder containing facefusion.py")
    PY = FF_DIR / "venv" / "Scripts" / "python.exe"
    if not PY.exists():
        PY = pathlib.Path(sys.executable)
    MODELS_DIR = FF_DIR / ".assets" / "models"
    log(f"FaceFusion : {FF_DIR}")


def available_models():
    """Only models whose .onnx is on disk. Downloading mid-job aborts the batch."""
    have, missing = [], []
    for m in FACE_SWAPPER_SET:
        (have if (MODELS_DIR / f"{m}.onnx").exists() else missing).append(m)
    return have, missing


def providers():
    try:
        import onnxruntime
        names = {p.replace("ExecutionProvider", "").lower()
                 for p in onnxruntime.get_available_providers()}
        return "cuda" if "cuda" in names else "cpu"
    except Exception:
        return "cpu"


# --------------------------------------------------------------------------
#  scoring  (borrows FaceFusion's detector + ArcFace)
# --------------------------------------------------------------------------
def boot_analyser():
    global _BOOTED
    if _BOOTED:
        return
    sys.path.insert(0, str(FF_DIR))
    from facefusion import state_manager
    defaults = {
        "execution_providers": [providers()],
        "execution_device_ids": ["0"],
        "execution_thread_count": 4,
        "download_providers": ["huggingface", "github"],
        "download_scope": "lite",
        "video_memory_strategy": "strict",
        "system_memory_limit": 0,
        "log_level": "error",
        "face_detector_model": "yolo_face",
        "face_detector_size": "640x640",
        "face_detector_angles": [0],
        "face_detector_score": 0.5,
        "face_detector_margin": [0, 0, 0, 0],   # 4 values, not a scalar
        "face_landmarker_model": "2dfan4",
        "face_landmarker_score": 0.5,
    }
    for k, v in defaults.items():
        state_manager.init_item(k, v)
    _BOOTED = True


def biggest_face(path):
    """-> (Face, n_faces) for the largest face in the image, or (None, 0)."""
    boot_analyser()
    from facefusion.face_analyser import get_many_faces
    from facefusion.vision import read_static_image
    frame = read_static_image(str(path))
    if frame is None:
        return None, 0
    faces = get_many_faces([frame])
    if not faces:
        return None, 0

    def area(f):
        x1, y1, x2, y2 = f.bounding_box
        return (x2 - x1) * (y2 - y1)

    return max(faces, key=area), len(faces)


def embedding(path):
    face, n = biggest_face(path)
    if face is None or face.embedding_norm is None:
        return None, n
    import numpy
    return numpy.asarray(face.embedding_norm, dtype=numpy.float32), n


def score_against(ref_emb, path):
    import numpy
    emb, _ = embedding(path)
    if emb is None:
        return None
    return round(float(numpy.dot(ref_emb, emb)), 4)


# --------------------------------------------------------------------------
#  step 1 - crop the source to exactly one face
# --------------------------------------------------------------------------
def crop_source(src, out_path, box=None):
    """FaceFusion AVERAGES every face it finds in the source. Two faces in the
    picture means two people blended into one identity, before the swap even
    runs. So we cut out exactly one."""
    from PIL import Image
    im = Image.open(src).convert("RGB")

    if box is None:
        face, n = biggest_face(src)
        if face is None:
            sys.exit(f"ERROR: no face found in {src}\n"
                     f"       Set SOURCE_BOX at the top of this file to crop it manually.")
        x1, y1, x2, y2 = [int(v) for v in face.bounding_box]
        w, h = x2 - x1, y2 - y1
        # generous margin so the whole head is included, clamped to the image
        box = (max(0, x1 - int(w * 0.6)), max(0, y1 - int(h * 0.8)),
               min(im.width, x2 + int(w * 0.6)), min(im.height, y2 + int(h * 0.6)))
        if n > 1:
            log(f"  NOTE: {n} faces found in the source; cropped to the largest.")

    im.crop(box).save(out_path, quality=98, subsampling=0)
    log(f"  source face -> {out_path.name}  {box}")
    return out_path


# --------------------------------------------------------------------------
#  running FaceFusion
# --------------------------------------------------------------------------
def run_batch(steps, source, target, provider):
    """steps = [(out_path, {cli args})]. One job, so each model loads once."""
    if not steps:
        return
    job = "ffpipe"
    subprocess.run([str(PY), "facefusion.py", "job-delete", job],
                   cwd=FF_DIR, capture_output=True)
    cmds = [[str(PY), "facefusion.py", "job-create", job]]
    for out, args in steps:
        c = [str(PY), "facefusion.py", "job-add-step", job,
             "-s", str(source), "-t", str(target), "-o", str(out),
             "--face-selector-mode", "one",
             "--face-detector-model", "yolo_face",
             "--output-image-quality", "100",
             "--processors", "face_swapper"]
        for k, v in args.items():
            c += [f"--{k}"] + ([str(x) for x in v] if isinstance(v, list) else [str(v)])
        cmds.append(c)
    cmds.append([str(PY), "facefusion.py", "job-submit", job])
    cmds.append([str(PY), "facefusion.py", "job-run", job,
                 "--execution-providers", provider,
                 "--execution-thread-count", "4",
                 "--log-level", "error"])
    for c in cmds:
        if subprocess.run(c, cwd=FF_DIR).returncode != 0:
            log("  WARNING: a FaceFusion step failed; continuing with what was produced")
            return


# --------------------------------------------------------------------------
#  optional style pass (stylized posters only)
# --------------------------------------------------------------------------
def style_pass(image, outdir, denoises):
    """Repaint the face in the poster's art style via ComfyUI FaceDetailer."""
    import urllib.request, uuid, time, json as _json
    made = []
    try:
        info = _json.load(urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5))
    except Exception:
        log(f"  SKIPPED style pass: ComfyUI is not running at {COMFY_URL}")
        log(r"    start it first:  .venv\Scripts\python.exe main.py --port 8199")
        return made

    comfy_root = None
    for key in ("comfyui_path", "base_directory"):
        v = info.get("system", {}).get(key)
        if v and pathlib.Path(v).exists():
            comfy_root = pathlib.Path(v)
            break
    if comfy_root is None:
        log("  SKIPPED style pass: could not locate ComfyUI's input folder")
        return made

    staged = comfy_root / "input" / f"ffpipe_{uuid.uuid4().hex[:8]}.png"
    staged.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(image, staged)

    for dn in denoises:
        g = {
            "1": {"class_type": "CheckpointLoaderSimple",
                  "inputs": {"ckpt_name": COMFY_CHECKPOINT}},
            "2": {"class_type": "LoadImage", "inputs": {"image": staged.name}},
            "3": {"class_type": "UltralyticsDetectorProvider",
                  "inputs": {"model_name": "bbox/face_yolov8m.pt"}},
            "4": {"class_type": "CLIPTextEncode",
                  "inputs": {"text": STYLE_POSITIVE, "clip": ["1", 1]}},
            "5": {"class_type": "CLIPTextEncode",
                  "inputs": {"text": STYLE_NEGATIVE, "clip": ["1", 1]}},
            "6": {"class_type": "FaceDetailer", "inputs": {
                "image": ["2", 0], "model": ["1", 0], "clip": ["1", 1], "vae": ["1", 2],
                "positive": ["4", 0], "negative": ["5", 0], "bbox_detector": ["3", 0],
                "guide_size": 512, "guide_size_for": True, "max_size": 1024,
                "seed": 1, "steps": 20, "cfg": 6.0,
                "sampler_name": "dpmpp_2m", "scheduler": "karras",
                "denoise": float(dn), "feather": 5, "noise_mask": True,
                "force_inpaint": True, "bbox_threshold": 0.5, "bbox_dilation": 10,
                "bbox_crop_factor": 3.0, "sam_detection_hint": "center-1",
                "sam_dilation": 0, "sam_threshold": 0.93, "sam_bbox_expansion": 0,
                "sam_mask_hint_threshold": 0.7, "sam_mask_hint_use_negative": "False",
                "drop_size": 10, "wildcard": "", "cycle": 1}},
            "7": {"class_type": "SaveImage",
                  "inputs": {"images": ["6", 0], "filename_prefix": f"ffpipe_dn{dn}"}},
        }
        try:
            req = urllib.request.Request(
                f"{COMFY_URL}/prompt",
                data=_json.dumps({"prompt": g, "client_id": uuid.uuid4().hex}).encode(),
                headers={"Content-Type": "application/json"})
            pid = _json.load(urllib.request.urlopen(req, timeout=60))["prompt_id"]
        except Exception as e:
            log(f"  style pass denoise {dn} failed to queue: {e}")
            continue

        for _ in range(600):
            time.sleep(1)
            try:
                h = _json.load(urllib.request.urlopen(f"{COMFY_URL}/history/{pid}", timeout=10))
            except Exception:
                continue
            if pid in h:
                for node in h[pid].get("outputs", {}).values():
                    for im in node.get("images", []):
                        srcf = comfy_root / "output" / im.get("subfolder", "") / im["filename"]
                        if not srcf.exists():
                            srcf = comfy_root / im.get("subfolder", "") / im["filename"]
                        if srcf.exists():
                            dst = outdir / f"style_dn{str(dn).replace('.', '')}.png"
                            shutil.copy(srcf, dst)
                            made.append(dst)
                            log(f"    denoise {dn} -> {dst.name}")
                break
    try:
        staged.unlink()
    except OSError:
        pass
    return made


# --------------------------------------------------------------------------
#  contact sheet
# --------------------------------------------------------------------------
def contact_sheet(entries, target, out_path, cols=5):
    """entries = [(name, path, score)]. Cropped to the face, score burned in."""
    from PIL import Image, ImageDraw
    face, _ = biggest_face(target)
    crop = None
    if face is not None:
        x1, y1, x2, y2 = [int(v) for v in face.bounding_box]
        w, h = x2 - x1, y2 - y1
        crop = (max(0, x1 - w // 2), max(0, y1 - h // 2), w * 2, h * 2)

    tiles = []
    for name, path, sc in entries:
        try:
            im = Image.open(path).convert("RGB")
        except Exception:
            continue
        if crop:
            x, y, w, h = crop
            im = im.crop((x, y, min(x + w, im.width), min(y + h, im.height)))
        im.thumbnail((320, 320), Image.LANCZOS)
        tiles.append((f"{name}  {'n/a' if sc is None else f'{sc:.4f}'}", im))
    if not tiles:
        return None

    tw = max(i.width for _, i in tiles)
    th = max(i.height for _, i in tiles) + 16
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    for i, (lbl, im) in enumerate(tiles):
        cx, cy = (i % cols) * tw, (i // cols) * th
        sheet.paste(im, (cx, cy))
        d.text((cx + 3, cy + im.height + 2), lbl[:44], fill=(255, 235, 130))
    sheet.save(out_path)
    return out_path


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Face swap pipeline with automatic scoring and selection")
    ap.add_argument("--source", default=SOURCE)
    ap.add_argument("--target", default=TARGET)
    ap.add_argument("--out", default=OUTPUT_DIR)
    ap.add_argument("--facefusion", default=FACEFUSION_DIR)
    ap.add_argument("--style", default=STYLE, choices=["auto", "photoreal", "stylized"])
    ap.add_argument("--box", default=None, help="source crop as left,top,right,bottom")
    ap.add_argument("--quick", action="store_true", help="skip the model shootout")
    args = ap.parse_args()

    setup_paths(args.facefusion)

    source = pathlib.Path(args.source)
    target = pathlib.Path(args.target)
    outdir = pathlib.Path(args.out)
    for p, what in ((source, "source photo"), (target, "target poster")):
        if not p.exists():
            sys.exit(f"ERROR: {what} not found: {p}")
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "candidates").mkdir(exist_ok=True)

    prov = providers()
    have, missing = available_models()
    log(f"Provider   : {prov}")
    log(f"Models     : {len(have)} on disk" +
        (f"  |  {len(missing)} not downloaded: {', '.join(missing)}" if missing else ""))
    log("")

    # ---- 1. crop the source ------------------------------------------------
    log("[1/6] Cropping the source face")
    box = tuple(int(v) for v in args.box.split(",")) if args.box else SOURCE_BOX
    face_path = crop_source(source, outdir / "Source_face.jpg", box)
    ref_emb, nref = embedding(face_path)
    if ref_emb is None:
        sys.exit("ERROR: no usable face in the cropped source. Set SOURCE_BOX and retry.")
    if nref > 1:
        log(f"  WARNING: the crop still contains {nref} faces. Identity will be blended.\n"
            f"           Set SOURCE_BOX to isolate one face.")

    # ---- 2. baseline -------------------------------------------------------
    log("\n[2/6] Scoring the untouched poster (your 'before' number)")
    baseline = score_against(ref_emb, target)
    log(f"  baseline = {baseline}")

    results = []          # (name, path, score, kind)
    safe = [m for m in SAFE_MODELS if m in have] or have[:1]
    if not safe:
        sys.exit("ERROR: no swapper models are downloaded.\n"
                 "       Run one swap in the FaceFusion UI first so it fetches a model.")

    # ---- 3. model shootout -------------------------------------------------
    shootout = []
    if not args.quick and len(have) > 1:
        log(f"\n[3/6] Trying all {len(have)} models")
        steps = []
        for m in have:
            pb = PIXEL_BOOST if PIXEL_BOOST in FACE_SWAPPER_SET[m] else FACE_SWAPPER_SET[m][0]
            out = outdir / "candidates" / f"model_{m}.png"
            steps.append((out, {"face-swapper-model": m, "face-swapper-pixel-boost": pb,
                                "face-swapper-weight": "0.5", "face-mask-types": ["box"],
                                "face-mask-blur": "0.3"}))
        run_batch(steps, face_path, target, prov)
        for out, a in steps:
            if out.exists():
                sc = score_against(ref_emb, out)
                shootout.append((a["face-swapper-model"], sc))
                results.append((f"model_{a['face-swapper-model']}", out, sc, "shootout"))
                log(f"  {a['face-swapper-model']:<26} {sc}")
    else:
        log("\n[3/6] Model shootout skipped")

    # ---- 4. refine the safe model -----------------------------------------
    m = safe[0]
    log(f"\n[4/6] Refining {m} across weight x blur")
    pb = PIXEL_BOOST if PIXEL_BOOST in FACE_SWAPPER_SET[m] else FACE_SWAPPER_SET[m][0]
    steps = []
    for w, b in itertools.product(WEIGHTS, BLURS):
        out = outdir / "candidates" / f"tune_w{w.replace('.','')}_b{b.replace('.','')}.png"
        steps.append((out, {"face-swapper-model": m, "face-swapper-pixel-boost": pb,
                            "face-swapper-weight": w, "face-mask-types": ["box"],
                            "face-mask-blur": b}))
    run_batch(steps, face_path, target, prov)
    tuned = []
    for out, a in steps:
        if out.exists():
            sc = score_against(ref_emb, out)
            tuned.append((out, sc))
            results.append((out.stem, out, sc, "tuned"))
            log(f"  weight {a['face-swapper-weight']}  blur {a['face-mask-blur']}  -> {sc}")

    scored_tuned = [(p, s) for p, s in tuned if s is not None]
    if not scored_tuned:
        sys.exit("ERROR: every candidate failed to score. Check the source crop.")
    best_swap, best_swap_score = max(scored_tuned, key=lambda t: t[1])

    # ---- 5. style pass -----------------------------------------------------
    style = args.style
    if style == "auto":
        style = "photoreal" if (baseline or 0) >= 0.12 else "stylized"
        log(f"\n[5/6] Poster looks {style.upper()}  (baseline {baseline})")
    else:
        log(f"\n[5/6] Poster forced to {style.upper()}")

    styled = []
    if style == "stylized":
        log("  A swapped face is a photo sitting on a painting. Repainting it:")
        for p in style_pass(best_swap, outdir / "candidates", STYLE_DENOISE):
            sc = score_against(ref_emb, p)
            styled.append((p, sc))
            results.append((p.stem, p, sc, "styled"))
            log(f"      -> {sc}")
    else:
        log("  Photoreal poster: no style pass (measured to only cost identity here).")

    # ---- 6. choose, write, report -----------------------------------------
    log("\n[6/6] Choosing the winner")
    winner, winner_score, winner_kind = best_swap, best_swap_score, "swap"
    if styled:
        # A styled render always scores LOWER but matches the artwork better.
        # Take the best one that stays within 0.12 of the raw swap.
        ok = [(p, s) for p, s in styled if s is not None and best_swap_score - s <= 0.12]
        if ok:
            p, s = max(ok, key=lambda t: t[1])
            winner, winner_score, winner_kind = p, s, "styled"

    final = outdir / f"FINAL_{target.stem}_{winner_kind}_{winner_score:.4f}.png"
    shutil.copy(winner, final)

    ranked = sorted([r for r in results if r[2] is not None], key=lambda r: -r[2])

    lines = [
        "SCORES  -  higher = more like the real person",
        "=" * 62, "",
        f"source photo : {source.name}",
        f"target poster: {target.name}",
        f"poster type  : {style}",
        "",
        f"BASELINE (poster before any swap) : {baseline}",
        f"WINNER                            : {final.name}",
        f"WINNER SCORE                      : {winner_score:.4f}",
        f"IMPROVEMENT                       : {baseline} -> {winner_score:.4f}",
        "", "-" * 62, "ALL CANDIDATES, BEST FIRST", "-" * 62, "",
    ]
    w = max((len(r[0]) for r in ranked), default=10)
    for name, path, sc, kind in ranked:
        mark = "  <-- WINNER" if path == winner else ""
        lines.append(f"  {name:<{w}}  {sc:.4f}  [{kind}]{mark}")

    if shootout:
        lines += ["", "-" * 62, "MODEL SHOOTOUT", "-" * 62, ""]
        for name, sc in sorted([s for s in shootout if s[1] is not None], key=lambda t: -t[1]):
            note = "" if name in SAFE_MODELS else "   (not eligible to win - see note)"
            lines.append(f"  {name:<26} {sc:.4f}{note}")
        lines += [
            "",
            "  NOTE: only " + ", ".join(SAFE_MODELS) + " may be selected automatically.",
            "  On side-view posters, ghost_1_256 and ghost_2_256 score well by rotating",
            "  the face toward the camera - which looks wrong on the poster. They are",
            "  measured here so you can compare, but they cannot win on score alone.",
        ]

    lines += [
        "", "-" * 62, "HOW TO READ THESE", "-" * 62, "",
        "  under 0.30   failed - the face did not transfer",
        "  0.60 - 0.75  weak - use only if it looks right to you",
        "  0.80 - 0.90  good - normal range for a successful swap",
        "  above 0.90   excellent",
        "",
        "  An untouched AI poster scores about 0.05 - 0.20, so that is your",
        "  starting point, not zero.",
        "",
        "  ALWAYS LOOK AT THE PICTURE. If the number is high but the face looks",
        "  wrong, trust your eyes. The score catches failures; it has no taste.",
    ]
    (outdir / "scores.txt").write_text("\n".join(lines), encoding="utf-8")

    (outdir / "scores.json").write_text(json.dumps({
        "source": str(source), "target": str(target), "style": style,
        "baseline": baseline, "winner": final.name, "winner_score": winner_score,
        "winner_kind": winner_kind,
        "candidates": [{"name": n, "file": str(p), "score": s, "kind": k}
                       for n, p, s, k in ranked],
        "model_shootout": [{"model": n, "score": s} for n, s in shootout],
        "models_missing": missing,
    }, indent=2), encoding="utf-8")

    sheet = contact_sheet(
        [("BEFORE", target, baseline)] + [(n, p, s) for n, p, s, _ in ranked],
        target, outdir / "contact_sheet.png")

    log("")
    log("=" * 62)
    log(f"  BASELINE : {baseline}")
    log(f"  WINNER   : {winner_score:.4f}   ({winner_kind})")
    log(f"  FINAL    : {final}")
    log("=" * 62)
    log(f"  scores.txt    {outdir / 'scores.txt'}")
    log(f"  scores.json   {outdir / 'scores.json'}")
    if sheet:
        log(f"  contact sheet {sheet}")
    log(f"  candidates    {outdir / 'candidates'}  ({len(ranked)} images)")
    if missing:
        log(f"\n  {len(missing)} models not tested (not downloaded): {', '.join(missing)}")


if __name__ == "__main__":
    main()
