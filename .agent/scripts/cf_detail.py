#!/usr/bin/env python3
"""
FaceDetailer redraw pass over a FaceFusion swap result, driven through ComfyUI's HTTP API.

Why this stage exists: FaceFusion transfers identity but paints it in the SOURCE's
lighting and resolution. On a poster the result reads as a sticker - the face is
right but the render doesn't belong to the image. FaceDetailer crops the face,
re-renders it at low denoise with the poster's own checkpoint, and stitches it
back, so grain, light and style become native. Denoise is the whole game:
  ~0.15-0.25  restyle only, identity untouched
  ~0.30-0.45  fixes a clear style/lighting clash, starts drifting off likeness
  >0.50       the checkpoint invents its own face - identity is lost

This talks to ComfyUI over plain HTTP with stdlib only, so run it with FaceFusion's
venv python and identity scoring comes along for free:

  "D:\\Softwares\\FaceFusion - Copy\\venv\\Scripts\\python.exe" cf_detail.py --denoise 0.2 0.3 0.4

Requires ComfyUI running:
  cd "D:\\Comfy-Desktop\\ComfyUI-Installs\\ComfyUI\\ComfyUI"
  .venv\\Scripts\\python.exe -u main.py --port 8199
"""

import argparse
import json
import pathlib
import shutil
import sys
import time
import urllib.parse
import urllib.request

SERVER = "127.0.0.1:8199"

COMFY_ROOT = pathlib.Path(r"D:\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI")
COMFY_INPUT = COMFY_ROOT / "input"

PROJECT = pathlib.Path(r"D:\01-AI\002-MertydomPosters")
SWEEP = PROJECT / "sweep"
DEFAULT_IMAGE = SWEEP / "out" / "best" / "best_noenh.png"
SOURCE_FACE = SWEEP / "Source_face.jpg"
OUTDIR = SWEEP / "out" / "detail"


def use_sweep_dir(name):
    """Repoint at a different subject folder (sweep, sweep-02, sweep-03, ...)."""
    global SWEEP, SOURCE_FACE, OUTDIR
    SWEEP = PROJECT / name
    SOURCE_FACE = SWEEP / "Source_face.jpg"
    OUTDIR = SWEEP / "out" / "detail"

CHECKPOINT = "juggernautXL_ragnarok.safetensors"
DETECTOR = "bbox/face_yolov8m.pt"

# Describe the RENDER, not the person. The identity is already in the pixels; the
# prompt's job is only to tell the checkpoint what kind of image this is, so it
# restyles rather than reinvents.
POSITIVE = ("photorealistic portrait photograph of a naval officer, white dress uniform, "
            "peaked cap, warm golden rim lighting, sharp focus, natural skin texture, "
            "detailed eyes, film grain, shallow depth of field")
NEGATIVE = ("cartoon, anime, illustration, painting, 3d render, cgi, plastic skin, "
            "airbrushed, waxy, blurry, deformed, extra faces, watermark, text")


def post(path, payload):
    req = urllib.request.Request(f"http://{SERVER}{path}",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def get(path):
    return json.loads(urllib.request.urlopen(f"http://{SERVER}{path}", timeout=60).read())


def build_graph(image_name, denoise, seed, steps, cfg, checkpoint, positive, negative,
                guide_size, max_size, feather, crop_factor):
    """API-format graph: load -> detect -> FaceDetailer -> save."""
    return {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": checkpoint}},
        "2": {"class_type": "LoadImage",
              "inputs": {"image": image_name, "upload": "image"}},
        "3": {"class_type": "UltralyticsDetectorProvider",
              "inputs": {"model_name": DETECTOR}},
        "4": {"class_type": "CLIPTextEncode",
              "inputs": {"text": positive, "clip": ["1", 1]}},
        "5": {"class_type": "CLIPTextEncode",
              "inputs": {"text": negative, "clip": ["1", 1]}},
        "6": {"class_type": "FaceDetailer",
              "inputs": {
                  "image": ["2", 0], "model": ["1", 0], "clip": ["1", 1], "vae": ["1", 2],
                  "positive": ["4", 0], "negative": ["5", 0], "bbox_detector": ["3", 0],
                  "guide_size": guide_size, "guide_size_for": True, "max_size": max_size,
                  "seed": seed, "steps": steps, "cfg": cfg,
                  "sampler_name": "dpmpp_2m", "scheduler": "karras",
                  "denoise": denoise, "feather": feather,
                  "noise_mask": True, "force_inpaint": True,
                  "bbox_threshold": 0.50, "bbox_dilation": 10, "bbox_crop_factor": crop_factor,
                  "sam_detection_hint": "center-1", "sam_dilation": 0, "sam_threshold": 0.93,
                  "sam_bbox_expansion": 0, "sam_mask_hint_threshold": 0.70,
                  "sam_mask_hint_use_negative": "False",
                  "drop_size": 10, "wildcard": "", "cycle": 1,
              }},
        "7": {"class_type": "SaveImage",
              "inputs": {"images": ["6", 0], "filename_prefix": "detail"}},
    }


def run(graph, timeout=1800):
    pid = post("/prompt", {"prompt": graph})["prompt_id"]
    start = time.time()
    while True:
        hist = get(f"/history/{pid}")
        if pid in hist:
            entry = hist[pid]
            status = entry.get("status", {})
            if status.get("status_str") == "error" or not status.get("completed", True):
                msgs = status.get("messages", [])
                raise RuntimeError(f"ComfyUI error: {json.dumps(msgs)[:600]}")
            for node in entry.get("outputs", {}).values():
                for img in node.get("images", []):
                    return img
            raise RuntimeError("prompt finished but produced no image")
        if time.time() - start > timeout:
            raise TimeoutError(f"prompt {pid} exceeded {timeout}s")
        time.sleep(2)


def fetch(img, dest):
    q = urllib.parse.urlencode({"filename": img["filename"],
                                "subfolder": img.get("subfolder", ""),
                                "type": img.get("type", "output")})
    data = urllib.request.urlopen(f"http://{SERVER}/view?{q}", timeout=120).read()
    dest.write_bytes(data)
    return dest


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sweep-dir", help="subject folder under the project root (e.g. sweep-03)")
    ap.add_argument("--image", default=None)
    ap.add_argument("--denoise", nargs="*", type=float, default=[0.15, 0.25, 0.35, 0.45])
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--steps", type=int, default=25)
    ap.add_argument("--cfg", type=float, default=6.0)
    ap.add_argument("--checkpoint", default=CHECKPOINT)
    ap.add_argument("--positive", default=POSITIVE)
    ap.add_argument("--negative", default=NEGATIVE)
    ap.add_argument("--guide-size", type=float, default=768)
    ap.add_argument("--max-size", type=float, default=1024)
    ap.add_argument("--feather", type=int, default=5)
    ap.add_argument("--crop-factor", type=float, default=3.0)
    ap.add_argument("--no-score", action="store_true")
    args = ap.parse_args()

    if args.sweep_dir:
        use_sweep_dir(args.sweep_dir)
    src = pathlib.Path(args.image) if args.image else DEFAULT_IMAGE
    if not src.exists():
        sys.exit(f"ERROR: input image not found: {src}")
    try:
        get("/system_stats")
    except Exception:
        sys.exit(f"ERROR: ComfyUI not reachable at {SERVER}. Start it first (see module docstring).")

    # LoadImage resolves names relative to ComfyUI's input folder
    staged = COMFY_INPUT / src.name
    if not staged.exists() or staged.stat().st_mtime < src.stat().st_mtime:
        shutil.copy2(src, staged)

    OUTDIR.mkdir(parents=True, exist_ok=True)
    results = []
    for dn in args.denoise:
        graph = build_graph(src.name, dn, args.seed, args.steps, args.cfg,
                            args.checkpoint, args.positive, args.negative,
                            args.guide_size, args.max_size, args.feather, args.crop_factor)
        t = time.time()
        print(f"denoise {dn:.2f} ... ", end="", flush=True)
        try:
            img = run(graph)
        except Exception as exc:
            print(f"FAILED: {exc}")
            continue
        dest = OUTDIR / f"detail_dn{str(dn).replace('.', '')}.png"
        fetch(img, dest)
        print(f"{time.time() - t:.0f}s -> {dest.name}")
        results.append(dest)

    if not results:
        sys.exit("no renders produced")

    if not args.no_score:
        try:
            sys.path.insert(0, str(pathlib.Path(__file__).parent))
            import ff_identity
            print("\nidentity vs Source_face.jpg (pre-detail input included as baseline):")
            scores = ff_identity.score_paths(SOURCE_FACE, [src] + results)
            for name, s in sorted(scores.items(), key=lambda kv: -(kv[1] or 0)):
                print(f"  {'n/a' if s is None else f'{s:.4f}'}  {name}")
        except Exception as exc:
            print(f"identity scoring skipped: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
