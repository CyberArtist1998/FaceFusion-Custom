# REPO-MAP

_Generated 2026-08-15 15:02 UTC by repo-orient.sh. Sections marked JUDGEMENT need a human._

## JUDGEMENT: what this project is

<one paragraph — what it does, who uses it, what the main flow is>

## Manifests
```
./package.json
./requirements.txt
```

### package.json scripts
```
lint              eslint .
fix               npm run lint -- --fix
```

### workspaces / monorepo
```
(no workspaces field)
```

## Source roots by size

| Directory | Files | Lines |
|---|---:|---:|
| `./facefusion` | 177 | 17611 |
| `./facefusion/jobs` | 6 | 458 |
| `./facefusion/processors` | 61 | 5708 |
| `./facefusion/uis` | 53 | 4388 |
| `./facefusion/workflows` | 4 | 318 |
| `./tests` | 42 | 2794 |

## JUDGEMENT: directory responsibilities

| Path | Responsibility |
|---|---|
| `<path>` | `<what lives here>` |

## Entry point candidates
```
-- root-level scripts --
./FF.py
./facefusion.py
./install.js
./install.py
./menu.js
./reset.js
./run.js
./run_identity.bat
./run_prep_source.bat
./run_swap.bat
./update.js
-- package.json main/bin --
```

## Config, env, and flags
```
./.github/FUNDING.yml
./.github/workflows/ci.yml
./eslint.config.cjs
./facefusion.ini
./mypy.ini
```

## Largest source files — read these with line ranges, never whole
```
   774 ./facefusion/processors/modules/face_swapper/core.py
   669 ./facefusion/processors/modules/frame_enhancer/core.py
   647 ./facefusion/processors/modules/background_remover/core.py
   639 ./FF.py
   499 ./facefusion/processors/modules/face_editor/core.py
   458 ./facefusion/face_detector.py
   426 ./facefusion/processors/modules/face_enhancer/core.py
   424 ./facefusion/processors/modules/deep_swapper/core.py
   402 ./facefusion/types.py
   386 ./tests/test_job_manager.py
   365 ./facefusion/vision.py
   350 ./facefusion/core.py
   324 ./facefusion/program.py
   306 ./facefusion/uis/components/preview.py
   299 ./facefusion/processors/modules/frame_colorizer/core.py
```

## License
```
(no LICENSE file — resolve before distributing changes)
```

## Repo history
```
commits:      145
first commit: 2023-11-27
last commit:  2026-07-11
branch:       master
```

## JUDGEMENT: landmines

- <files never to read whole>
- <generated directories never to edit>
- <behaviour enforced server-side that client changes cannot affect>
