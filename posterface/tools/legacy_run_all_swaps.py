#!/usr/bin/env python3
"""
Batch face swap: one source face → all target images in Raw Pictures.

Uses FaceFusion headless mode with deep_swapper (elon_musk_224).
Outputs go into a new folder per target image.

Usage:
    D:/MyWorld-Sync/011-AI/FaceFusion/venv/Scripts/python.exe run_all_swaps.py
"""

import pathlib
import subprocess
import sys
import json
import time

# ── Paths ───────────────────────────────────────────────────────────────
FF_DIR = pathlib.Path(r"D:\MyWorld-Sync\011-AI\FaceFusion")
FF_VENV_PYTHON = FF_DIR / "venv_311" / "Scripts" / "python.exe"
SOURCE_FACE = pathlib.Path(r"D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\Finial\پهپاد - امیر دریادار - دانا\Source_face.jpg")
RAW_PICTURES = pathlib.Path(r"D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\Raw Pictures")
OUTPUT_BASE = pathlib.Path(r"D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\Finial\batch_swaps")

# ── Verify source exists ────────────────────────────────────────────────
if not SOURCE_FACE.exists():
    sys.exit(f"ERROR: source face not found: {SOURCE_FACE}")

print(f"Source face: {SOURCE_FACE.name} ({SOURCE_FACE.stat().st_size / 1024:.0f} KB)")
target_files = list(RAW_PICTURES.glob("*.png")) + list(RAW_PICTURES.glob("*.jpg"))
print(f"Target images: {len(target_files)} found")
print(f"Output base: {OUTPUT_BASE}")
print()

# ── Build target list ───────────────────────────────────────────────────
targets = sorted([
    *RAW_PICTURES.glob("*.png"),
    *RAW_PICTURES.glob("*.jpg"),
])

if not targets:
    sys.exit("ERROR: no .png or .jpg files in Raw Pictures")

print(f"Processing {len(targets)} target images...\n")

# ── Run FaceFusion headless for each target ─────────────────────────────
for i, target in enumerate(targets, 1):
    job_name = f"{target.stem}"
    output_dir = OUTPUT_BASE / job_name
    output_file = output_dir / "final.png"
    
    print(f"[{i}/{len(targets)}] {target.name} → {output_dir.name}/")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build FaceFusion headless command (uses facefusion.py headless-run)
    cmd = [
        str(FF_VENV_PYTHON), "facefusion.py", "headless-run",
        "--temp-frame-format", "png",
        "--output-image-quality", "100",
        "--output-image-scale", "1.0",
        "-s", str(SOURCE_FACE),
        "-t", str(target),
        "--output-path", str(output_file),
        "--processors", "deep_swapper",
        "--face-enhancer-model", "gfpgan_1.4",
        "--face-enhancer-blend", "80",
        "--face-detector-model", "yolo_face",
        "--face-detector-size", "640x640",
        "--face-detector-score", "0.5",
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(FF_DIR),
            capture_output=True,
            text=True,
            timeout=300  # 5 min per image
        )
        
        if result.returncode == 0 and output_file.exists():
            size_kb = output_file.stat().st_size / 1024
            print(f"   ✓ Done ({size_kb:.0f} KB)")
        else:
            stderr = result.stderr[-500:] if result.stderr else "no error output"
            print(f"   ✗ FAILED: {stderr}")
            
    except subprocess.TimeoutExpired:
        print(f"   ✗ TIMEOUT (>5 min)")
    except Exception as exc:
        print(f"   ✗ ERROR: {exc}")
    
    # Small delay between jobs to avoid GPU memory issues
    if i < len(targets):
        time.sleep(3)

print(f"\n✅ All done! Results in: {OUTPUT_BASE}")
