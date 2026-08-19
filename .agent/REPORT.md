# Martyr Memorial Posters — FaceFusion Parameter Sweep

**Subject:** شهید محمد درویشی — Source.jpg / Target.png
**Environment:** FaceFusion 3.6.1 (`D:\Softwares\FaceFusion - Copy`), CPU onnxruntime 1.28.0, RTX 4060 Ti 8GB (unused), 64GB RAM
**Date:** 2026-07-28

---

## 1. Objective

Put the real face of the martyr onto an AI-generated poster body, as close to his actual likeness as possible, with a repeatable process that works for the next person.

## 2. Headline result

| | ArcFace similarity to real source |
|---|---|
| AI template before any swap | **0.2005** |
| FaceFusion defaults (`hyperswap_1a_256`, enhancer blend 80) | ~0.42 or lower |
| Tuned configuration | **0.904** |

The swap moves identity from essentially *a different person* to a strong likeness. The single largest contributor is **model choice**, not any tuning parameter.

## 3. What was built

Three scripts in `D:\01-AI\002-MertydomPosters\scripts\`.

### `ff_prep_source.py` — source face extraction
FaceFusion builds its source identity with `get_average_face()` (`face_swapper/core.py:757`), which averages **every** face it detects across the source images. A finished poster containing a second photo therefore blends two people into one identity before the swapper runs at all. This script crops to exactly one face. `--grid` overlays coordinates so the crop box can be read off any new poster.

### `ff_identity.py` — objective identity scoring
Imports FaceFusion in-process and drives its own `face_analyser`, so detection, 5-point alignment and the ArcFace pass are identical to what the swapper uses. `Face.embedding_norm` (`types.py:35-46`) is the L2-normalised 512-d vector; similarity is a dot product. Reusing FaceFusion's alignment matters — hand-rolled ArcFace scripts typically go wrong exactly there.

### `ff_sweep.py` — staged sweep engine
Six stages: `models`, `boost`, `weight`, `enhancer`, `mask`, `detector`.

Key design point: every swept axis is a **step key** (`program.py:107-192`, `face_swapper/core.py:521`, `face_enhancer/core.py:298`), so a single job holds all variants and each model loads once. Only execution and memory settings are job keys, which is why they sit on `job-run`. Each stage varies one axis against a fixed baseline, writes `_manifest.json` for provenance, and produces a contact sheet with every parameter and the identity score burned into each tile.

## 4. Results by axis

### Model (decisive)
| Model | Score |
|---|---|
| inswapper_128 | **0.8951** |
| ghost_1_256 | 0.7992 |
| ghost_2_256 | 0.7671 |
| blendswap_256 | 0.6855 |
| hyperswap_1a_256 | 0.4198 |

*Tested at 512px boost, weight 0.5, no enhancer, box mask. 5 of 13 models — the other 8 were not on disk.*

### Mask blur (second largest)
`0.15` → **0.9082** · `0.0` → 0.9051 · `0.3` (default) → 0.8951 · `0.5` → 0.8661 · `0.7` → 0.8438

Adding `occlusion` or `region` mask types costs 0.01–0.02. Asymmetric padding (`0,16,16,16`) costs 0.06.

### Enhancer (purely destructive, monotonic)
| Blend | gfpgan_1.4 | codeformer |
|---|---|---|
| 0 | 0.8951 | 0.8951 |
| 25 | 0.8893 | 0.8824 |
| 40 | 0.8818 | 0.8679 |
| 60 | 0.8667 | 0.8395 |
| **80 (default)** | 0.8457 | 0.7984 |
| 100 | 0.8153 | 0.7514 |

Every increment loses identity. FaceFusion's default blend is 80. **Exception:** `gpen_bfr_1024` at blend 80 scores 0.8932 and at blend 60 costs 0.0004 — the only enhancer that is effectively free.

### Weight (minor)
Peaks at 0.5–0.65, degrades above. `inswapper_128`: w0.0 0.825 · w0.5 0.895 · w0.65 0.895 · w0.8 0.889 · w1.0 0.874. Total range ~0.02.

### Pixel boost (negligible)
`inswapper_128`: 256 → 0.8959 · 512 → 0.8951 · 768 → 0.8985 · 1024 → 0.8808. Within noise; 1024 is worse.

## 5. Findings that contradicted prior assumptions

1. **`hyperswap_1a_256` is the worst of the five tested.** It is FaceFusion's default and the model both prior research documents recommended switching *to*. It moves identity only 0.20 → 0.42. It appears cleanest visually precisely because it changes the target's face least.

2. **`--face-swapper-weight` above 0.5 does not increase identity.** The code (`face_swapper/core.py:701-709`) does interpolate the blend coefficient to negative values above 0.5, extrapolating away from the target embedding — but measured similarity peaks at 0.65 and declines after. Extrapolation overshoots into a less valid region rather than strengthening identity.

3. **Pixel boost is not a quality dial for identity.** Higher is not better; 1024 measured worse than 256.

4. **The enhancer is the most costly default in the tool.** At the stock blend of 80, `codeformer` costs 0.097 — more than the entire weight and boost axes could return.

5. **Photoreal checkpoints are correct for this project.** Prior research advised against Juggernaut XL as "wrong family," but that assumed stylized posters. This target is photoreal, so `juggernautXL_ragnarok.safetensors` is an appropriate FaceDetailer checkpoint here.

## 6. Recommended production configuration

```
--face-swapper-model inswapper_128
--face-swapper-pixel-boost 512x512
--face-swapper-weight 0.5
--face-mask-types box
--face-mask-blur 0.15
--face-selector-mode one
--output-image-quality 100
```

Enhancer **off**. If sharpening is needed, `gpen_bfr_1024` at blend ≤60 only. Never `codeformer` or `gfpgan` at the default 80.

## 7. Method caveats

- **The metric is partly circular.** `inswapper_128` is conditioned on ArcFace embeddings — the same signal being scored — and the Ghost family shares that lineage. ArcFace scoring structurally flatters them. The ranking is reliable for detecting failures (`hyperswap_1a` at 0.42) and for within-model comparisons, but should not be read as proof that `inswapper` beats `ghost` in perceived likeness. Judge the contact sheets.
- **0.904 is not "90% him."** ArcFace verification thresholds sit near 0.35–0.40 for same-person. These are ranking numbers.
- **5 of 13 swappers tested.** `ghost_3`, `hififace_unofficial`, `hyperswap_1b/1c`, `inswapper_128_fp16`, `simswap_unofficial_512`, `uniface_256` were not on disk; `simswap_256` is corrupt (`.hash` present, `.onnx` missing).
- **Single subject, single template.** All conclusions are from one source/target pair.
- **CPU only.** ~6–10s per render at 1856×2304. Both venvs have CPU-only onnxruntime; the 4060 Ti is unused. Not a bottleneck for stills.

## 8. Remaining ceiling

The FaceFusion axes are exhausted; remaining headroom is noise. The residual gap is structural, not a settings problem: the brow and beard now read as his, but the skull geometry, the ~30–40° head yaw and the rim-lighting are still the template's, and no swapper parameter reaches those.

Two moves address it, in order of payoff:

1. **Generate the next template at the source's head angle.** The template is AI-generated, so the pose is a free variable. The source portrait is frontal; the target is turned 30–40°. Removing that mismatch costs nothing but prompt discipline and eliminates the largest single error source.
2. **FaceDetailer redraw pass in ComfyUI** — re-render the swapped face in the poster's own lighting and grain at low denoise, using `juggernautXL_ragnarok`.

## 9. ComfyUI audit (2026-07-28)

Four ComfyUI-related trees exist on D:. Only one is functional.

| Path | What it is | Status |
|---|---|---|
| `D:\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI` | Desktop app's install, `.venv` = Python 3.13.12, torch 2.10.0+cu130 | **HEALTHY — use this.** CUDA True, RTX 4060 Ti detected |
| `D:\Comfy-Desktop\ComfyUI-Shared\models` | Shared model store the above resolves from | **Useful** — put all models here |
| `D:\Softwares\ComfyUI` | Standalone git clone, venv was Python 3.14 + numpy 1.26.4 | **BROKEN** — numpy 1.26 has no 3.14 support, torch can't import. Renamed to `Old_venv`. Nothing here is needed |
| `D:\Softwares\Comfy Desktop` | The Desktop application binaries | Keep — this is the launcher |

Also note: `standalone-env` inside the Desktop install is a bare Python with **no torch** — the real runtime is `ComfyUI/.venv`. Two shared models are truncated downloads: `z_image_turbo_bf16.safetensors` and `qwen_3_4b.safetensors` are both ~103MB when they should be multi-GB.

**Changes made to the healthy install:**
- Installed `ComfyUI-Impact-Subpack` v1.3.5 + `ultralytics` 8.4.108. Impact-Pack alone does **not** provide `UltralyticsDetectorProvider`, so FaceDetailer had no detector — the classic trip-up.
- Downloaded `face_yolov8m.pt` (52MB) to `ComfyUI/models/ultralytics/bbox/`.
- Hardlinked `juggernautXL_ragnarok.safetensors` into the shared checkpoints folder (no 7GB copy).
- Added `extra_model_paths.yaml` so headless launches resolve models like the Desktop app does.

## 10. FaceDetailer result — the pass was rejected

Ran a denoise sweep with `juggernautXL_ragnarok` over the best swap output (`cf_detail.py`).

| Denoise | Identity | Δ |
|---|---|---|
| input (swap only) | 0.9038 | — |
| 0.05 | 0.8823 | −0.02 |
| 0.10 | 0.8690 | −0.03 |
| 0.15 | 0.8429 | −0.06 |
| 0.25 | 0.7052 | −0.20 |
| 0.35 | 0.4387 | **−0.47** |

**Verdict: do not run FaceDetailer in this pipeline.** Prior research recommended denoise 0.25–0.35; at 0.35 the pass discards more identity than the entire FaceFusion tuning effort gained, and the output is visibly a different person. Juggernaut XL's photoreal face prior redraws toward its own generic face rather than restyling.

The pass was meant to fix a "pasted-on" look — but `inswapper_128` at mask blur 0.15 already blends with no visible seam, so there was nothing to repair. It is pure loss here. Cap at 0.05 if ever needed for grain matching; otherwise skip the stage entirely.

## 11. Assets

```
D:\01-AI\002-MertydomPosters\
  scripts\  ff_prep_source.py  ff_identity.py  ff_sweep.py
  sweep\    Source.jpg  Source_face.jpg  Target.png
    out\    models\  weight\  boost\  mask\  enhancer\  best\
            (each with _sheet_*.png and _manifest.json)
```
