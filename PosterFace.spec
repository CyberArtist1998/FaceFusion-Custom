# -*- mode: python ; coding: utf-8 -*-
r"""
PyInstaller spec for PosterFace.

Build:
    venv_311\Scripts\python.exe -m PyInstaller PosterFace.spec --noconfirm

Output:
    dist\PosterFace\PosterFace.exe          <- give colleagues this whole folder

WHY ONEDIR AND NOT ONEFILE
  The models are ~800 MB. A --onefile exe unpacks everything to a temp folder
  on EVERY run, which would add a minute of startup each time. onedir starts
  instantly and the models sit on disk once.

WHERE THE MODELS GO
  facefusion/filesystem.py resolves models with
      abspath(join(dirname(__file__), '../.assets/models'))
  In a onedir build the package lands at _internal/facefusion/, so that path
  resolves to _internal/.assets/models  -- which is exactly where the datas
  entry below puts them. Do not change that destination.

WHICH MODELS ARE BUNDLED
  Only the four needed for the winning pipeline (~800 MB):
      yoloface_8n          find the face
      2dfan4               landmarks for alignment
      arcface_w600k_r50    identity + scoring
      inswapper_128        the swap
  The extra comparison models (ghost/blendswap/hyperswap) add ~3.2 GB and only
  populate the "model comparison" table. poster_cli.py skips any model that is
  not present, so leaving them out degrades gracefully. Add them to
  EXTRA_MODELS below if you want the full comparison in the exe.
"""

import pathlib

PROJECT = pathlib.Path(SPECPATH)
MODELS = PROJECT / ".assets" / "models"

CORE_MODELS = [
    "yoloface_8n",          # find the face
    "fan_68_5",             # 5 -> 68 landmark estimate (create_faces needs it)
    "2dfan4",               # refined 68-point landmarks
    "fairface",             # classify_face() is called unconditionally
    "arcface_w600k_r50",    # identity embedding + scoring
    "inswapper_128",        # the swap
]
EXTRA_MODELS = []          # e.g. ["ghost_1_256", "ghost_2_256", "hyperswap_1a_256"]

model_datas = []
for name in CORE_MODELS + EXTRA_MODELS:
    for ext in (".onnx", ".hash"):
        f = MODELS / f"{name}{ext}"
        if f.exists():
            model_datas.append((str(f), ".assets/models"))

hidden = [
    # facefusion/translator.py does importlib.import_module(mod + '.locales')
    # and swallows the ImportError, which leaves an empty pool that later
    # crashes with "'NoneType' object has no attribute 'get'". PyInstaller
    # cannot see a dynamic import, so these must be listed by hand.
    "facefusion.locales",
    "facefusion.processors.modules.face_swapper.locales",
    # imported dynamically or via string lookup inside facefusion
    "facefusion.processors.modules.face_swapper.core",
    "facefusion.processors.modules.face_swapper.choices",
    "facefusion.face_analyser",
    "facefusion.face_detector",
    "facefusion.face_landmarker",
    "facefusion.face_recognizer",
    "facefusion.face_classifier",
    "facefusion.face_masker",
    "facefusion.face_helper",
    "facefusion.vision",
    "facefusion.filesystem",
    "facefusion.state_manager",
    "onnxruntime",
    "cv2",
    "numpy",
]

a = Analysis(
    ["poster_cli.py"],
    pathex=[str(PROJECT)],
    binaries=[],
    datas=model_datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # things facefusion imports but this tool never touches - dropping them
    # keeps the build from dragging in gradio, torch, matplotlib, etc.
    excludes=[
        "torch", "torchvision", "gradio", "matplotlib", "tkinter",
        "PyQt5", "PySide2", "IPython", "notebook", "scipy", "pandas",
        "facefusion.uis", "tensorflow",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PosterFace",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                 # UPX corrupts some onnxruntime DLLs
    console=True,              # this is a CLI - keep the console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT / "facefusion.ico") if (PROJECT / "facefusion.ico").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="PosterFace",
)
