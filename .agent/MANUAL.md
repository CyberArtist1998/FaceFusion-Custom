

## STEPS:
1. Read AGENTS.md.
2. Read src/services/panel-gating.ts.
3. Above the line `export function hasPremiumAccess`, insert exactly this
   comment line, keeping the existing comment block intact:
   // Verified: single entry point for premium checks.
4. Run this exact command and paste its full output:
   npx tsc --noEmit -p tsconfig.json && npx tsc --noEmit -p tsconfig.api.json
5. If it exits 0, run:
   git add src/services/panel-gating.ts && git commit -m "docs: note on hasPremiumAccess"
   If it exits non-zero, run: git checkout -- src/services/panel-gating.ts
   and report the error. Do not attempt a fix.
6. Stop.


# How to Put a Martyr's Face on a Poster — Step by Step

A plain-language guide. Follow it in order. You do not need to understand the
technical parts to get the same results.

---

## What this does

You have two pictures:

- **The source** — a real photo of the martyr (often already inside a memorial poster).
- **The target** — an AI-generated poster with a *stranger's* face on it.

This process replaces the stranger's face with the martyr's face, and gives you a
**number** telling you how well it worked, so you are not just guessing by eye.

---

## Before you start (one time only)

You need these, and they are already installed on this machine:

| Thing | Where it is |
|---|---|
| FaceFusion | `D:\MyWorld-Sync\011-AI\FaceFusion` |
| The scripts | `D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\scripts` |
| ComfyUI (only for the optional style pass) | `D:\MyWorld-Sync\011-AI\ComfyUIDirectory\Main\ComfyUI` |

**One shortcut to remember.** Every command below starts with this long path. It is
just "the Python that belongs to FaceFusion":

```
D:\MyWorld-Sync\011-AI\FaceFusion\venv_311\Scripts\python.exe
```

---

# THE RECOMMENDED WAY — one command, scored and chosen for you

**Use this. The step-by-step further down is only for one-off jobs.**

Steps 1–5 below run *one* fixed setting and hand you a single picture with no evidence
behind it. That is guessing. This command instead makes several versions of every
poster, measures each one against the real face, writes the numbers to disk, and picks
the winner from the measurements.

**This is not a small difference.** Tested across 20 posters, the best setting was
different for almost every one:

```
 7 of 20 posters   won by weight 0.50, blur 0.15
 5 of 20 posters   won by weight 0.65, blur 0.00
 5 of 20 posters   won by weight 0.65, blur 0.15
 3 of 20 posters   won by a version using the gpen enhancer
```

No single recipe was right more than about a third of the time. That is why the
machine should choose, per poster, from real measurements.

### How to run it

```bash
cd "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\scripts"
"D:\MyWorld-Sync\011-AI\FaceFusion\venv_311\Scripts\python.exe" ff_batch.py --list-sources
```

That shows every martyr folder. `OK` means it is ready; `--` means it still needs
Step 2 (cut out the face) first.

Then run one martyr against every poster:

```bash
"D:\MyWorld-Sync\011-AI\FaceFusion\venv_311\Scripts\python.exe" ff_batch.py --source "پهپاد - امیردریادار - حسین دانا"
```

Useful extras:

- `--limit 3` — only the first 3 posters of each kind, for a quick trial
- `--kinds Real` — only the realistic posters
- `--include-risky` — also try the ghost models (read the warning below first)

### What you get

Everything is written to `Finial\<martyr name>\`:

| File | What it is |
|---|---|
| `SCORES_MASTER.txt` | every poster, its winner and score — read this first |
| `SCORES_MASTER.csv` | the same numbers for Excel |
| `<poster>\scores.txt` | all versions of that poster, ranked, with the settings used |
| `<poster>\scores.json` | the same, for other programs |
| `<poster>\_sheet.png` | all versions side by side, score printed on each |
| `<poster>\FINAL_<poster>.png` | **the winner, chosen by score** |

`SCORES_MASTER.txt` also lists any poster whose best score came out **below 0.60**
under a "NEEDS ATTENTION" heading, so bad results announce themselves instead of
hiding in a folder.

### One thing the machine cannot judge

The score is measured against a **front-facing** photo of the martyr. On posters that
show the head **from the side**, some models score well by quietly turning the face
toward the camera — which looks completely wrong on the finished poster.

The ghost models do this, so they are **switched off by default**. If you turn them on
with `--include-risky` and one of them wins, `scores.txt` prints a `REVIEW` warning.

**Always open `_sheet.png` and look. If the number is high but the picture looks wrong,
trust your eyes.**

---

# The manual way (single poster, no scoring)

---

## Step 1 — Make a folder for the new poster

Create a folder like `sweep-05` inside `D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\`.

Put two files in it:

- The martyr's photo (any name, e.g. `photo.jpg`)
- The AI poster, named exactly **`Target.png`**

---

## Step 2 — Cut out the face

**Why:** FaceFusion looks at your source picture and averages together *every* face it
finds. If the memorial poster has a second small photo in the corner, it will blend two
different people into one face and the result will look like neither of them. So we cut
out one clean face first.

```bash
cd "D:\MyWorld-Sync\011-AI\FaceFusion"
venv_311\Scripts\python.exe "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\scripts\ff_prep_source.py" --in "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\sweep-05\photo.jpg" --out "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\sweep-05\Source_face.jpg"
```

**Now open `Source_face.jpg` and look at it.** It must contain **exactly one face**,
showing the whole head.

If the crop is wrong, get a coordinate grid and pick your own box:

```bash
venv_311\Scripts\python.exe "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\scripts\ff_prep_source.py" --in "...\photo.jpg" --grid
```

Open the `_grid.png` file it makes, read the numbers off the edges, then re-run with
`--box left,top,right,bottom` (for example `--box 600,150,1060,800`).

---

## Step 3 — Decide which kind of poster you have

Look at your `Target.png` and answer one question:

- **Does it look like a photograph?** → **PHOTOREAL**. Go to Step 4A.
- **Does it look like a painting, drawing, or illustration?** → **STYLIZED**. Go to Step 4B.

This matters. The two need different treatment, and doing the wrong one makes the
result worse.

---

## Step 4A — PHOTOREAL posters (the simple case)

Run one command. Replace `sweep-05` with your folder name:

```bash
cd "D:\MyWorld-Sync\011-AI\FaceFusion"
venv_311\Scripts\python.exe facefusion.py headless-run -s "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\sweep-05\Source_face.jpg" -t "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\sweep-05\Target.png" -o "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\sweep-05\final.png" --processors face_swapper --face-swapper-model inswapper_128 --face-swapper-pixel-boost 512x512 --face-swapper-weight 0.65 --face-mask-types box --face-mask-blur 0.15 --face-selector-mode one --output-image-quality 100 --execution-providers cpu
```

That takes about 8 seconds. **You are done.** Skip to Step 5.

---

## Step 4B — STYLIZED posters (two passes)

**Pass 1 — swap the face** (same as above, but blur `0.0`):

```bash
cd "D:\MyWorld-Sync\011-AI\FaceFusion"
venv_311\Scripts\python.exe facefusion.py headless-run -s "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\sweep-05\Source_face.jpg" -t "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\sweep-05\Target.png" -o "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\sweep-05\swap.png" --processors face_swapper --face-swapper-model inswapper_128 --face-swapper-pixel-boost 512x512 --face-swapper-weight 0.65 --face-mask-types box --face-mask-blur 0.0 --face-selector-mode one --output-image-quality 100 --execution-providers cpu
```

**Why a second pass:** the swapped face is a *photograph* sitting on a *painting*. The
skin looks too real and it does not match the artwork. The second pass repaints the face
in the poster's own style.

**Start ComfyUI** (leave this window open):

```bash
cd "D:\MyWorld-Sync\011-AI\ComfyUIDirectory\Main\ComfyUI"
.venv_311\Scripts\python.exe main.py --port 8199
```

Wait until it prints `To see the GUI go to: http://127.0.0.1:8199`.

**Pass 2 — repaint the face.** In a *new* window:

```bash
cd "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\scripts"
"D:\MyWorld-Sync\011-AI\FaceFusion\venv_311\Scripts\python.exe" cf_detail.py --sweep-dir sweep-05 --image "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\sweep-05\swap.png" --denoise 0.15 0.20 0.25 --positive "stylized painterly illustration portrait of a naval officer, white peaked cap, gouache watercolor painting, soft brush strokes, flat shading, pastel palette, poster art" --negative "photograph, photorealistic, 3d render, realistic skin pores, blurry, deformed, extra faces, watermark"
```

Describe *your* poster's art style in the `--positive` text. Always keep
`photograph, photorealistic` in the `--negative` text.

You get three versions in `sweep-05\out\detail\`. **Pick with your eyes**:

- `0.15` — safest. Keeps the most likeness.
- `0.20` — usually the sweet spot.
- `0.25` — best art match, noticeably less like him.

---

## Step 5 — Check the result

```bash
cd "D:\MyWorld-Sync\011-AI\FaceFusion"
venv_311\Scripts\python.exe "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\scripts\ff_identity.py" --ref "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\sweep-05\Source_face.jpg" --dir "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\sweep-05"
```

You get a number between 0 and 1 for each picture. **Higher = more like the real person.**

| Number | Meaning |
|---|---|
| under 0.30 | Failed. The face did not transfer. Something is wrong |
| 0.60 – 0.75 | Weak. Usable only if it looks right to you |
| 0.80 – 0.90 | Good. This is the normal range for a successful swap |
| above 0.90 | Excellent |

For comparison: an untouched AI poster scores about **0.05 – 0.20**. That is your
starting point, so 0.88 is a very large improvement.

### Important warning about the number

**The number can lie when the poster shows the face from the side.**

Some models cheat by *turning the face toward the camera*. That scores high, because the
martyr's photo is also front-facing — but on a side-view poster it looks completely wrong,
with eyes staring forward on a head that is turned away.

**Rule: always look at the picture. If the number is high but it looks wrong, trust
your eyes.** The number is there to catch total failures, not to choose the winner.

---

## The settings, and why they are these

You do not need to change these. They were found by testing every option on four
different posters.

| Setting | Use | Why |
|---|---|---|
| `--face-swapper-model inswapper_128` | always | Won all four tests. The default, `hyperswap_1a_256`, barely transfers any face at all |
| `--face-swapper-weight 0.65` | always | Best in every test. Higher makes it worse, not better |
| `--face-mask-blur 0.15` (photoreal) / `0.0` (stylized) | | The program's default of `0.3` is too soft and loses likeness |
| `--face-swapper-pixel-boost 512x512` | always | Bigger values make no difference. `1024` was sometimes worse |
| `--face-selector-mode one` | always | Tells it to use the single face in the picture |
| **face enhancer** | **OFF** | This is the big one — see below |

### Do not use the face enhancer

FaceFusion turns on a "face enhancer" at strength 80 by default. **It makes the result
look less like the person.** Tested on every poster, the damage rises steadily:

```
enhancer off      0.895
strength 25       0.882
strength 60       0.840
strength 80       0.798   ← the default
strength 100      0.751
```

If a picture genuinely looks too soft, the *only* safe one is `gpen_bfr_1024` at
strength 60 or less. It costs almost nothing. Never use `codeformer` or `gfpgan`
at the default strength.

---

## Getting better results

The biggest improvement is not a setting — it is **how you generate the poster**.

The martyr's photo is almost always taken **facing forward**. If your AI poster shows the
head turned to the side, the computer has to invent everything it cannot see, and the
likeness suffers.

**So: when you create the poster, ask for a front-facing or slightly turned head.** This
costs nothing and helps more than any setting in this guide. Side-view and profile
posters are the hardest cases and give the weakest results.

---

## If something goes wrong

| Problem | Cause | Fix |
|---|---|---|
| `no face detected` | The crop is wrong, or the face is too small | Redo Step 2 with `--grid` and pick a better box |
| Face looks like a different person | Two faces in your source | Redo Step 2. The crop must show only ONE face |
| Score under 0.30 | Wrong model, or face not found | Check you typed `inswapper_128` |
| Eyes look forward on a side view | The model rotated the face | Use `inswapper_128`. Do not use `ghost_1_256` or `ghost_2_256` on side views |
| Face looks like a photo pasted on a painting | Stylized poster, no second pass | Do Step 4B |
| `invalid choice: 'cuda'` | This machine runs on CPU | Use `--execution-providers cpu`. It is fast enough — about 8 seconds |
| ComfyUI command fails | ComfyUI is not running | Start it (Step 4B) and wait for the `http://127.0.0.1:8199` message |

---

## Testing many options at once (optional)

If you want to compare settings instead of trusting this guide, there is a sweep tool.
It produces one big sheet of every version, with the settings and score printed on each.

```bash
cd "D:\MyWorld-Sync\011-AI\FaceFusion"
venv_311\Scripts\python.exe "D:\MyWorld-Sync\051-GraphicDesign\002-MertydomPosters\scripts\ff_sweep.py" --sweep-dir sweep-05 --stage models --execute
```

Replace `models` with `weight`, `boost`, `mask`, `enhancer`, or `detector` to test that
one thing. The sheet appears in `sweep-05\out\<stage>\_sheet_<stage>.png`.

Add `--sheet-crop x,y,w,h` to zoom the sheet onto the face — otherwise the pictures are
too small to judge.
