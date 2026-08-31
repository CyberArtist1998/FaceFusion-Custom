#!/usr/bin/env python3
r"""
POSTER FACE TOOL - standalone CLI

Puts a real person's face onto an AI-generated poster, scores every attempt
against the real photo, and picks the best one automatically.

Designed to be frozen with PyInstaller so colleagues need no Python:

    PosterFace.exe --source photo.jpg --target poster.png --out results

Runs the swap IN-PROCESS through FaceFusion's own modules, so output is
identical to FaceFusion itself - no reimplementation, no drift.
"""

import argparse
import itertools
import json
import os
import pathlib
import shutil
import sys
import time

# --------------------------------------------------------------------------
# make the bundled/neighbouring facefusion package importable
# --------------------------------------------------------------------------
FROZEN = getattr(sys, "frozen", False)
BASE = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).parent)).resolve()
APP_DIR = pathlib.Path(sys.executable).parent if FROZEN else pathlib.Path(__file__).parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

# ---- tuning (measured across 4 posters; see REPORT.md) --------------------
SAFE_MODELS = ["inswapper_128"]      # only these may be auto-selected
FALLBACK_MODELS = ["ghost_1_256", "ghost_2_256", "blendswap_256", "hyperswap_1a_256"]
WEIGHTS = ["0.5", "0.65", "0.8"]
BLURS = ["0.0", "0.15", "0.3"]
PIXEL_BOOST = "512x512"

SCORE_HELP = """
  under 0.30   failed - the face did not transfer
  0.60 - 0.75  weak - use only if it looks right to you
  0.80 - 0.90  good - normal range for a successful swap
  above 0.90   excellent

  An untouched AI poster scores about 0.05 - 0.20, so that is your starting
  point, not zero.

  ALWAYS LOOK AT THE PICTURE. If the number is high but the face looks wrong,
  trust your eyes. The score catches failures; it has no taste.
"""


# --------------------------------------------------------------------------
# progress bar
# --------------------------------------------------------------------------
class Progress:
    def __init__(self, total, width=34, quiet=False):
        self.total, self.width, self.quiet = total, width, quiet
        self.n, self.t0, self.label = 0, time.time(), ""

    def step(self, label):
        self.n += 1
        self.label = label
        self.draw()

    def draw(self, done=False):
        if self.quiet:
            return
        frac = min(self.n / max(self.total, 1), 1.0)
        filled = int(self.width * frac)
        bar = "#" * filled + "-" * (self.width - filled)
        el = time.time() - self.t0
        line = f"\r  [{bar}] {int(frac*100):3d}%  {el:5.1f}s  {self.label[:38]:<38}"
        sys.stdout.write(line)
        sys.stdout.flush()
        if done:
            sys.stdout.write("\n")

    def finish(self):
        self.n = self.total
        self.label = "done"
        self.draw(done=True)


def say(msg=""):
    print(msg, flush=True)


def head(msg):
    say("")
    say(msg)
    say("-" * max(len(msg), 20))


# --------------------------------------------------------------------------
# facefusion bootstrap
# --------------------------------------------------------------------------
_READY = False


def providers():
    try:
        import onnxruntime
        names = {p.replace("ExecutionProvider", "").lower()
                 for p in onnxruntime.get_available_providers()}
        return "cuda" if "cuda" in names else "cpu"
    except Exception:
        return "cpu"


def boot():
    """Initialise the FaceFusion global state this tool relies on."""
    global _READY
    if _READY:
        return
    from facefusion import state_manager
    for k, v in {
        "execution_providers": [providers()],
        "execution_device_ids": ["0"],
        "execution_thread_count": 4,
        "download_providers": ["huggingface", "github"],
        "download_scope": "lite",
        "video_memory_strategy": "strict",
        "system_memory_limit": 0,
        "log_level": "error",
        # detection / landmarking
        "face_detector_model": "yolo_face",
        "face_detector_size": "640x640",
        "face_detector_angles": [0],
        "face_detector_score": 0.5,
        "face_detector_margin": [0, 0, 0, 0],   # 4 values, not a scalar
        "face_landmarker_model": "2dfan4",
        "face_landmarker_score": 0.5,
        # swapping
        "face_swapper_model": SAFE_MODELS[0],
        "face_swapper_pixel_boost": PIXEL_BOOST,
        "face_swapper_weight": 0.65,
        # masking
        "face_mask_types": ["box"],
        "face_mask_blur": 0.15,
        "face_mask_padding": [0, 0, 0, 0],
        "face_occluder_model": "xseg_1",
        "face_parser_model": "bisenet_resnet_34",
        "face_mask_areas": [],
        "face_mask_regions": [],
    }.items():
        state_manager.init_item(k, v)
    _READY = True


def models_dir():
    from facefusion.filesystem import resolve_relative_path
    return pathlib.Path(resolve_relative_path("../.assets/models"))


def have_model(name):
    return (models_dir() / f"{name}.onnx").exists()


# --------------------------------------------------------------------------
# image + face helpers
# --------------------------------------------------------------------------
def read_img(path):
    from facefusion.vision import read_static_image
    return read_static_image(str(path))


def write_img(path, frame):
    import cv2
    cv2.imwrite(str(path), frame)


def faces_in(frame):
    from facefusion.face_analyser import get_many_faces
    return get_many_faces([frame]) if frame is not None else []


def biggest(faces):
    if not faces:
        return None

    def area(f):
        x1, y1, x2, y2 = f.bounding_box
        return (x2 - x1) * (y2 - y1)

    return max(faces, key=area)


def embed_of(face):
    if face is None or face.embedding_norm is None:
        return None
    import numpy
    return numpy.asarray(face.embedding_norm, dtype=numpy.float32)


def score(ref, frame):
    """Cosine similarity of the largest face in `frame` against `ref`."""
    import numpy
    e = embed_of(biggest(faces_in(frame)))
    return None if e is None else round(float(numpy.dot(ref, e)), 4)


# --------------------------------------------------------------------------
def crop_source(src_frame, box=None):
    """FaceFusion averages EVERY face it finds in the source, so two faces in
    the picture blend two people into one identity. Cut out exactly one."""
    fs = faces_in(src_frame)
    if not fs:
        return None, 0
    f = biggest(fs)
    h, w = src_frame.shape[:2]
    if box is None:
        x1, y1, x2, y2 = [int(v) for v in f.bounding_box]
        bw, bh = x2 - x1, y2 - y1
        box = (max(0, x1 - int(bw * .6)), max(0, y1 - int(bh * .8)),
               min(w, x2 + int(bw * .6)), min(h, y2 + int(bh * .6)))
    l, t, r, b = box
    return src_frame[t:b, l:r].copy(), len(fs)


def do_swap(src_face, tgt_frame, model, weight, blur):
    """One swap, in-process, using FaceFusion's own swap_face()."""
    from facefusion import state_manager
    from facefusion.processors.modules.face_swapper import core as fs_core
    state_manager.set_item("face_swapper_model", model)
    state_manager.set_item("face_swapper_weight", float(weight))
    state_manager.set_item("face_mask_blur", float(blur))
    pb = PIXEL_BOOST
    try:
        from facefusion.processors.modules.face_swapper import choices as fs_choices
        if pb not in fs_choices.face_swapper_set.get(model, []):
            pb = fs_choices.face_swapper_set[model][0]
    except Exception:
        pass
    state_manager.set_item("face_swapper_pixel_boost", pb)
    fs_core.clear_inference_pool()
    tgt_face = biggest(faces_in(tgt_frame))
    if tgt_face is None:
        return None
    return fs_core.swap_face(src_face, tgt_face, tgt_frame)


# --------------------------------------------------------------------------
def comparison(src_crop, before, after, ref, out_path, scores):
    """source | poster before | poster after, cropped to the face."""
    import cv2, numpy
    f = biggest(faces_in(before))
    panels = []

    def face_crop(frame):
        if f is None:
            return frame
        x1, y1, x2, y2 = [int(v) for v in f.bounding_box]
        w, h = x2 - x1, y2 - y1
        H, W = frame.shape[:2]
        return frame[max(0, y1 - h // 2):min(H, y2 + h // 2),
                     max(0, x1 - w // 2):min(W, x2 + w // 2)]

    for label, img in (("SOURCE (real)", src_crop),
                       (f"BEFORE  {scores[0]}", face_crop(before)),
                       (f"AFTER   {scores[1]}", face_crop(after))):
        if img is None or img.size == 0:
            continue
        h = 420
        scale = h / img.shape[0]
        im = cv2.resize(img, (max(1, int(img.shape[1] * scale)), h), interpolation=cv2.INTER_AREA)
        pad = numpy.full((im.shape[0] + 26, im.shape[1], 3), 16, numpy.uint8)
        pad[:im.shape[0]] = im
        cv2.putText(pad, label, (5, im.shape[0] + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (130, 235, 255), 1, cv2.LINE_AA)
        panels.append(pad)
    if not panels:
        return None
    H = max(p.shape[0] for p in panels)
    panels = [numpy.pad(p, ((0, H - p.shape[0]), (0, 0), (0, 0)), constant_values=16) for p in panels]
    cv2.imwrite(str(out_path), numpy.hstack(panels))
    return out_path


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        prog="PosterFace",
        description="Put a real face on an AI poster, score every attempt, pick the best.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="example:\n  PosterFace.exe -s photo.jpg -t poster.png -o results\n")
    ap.add_argument("-s", "--source", required=True, help="the real photo of the person")
    ap.add_argument("-t", "--target", required=True, help="the AI poster")
    ap.add_argument("-o", "--out", required=True, help="output folder")
    ap.add_argument("--box", help="source crop as left,top,right,bottom (if auto-crop grabs the wrong face)")
    ap.add_argument("--quick", action="store_true", help="skip the all-models comparison")
    ap.add_argument("--keep", action="store_true", help="keep every candidate image")
    ap.add_argument("--quiet", action="store_true", help="no progress bar")
    args = ap.parse_args()

    src_p, tgt_p = pathlib.Path(args.source), pathlib.Path(args.target)
    outdir = pathlib.Path(args.out)
    for p, what in ((src_p, "source photo"), (tgt_p, "target poster")):
        if not p.exists():
            say(f"ERROR: {what} not found: {p}")
            return 2
    outdir.mkdir(parents=True, exist_ok=True)
    cand_dir = outdir / "candidates"
    cand_dir.mkdir(exist_ok=True)

    say("=" * 60)
    say("  POSTER FACE TOOL")
    say("=" * 60)
    say(f"  source : {src_p.name}")
    say(f"  target : {tgt_p.name}")
    say(f"  output : {outdir}")

    t_start = time.time()
    boot()
    say(f"  device : {providers().upper()}")

    models = [m for m in SAFE_MODELS + FALLBACK_MODELS if have_model(m)]
    if not models:
        say("\nERROR: no swap models found next to the program.")
        say(f"       expected .onnx files in: {models_dir()}")
        return 2
    safe = [m for m in SAFE_MODELS if m in models] or models[:1]
    shoot = [] if args.quick else models

    # ---- source ----------------------------------------------------------
    head("[1/5] Reading the source photo")
    bar = Progress(1, quiet=args.quiet)
    bar.step("detecting and cropping the face")
    src_frame = read_img(src_p)
    if src_frame is None:
        say("\nERROR: could not read the source photo.")
        return 2
    box = tuple(int(v) for v in args.box.split(",")) if args.box else None
    crop, nfaces = crop_source(src_frame, box)
    if crop is None:
        say("\nERROR: no face found in the source photo.")
        say("       Try --box left,top,right,bottom to crop it manually.")
        return 2
    write_img(outdir / "Source_face.jpg", crop)
    src_face = biggest(faces_in(crop))
    ref = embed_of(src_face)
    if ref is None:
        say("\nERROR: the cropped source has no usable face.")
        return 2
    bar.finish()
    say(f"  found {nfaces} face(s) in the source; using the largest")
    if nfaces > 1:
        say("  NOTE: extra faces were cropped away (they would blend identities)")

    # ---- baseline --------------------------------------------------------
    head("[2/5] Scoring the untouched poster")
    tgt_frame = read_img(tgt_p)
    if tgt_frame is None:
        say("ERROR: could not read the target poster.")
        return 2
    baseline = score(ref, tgt_frame)
    say(f"  baseline = {baseline}   (this is your 'before' number)")
    if baseline is None:
        say("  ERROR: no face detected in the poster.")
        return 2

    results = []   # (name, score, path, kind)

    # ---- model comparison ------------------------------------------------
    shootout = []
    if shoot:
        head(f"[3/5] Comparing {len(shoot)} swap models")
        bar = Progress(len(shoot), quiet=args.quiet)
        for m in shoot:
            bar.step(m)
            try:
                out = do_swap(src_face, tgt_frame, m, 0.5, 0.3)
            except Exception as e:
                say(f"\n  {m}: failed ({type(e).__name__})")
                continue
            if out is None:
                continue
            sc = score(ref, out)
            shootout.append((m, sc))
            p = cand_dir / f"model_{m}.png"
            write_img(p, out)
            results.append((f"model_{m}", sc, p, "shootout"))
        bar.finish()
        for m, sc in sorted([s for s in shootout if s[1] is not None], key=lambda t: -t[1]):
            tag = "" if m in SAFE_MODELS else "  (not eligible to win)"
            say(f"    {m:<24} {sc:.4f}{tag}")
    else:
        head("[3/5] Model comparison skipped (--quick)")

    # ---- tuning ----------------------------------------------------------
    head(f"[4/5] Tuning {safe[0]}  ({len(WEIGHTS)*len(BLURS)} combinations)")
    bar = Progress(len(WEIGHTS) * len(BLURS), quiet=args.quiet)
    tuned = []
    for w, b in itertools.product(WEIGHTS, BLURS):
        bar.step(f"weight {w}  blur {b}")
        try:
            out = do_swap(src_face, tgt_frame, safe[0], w, b)
        except Exception as e:
            say(f"\n  weight {w} blur {b}: failed ({type(e).__name__})")
            continue
        if out is None:
            continue
        sc = score(ref, out)
        p = cand_dir / f"tune_w{w.replace('.','')}_b{b.replace('.','')}.png"
        write_img(p, out)
        tuned.append((p, sc))
        results.append((p.stem, sc, p, "tuned"))
    bar.finish()

    ok = [(p, s) for p, s in tuned if s is not None]
    if not ok:
        say("ERROR: every attempt failed to score.")
        return 2
    best_path, best_score = max(ok, key=lambda t: t[1])

    # ---- results ---------------------------------------------------------
    head("[5/5] Result")
    final = outdir / f"FINAL_{tgt_p.stem}_{best_score:.4f}.png"
    shutil.copy(best_path, final)

    after = read_img(final)
    cmp_path = comparison(crop, tgt_frame, after, ref,
                          outdir / "comparison.png", (baseline, f"{best_score:.4f}"))

    ranked = sorted([r for r in results if r[1] is not None], key=lambda r: -r[1])
    w_ = max((len(r[0]) for r in ranked), default=10)
    lines = ["SCORES  -  higher = more like the real person", "=" * 62, "",
             f"source photo : {src_p.name}",
             f"target poster: {tgt_p.name}", "",
             f"BASELINE (before any swap) : {baseline}",
             f"WINNER                     : {final.name}",
             f"WINNER SCORE               : {best_score:.4f}",
             f"IMPROVEMENT                : {baseline}  ->  {best_score:.4f}",
             "", "-" * 62, "ALL ATTEMPTS, BEST FIRST", "-" * 62, ""]
    for n, s, p, k in ranked:
        lines.append(f"  {n:<{w_}}  {s:.4f}  [{k}]" + ("   <-- WINNER" if p == best_path else ""))
    if shootout:
        lines += ["", "-" * 62, "MODEL COMPARISON", "-" * 62, ""]
        for m, s in sorted([x for x in shootout if x[1] is not None], key=lambda t: -t[1]):
            lines.append(f"  {m:<24} {s:.4f}" + ("" if m in SAFE_MODELS else "   (not eligible to win)"))
        lines += ["", "  Only " + ", ".join(SAFE_MODELS) + " may be picked automatically.",
                  "  On side-view posters ghost_1_256 and ghost_2_256 score well by",
                  "  rotating the face toward the camera, which looks wrong on the",
                  "  poster. They are measured so you can compare, but cannot win."]
    lines += ["", "-" * 62, "HOW TO READ THESE", "-" * 62, SCORE_HELP]
    (outdir / "scores.txt").write_text("\n".join(lines), encoding="utf-8")
    (outdir / "scores.json").write_text(json.dumps({
        "source": str(src_p), "target": str(tgt_p), "baseline": baseline,
        "winner": final.name, "winner_score": best_score,
        "attempts": [{"name": n, "score": s, "file": str(p), "kind": k} for n, s, p, k in ranked],
        "model_comparison": [{"model": m, "score": s} for m, s in shootout],
    }, indent=2), encoding="utf-8")

    if not args.keep:
        shutil.rmtree(cand_dir, ignore_errors=True)

    say("")
    say("=" * 60)
    say(f"  BEFORE : {baseline}")
    say(f"  AFTER  : {best_score:.4f}")
    say(f"  TIME   : {time.time() - t_start:.0f}s")
    say("=" * 60)
    say(f"  final image  : {final}")
    if cmp_path:
        say(f"  comparison   : {cmp_path}")
    say(f"  scores       : {outdir / 'scores.txt'}")
    if args.keep:
        say(f"  candidates   : {cand_dir}")
    say("")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        say("\ncancelled")
        sys.exit(130)
