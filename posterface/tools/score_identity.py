#!/usr/bin/env python3
"""
Identity scoring for sweep renders, using FaceFusion's own ArcFace pass.

Rather than reimplement ArcFace's 5-point alignment (which is where naive
similarity scripts quietly go wrong), this drives FaceFusion's face_analyser
in-process: the same detector, landmarker and recogniser the swapper itself uses.

Face.embedding_norm (types.py:35-46) is the L2-normalised 512-d ArcFace vector,
so cosine similarity is just a dot product.

Reading the number:
  ArcFace verification thresholds usually sit near 0.35-0.40 for "same person".
  Swap outputs score much higher because the swapper is optimising this very
  metric - so treat it as a RANKING signal between candidates, not proof of
  likeness. A high score with a face that still reads wrong to you means the
  identity is present but the rendering (lighting, style, resolution) is off.

Usage:
    python ff_identity.py --ref ../sweep/Source_face.jpg --dir ../sweep/out/models
    python ff_identity.py --ref A.jpg --files B.png C.png
"""

import argparse
import json
import pathlib
import sys

FF_DIR = pathlib.Path(r"D:\MyWorld-Sync\011-AI\FaceFusion")
sys.path.insert(0, str(FF_DIR))

import numpy  # noqa: E402


_READY = False


def boot(execution_providers=None):
    """Initialise the minimum FaceFusion global state that face_analyser needs."""
    global _READY
    if _READY:
        return
    from facefusion import state_manager

    try:
        import onnxruntime
        names = {p.replace("ExecutionProvider", "").lower() for p in onnxruntime.get_available_providers()}
        default = ["cuda"] if "cuda" in names else ["cpu"]
    except Exception:
        default = ["cpu"]

    defaults = {
        "execution_providers": execution_providers or default,
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
        "face_detector_margin": [0, 0, 0, 0],   # top/right/bottom/left, not a scalar
        "face_landmarker_model": "2dfan4",
        "face_landmarker_score": 0.5,
    }
    for k, v in defaults.items():
        state_manager.init_item(k, v)
    _READY = True


def embed(path):
    """Return the L2-normalised ArcFace embedding of the largest face in `path`."""
    boot()
    from facefusion.face_analyser import get_many_faces
    from facefusion.vision import read_static_image

    frame = read_static_image(str(path))
    if frame is None:
        return None, "unreadable"

    faces = get_many_faces([frame])
    if not faces:
        return None, "no face detected"

    def area(f):
        x1, y1, x2, y2 = f.bounding_box
        return (x2 - x1) * (y2 - y1)

    face = max(faces, key=area)
    if face.embedding_norm is None:
        return None, "no embedding"
    return numpy.asarray(face.embedding_norm, dtype=numpy.float32), f"{len(faces)} face(s)"


def cosine(a, b):
    return float(numpy.dot(a, b))


def score_paths(ref_path, paths):
    """-> {absolute path str: score or None}. Cosine similarity vs the reference.

    Keyed by FULL PATH, not filename. Batch runs put identically-named candidates
    (inswapper_w065_b0.15.png ...) in one folder per poster, so a filename key
    silently collides and every poster ends up reporting the last one's score.
    """
    ref, note = embed(ref_path)
    if ref is None:
        raise SystemExit(f"ERROR: no usable face in reference {ref_path} ({note})")

    scores = {}
    for p in paths:
        emb, note = embed(p)
        scores[str(pathlib.Path(p).resolve())] = None if emb is None else round(cosine(ref, emb), 4)
    return scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, help="reference face (the cropped source)")
    ap.add_argument("--dir", help="score every .png/.jpg in this folder")
    ap.add_argument("--files", nargs="*", default=[])
    ap.add_argument("--json", help="write results here")
    args = ap.parse_args()

    paths = [pathlib.Path(f) for f in args.files]
    if args.dir:
        d = pathlib.Path(args.dir)
        paths += sorted(p for p in d.iterdir()
                        if p.suffix.lower() in (".png", ".jpg", ".jpeg")
                        and not p.name.startswith("_sheet"))
    if not paths:
        sys.exit("nothing to score")

    scores = score_paths(args.ref, paths)

    # keys are full paths; show just the filename unless two share one
    names = [pathlib.Path(k).name for k in scores]
    ambiguous = len(set(names)) != len(names)
    label = {k: (k if ambiguous else pathlib.Path(k).name) for k in scores}
    width = max(len(v) for v in label.values())
    print(f"\nreference: {pathlib.Path(args.ref).name}\n")
    for key, s in sorted(scores.items(), key=lambda kv: (kv[1] is None, -(kv[1] or 0))):
        print(f"  {label[key]:<{width}}  {'  n/a' if s is None else f'{s:.4f}'}")

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(scores, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
